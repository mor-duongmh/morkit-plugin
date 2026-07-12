"""Phase 3 — the network layer and the push.

No test here reaches the network: `jira_client._request` is the single call site, so
replacing it gives a complete, honest fake — and `Config.calls` lets us assert the
thing that matters most, which is that a refused approval sends *nothing at all*.
"""

from __future__ import annotations

import hashlib
import json
import types
import urllib.error
import urllib.request

import pytest

import breakdown_file as bf
import diff_tasks as dt
import jira_client as jc
import jira_map as jm
import push_jira as pj
import task_mapper as tm
from test_diff_tasks import BASE_URL, MODEL_SHA, PROJECT, payload, task

ENV = {
    "JIRA_BASE_URL": BASE_URL,
    "JIRA_PROJECT_KEY": PROJECT,
    "JIRA_PAT": "s3cret-token",
}


class FakeJira:
    """Stands in for the instance. Records every call so tests can count them."""

    def __init__(self, issue_types=("Story", "Task"), priorities=("High", "Medium", "Low")):
        self.issue_types = list(issue_types)
        self.priorities = list(priorities)
        self.issues = {}
        self.calls = []
        self.next_id = 100
        self.die_on_create = False

    def __call__(self, cfg, method, path, body=None):
        cfg.calls += 1
        self.calls.append((method, path.split("?")[0]))

        if path.startswith("/rest/api/2/myself"):
            return {"name": "brse"}
        if path.startswith("/rest/api/2/issue/createmeta"):
            return {"projects": [{"issuetypes": [{"name": n} for n in self.issue_types]}]}
        if path.startswith("/rest/api/2/priority"):
            return [{"name": n} for n in self.priorities]
        if path.startswith("/rest/api/2/search"):
            return {"issues": list(self.issues.values()), "total": len(self.issues)}
        if method == "POST" and path == "/rest/api/2/issue":
            if self.die_on_create:
                raise ConnectionResetError("the reply never came back")
            self.next_id += 1
            key = f"{PROJECT}-{self.next_id}"
            self.issues[key] = {"key": key, "fields": dict(body["fields"])}
            return {"key": key}
        if method == "PUT":
            key = path.rsplit("/", 1)[-1]
            self.issues[key]["fields"].update(body["fields"])
            return {}
        if method == "GET" and "/rest/api/2/issue/" in path:
            key = path.rsplit("/", 1)[-1].split("?")[0]
            return {"fields": self.issues[key]["fields"]}
        raise AssertionError(f"unexpected call: {method} {path}")

    def count(self, method) -> int:
        return sum(1 for m, _ in self.calls if m == method)


@pytest.fixture
def jira(monkeypatch):
    fake = FakeJira()
    monkeypatch.setattr(jc, "_request", fake)
    return fake


def make_args(tmp_path, **overrides):
    args = types.SimpleNamespace(
        breakdown=str(tmp_path / "task-breakdown.md"),
        tasks=str(tmp_path / "tasks.json"),
        map=str(tmp_path / "jira-map.json"),
        workspace=None, dry_run=False, offline=False, recover=False, force=False,
    )
    for key, value in overrides.items():
        setattr(args, key, value)
    return args


def setup_workspace(tmp_path, tasks_payload, book=None, approve=True):
    """Write the three files a push reads: tasks.json, the breakdown, the ledger."""
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps(tasks_payload), encoding="utf-8")
    sha = hashlib.sha256(tasks_path.read_bytes()).hexdigest()

    actions = dt.diff(tasks_payload, book)
    text = bf.render(actions, tasks_payload, book, PROJECT, BASE_URL, sha,
                     generated="2026-07-12T00:00:00+00:00")
    if approve:
        text = text.replace("status: draft", "status: approved", 1)
    (tmp_path / "task-breakdown.md").write_text(text, encoding="utf-8")

    if book is not None:
        jm.save_map_atomic(tmp_path / "jira-map.json", book)
    return sha


# --- config refuses an unsafe environment --------------------------------


def test_plaintext_base_url_is_refused():
    with pytest.raises(jc.ConfigError, match="https"):
        jc.config_from_env({**ENV, "JIRA_BASE_URL": "http://jira.example.com"})


def test_credentials_in_the_url_are_refused():
    with pytest.raises(jc.ConfigError, match="credentials"):
        jc.config_from_env({**ENV, "JIRA_BASE_URL": "https://u:p@jira.example.com"})


def test_a_project_key_cannot_smuggle_jql():
    """Unvalidated, `X" OR project = OPS` retargets the recovery query at another
    team's project — whose issues the next run would then overwrite."""
    with pytest.raises(jc.ConfigError, match="not a Jira project key"):
        jc.config_from_env({**ENV, "JIRA_PROJECT_KEY": 'X" OR project = OPS'})


def test_a_missing_credential_is_refused_not_prompted():
    with pytest.raises(jc.ConfigError, match="No Jira credential"):
        jc.config_from_env({"JIRA_BASE_URL": BASE_URL, "JIRA_PROJECT_KEY": PROJECT})


# --- the transport does not leak the credential --------------------------


def test_the_opener_speaks_only_https():
    """urlopen()'s default opener also registers File, FTP and Data handlers, and
    JIRA_BASE_URL comes from the environment. file:/// is not a code path we want."""
    handlers = {h.__class__.__name__ for h in jc._opener().handlers}
    assert "HTTPSHandler" in handlers
    assert not handlers & {"HTTPHandler", "FTPHandler", "FileHandler", "DataHandler"}


def test_the_redirect_guard_is_actually_wired_into_the_opener():
    """Testing _RefuseRedirect in isolation proves nothing if the opener never installs
    it — the test would keep passing with the handler removed."""
    assert any(isinstance(h, jc._RefuseRedirect) for h in jc._opener().handlers)


def test_a_redirect_is_refused_rather_than_followed():
    """CPython copies Authorization onto the redirect target, any host. One stale
    JIRA_BASE_URL and the PAT is posted to somebody else's server."""
    handler = jc._RefuseRedirect()
    with pytest.raises(jc.JiraError, match="Refusing"):
        handler.redirect_request(
            urllib.request.Request(BASE_URL), None, 302, "Found", {}, "https://evil.example/x"
        )


def test_tls_verification_is_on():
    context = jc._tls_context()
    assert context.verify_mode == jc.ssl.CERT_REQUIRED
    assert context.check_hostname is True


def test_the_config_repr_does_not_print_the_token():
    """One stray log.debug("%r", cfg) is all it would take."""
    cfg = jc.config_from_env(ENV)
    assert cfg.pat not in repr(cfg)


def test_a_non_json_body_becomes_a_jira_error(monkeypatch):
    """An SSO or proxy interstitial answers 200 with HTML. Unwrapped, the JSONDecodeError
    escapes the caller's `except JiraError` and aborts the push mid-backlog."""
    cfg = jc.config_from_env(ENV)

    class FakeResponse:
        def read(self):
            return b"<html>please log in</html>"

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(jc.urllib.request.OpenerDirector, "open", lambda *a, **k: FakeResponse())
    with pytest.raises(jc.JiraError, match="non-JSON"):
        jc._request(cfg, "GET", "/rest/api/2/myself")


def test_a_read_timeout_becomes_a_jira_error(monkeypatch):
    """socket.timeout is an OSError and fires while reading the body — urllib does not
    wrap it. Thirty seconds into sixty sequential posts, this is routine."""
    cfg = jc.config_from_env(ENV)

    def timeout(*_a, **_kw):
        raise TimeoutError("timed out")

    monkeypatch.setattr(jc.urllib.request.OpenerDirector, "open", timeout)
    with pytest.raises(jc.JiraError):
        jc._request(cfg, "GET", "/rest/api/2/myself")


def test_one_label_constant_serves_both_the_search_and_the_strip():
    """Recovery searches by `morkit-srs` and recovers the id by stripping
    `morkit-id-`. Two copies of these constants drifting apart means recovery finds
    nothing and re-creates the whole backlog."""
    assert jc.LABEL_ALL is tm.LABEL_ALL


def test_an_error_message_never_carries_the_token(monkeypatch):
    cfg = jc.config_from_env(ENV)

    def explode(*_a, **_kw):
        raise urllib.error.URLError(f"failed talking to {cfg.pat}")

    monkeypatch.setattr(jc.urllib.request.OpenerDirector, "open", explode)
    with pytest.raises(jc.JiraError) as caught:
        jc._request(cfg, "GET", "/rest/api/2/myself")
    assert cfg.pat not in str(caught.value)
    assert "***" in str(caught.value)


# --- the gate stops the push before any request --------------------------


def test_an_unapproved_breakdown_sends_nothing(tmp_path, jira):
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks, approve=False)
    with pytest.raises(SystemExit, match="Not approved"):
        pj.run(make_args(tmp_path), env=ENV)
    assert jira.calls == []  # not one request, not even preflight


def test_a_stale_approval_sends_nothing(tmp_path, jira):
    """tasks.json regenerated after signing: the ticket bodies come from there, so
    pushing now would send text the reviewer never read."""
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)
    (tmp_path / "tasks.json").write_text(json.dumps(payload(task("FR-001", "h2"))), encoding="utf-8")

    with pytest.raises(bf.StaleBreakdownError):
        pj.run(make_args(tmp_path), env=ENV)
    assert jira.calls == []


def test_pushing_to_a_project_the_reviewer_did_not_approve_is_refused(tmp_path, jira):
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)
    with pytest.raises(jm.BindingError, match="did not approve"):
        pj.run(make_args(tmp_path), env={**ENV, "JIRA_PROJECT_KEY": "PROD"})
    assert jira.calls == []


def test_a_breakdown_with_no_project_line_is_refused(tmp_path, jira):
    """Deleting the `project:` line does not disturb `rows_for` or `tasks_sha256`, so
    the file still reads as approved. An absent binding is not a pass — otherwise a
    reviewer tidying up frontmatter they did not understand hands the target over to
    whatever the shell happens to export."""
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)
    path = tmp_path / "task-breakdown.md"
    path.write_text(
        "\n".join(l for l in path.read_text().splitlines() if not l.startswith("project:")) + "\n",
        encoding="utf-8",
    )
    assert bf.is_approved(path.read_text()) is True  # the signature still looks valid

    with pytest.raises(jm.BindingError, match="nothing proving"):
        pj.run(make_args(tmp_path), env={**ENV, "JIRA_PROJECT_KEY": "PROD"})
    assert jira.calls == []


def test_the_workspace_guard_governs_the_path_actually_written(tmp_path, jira, monkeypatch):
    """resolve_within RETURNS the safe path. Validating one path and then writing to
    the original is not a guard: a relative --map would land in the cwd, the next run
    would not find it, and every requirement would look new — the backlog created
    twice, which is the one failure this whole skill exists to prevent."""
    workspace = tmp_path / "ws"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()

    tasks = payload(task("FR-001", "h1"))
    setup_workspace(workspace, tasks)
    monkeypatch.chdir(outside)  # relative paths would resolve here, not in the workspace

    args = make_args(workspace, map="jira-map.json", workspace=str(workspace))
    pj.run(args, env=ENV)

    assert (workspace / "jira-map.json").exists()
    assert not (outside / "jira-map.json").exists()


def test_a_map_outside_the_workspace_is_refused(tmp_path, jira):
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)
    args = make_args(tmp_path, map="../../escape.json", workspace=str(tmp_path))
    with pytest.raises(jm.UnsafePathError):
        pj.run(args, env=ENV)
    assert jira.calls == []


def test_offline_makes_no_requests_at_all(tmp_path, jira):
    """The rehearsal path — and the reason a developer with no token can still run the
    whole thing end to end."""
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)
    result = pj.run(make_args(tmp_path, offline=True, dry_run=True), env=ENV)
    assert jira.calls == []
    assert [w["source_id"] for w in result["would"]] == ["FR-001"]


def test_dry_run_previews_without_writing(tmp_path, jira):
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)
    pj.run(make_args(tmp_path, dry_run=True), env=ENV)
    assert jira.count("POST") == 0 and jira.count("PUT") == 0
    assert jira.count("GET") > 0  # preflight did run


# --- creating, and not creating twice ------------------------------------


def test_a_first_push_creates_and_records(tmp_path, jira):
    tasks = payload(task("FR-001", "h1"), task("NFR-01", "h9", issue_type="Task"))
    setup_workspace(tmp_path, tasks)
    result = pj.run(make_args(tmp_path), env=ENV)

    assert result["ok"] and len(result["created"]) == 2
    book = jm.load_map(tmp_path / "jira-map.json")
    assert book["issues"]["FR-001"]["state"] == jm.STATE_CREATED
    assert book["issues"]["FR-001"]["source_hash"] == "h1"


def test_running_the_push_twice_does_not_duplicate_the_backlog(tmp_path, jira):
    """The failure the whole ledger exists to prevent. Shell history, a CI retry, or
    simply not being sure it went through the first time."""
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)
    pj.run(make_args(tmp_path), env=ENV)
    created_first = jira.count("POST")

    with pytest.raises(SystemExit, match="Not approved"):
        pj.run(make_args(tmp_path), env=ENV)  # the signature was retired on success
    assert jira.count("POST") == created_first == 1


def test_a_stale_create_in_the_file_does_not_recreate_a_live_issue(tmp_path, jira):
    """The breakdown's Action column says CREATE. The ledger says it already exists.
    The ledger wins — which is exactly why the push re-diffs instead of obeying the
    file."""
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)  # rendered with no ledger -> the row says CREATE

    book = jm.new_map(PROJECT, BASE_URL, "m.json", MODEL_SHA)
    book["issues"]["FR-001"] = {"key": "PROJ-1", "state": jm.STATE_CREATED, "source_hash": "h1"}
    jm.save_map_atomic(tmp_path / "jira-map.json", book)

    assert "| CREATE |" in (tmp_path / "task-breakdown.md").read_text()
    result = pj.run(make_args(tmp_path), env=ENV)
    assert jira.count("POST") == 0
    assert result["skipped"] == ["FR-001"]


def test_a_create_interrupted_before_the_reply_reconciles(tmp_path, jira):
    """The dangerous window: Jira committed the issue, the process died before the
    response arrived. The ledger holds a `creating` breadcrumb; the next run looks the
    issue up by label instead of making a second one."""
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)
    jira.die_on_create = True
    with pytest.raises(ConnectionResetError):
        pj.run(make_args(tmp_path), env=ENV)

    book = jm.load_map(tmp_path / "jira-map.json")
    assert book["issues"]["FR-001"]["state"] == jm.STATE_CREATING  # written before the POST
    posts_so_far = jira.count("POST")  # Jira did receive it — that is the whole problem

    # The issue did land on Jira, we just never heard about it.
    jira.die_on_create = False
    jira.issues["PROJ-77"] = {
        "key": "PROJ-77", "fields": {"labels": ["morkit-srs", "morkit-id-FR-001"]},
    }
    setup_workspace(tmp_path, tasks, book=jm.load_map(tmp_path / "jira-map.json"))

    result = pj.run(make_args(tmp_path), env=ENV)
    assert jira.count("POST") == posts_so_far, "the second run must not create a second issue"
    assert result["reconciled"] == [{"source_id": "FR-001", "key": "PROJ-77"}]
    assert jm.load_map(tmp_path / "jira-map.json")["issues"]["FR-001"]["key"] == "PROJ-77"


# --- the reviewer's wording, and the revert loop -------------------------


def test_the_edited_summary_is_sent_and_the_machine_hash_is_stored(tmp_path, jira):
    """Two halves of the same guarantee: Jira gets what the human wrote, and the
    ledger records what the SRS generated. Storing the edited text's hash here is what
    makes the next run "helpfully" revert them."""
    tasks = payload(task("FR-001", "h1", summary="[FR-001] machine wording"))
    setup_workspace(tmp_path, tasks)
    path = tmp_path / "task-breakdown.md"
    path.write_text(
        path.read_text().replace("[FR-001] machine wording", "[FR-001] human wording"),
        encoding="utf-8",
    )

    pj.run(make_args(tmp_path), env=ENV)

    sent = next(iter(jira.issues.values()))["fields"]["summary"]
    assert sent == "[FR-001] human wording"

    entry = jm.load_map(tmp_path / "jira-map.json")["issues"]["FR-001"]
    assert entry["source_hash"] == "h1"  # the SRS hash, NOT the edit's
    assert entry["overrides"] == {"summary": "[FR-001] human wording"}


def test_an_unticked_row_is_held_back(tmp_path, jira):
    tasks = payload(task("FR-001", "h1"), task("FR-002", "h2"))
    setup_workspace(tmp_path, tasks)
    path = tmp_path / "task-breakdown.md"
    path.write_text(path.read_text().replace("| [x] | FR-002", "| [ ] | FR-002"), encoding="utf-8")

    result = pj.run(make_args(tmp_path), env=ENV)
    assert result["held_back"] == ["FR-002"]
    assert [c["source_id"] for c in result["created"]] == ["FR-001"]


# --- updating without trampling on the team ------------------------------


def test_an_update_refuses_to_overwrite_work_done_on_the_ticket(tmp_path, jira):
    """By the time anyone re-runs this, a dev may have refined the acceptance criteria
    on the ticket. Blowing that away because a plan file changed is not a trade to
    make silently."""
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)
    pj.run(make_args(tmp_path), env=ENV)

    key = next(iter(jira.issues))
    jira.issues[key]["fields"]["description"] = "QA added repro steps here"

    moved_on = payload(task("FR-001", "h2"))
    setup_workspace(tmp_path, moved_on, book=jm.load_map(tmp_path / "jira-map.json"))
    result = pj.run(make_args(tmp_path), env=ENV)

    assert result["ok"] is False
    assert "edited on Jira" in result["failed"][0]["error"]
    assert jira.issues[key]["fields"]["description"] == "QA added repro steps here"


def test_force_overwrites_when_the_human_means_it(tmp_path, jira):
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)
    pj.run(make_args(tmp_path), env=ENV)
    key = next(iter(jira.issues))
    jira.issues[key]["fields"]["description"] = "edited on the board"

    setup_workspace(tmp_path, payload(task("FR-001", "h2")),
                    book=jm.load_map(tmp_path / "jira-map.json"))
    result = pj.run(make_args(tmp_path, force=True), env=ENV)
    assert result["ok"] and len(result["updated"]) == 1
    assert jira.issues[key]["fields"]["description"] == "body"


# --- recovery -------------------------------------------------------------


def test_recovery_rebuilds_the_ledger_without_duplicating(tmp_path, jira):
    """A lost ledger is not permission to re-create a backlog. Labels carry the id, so
    the issues are found again rather than made again."""
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)
    pj.run(make_args(tmp_path), env=ENV)
    original_key = next(iter(jira.issues))
    (tmp_path / "jira-map.json").unlink()

    setup_workspace(tmp_path, tasks)
    result = pj.run(make_args(tmp_path, recover=True, force=True), env=ENV)

    assert jira.count("POST") == 1, "no second issue: the original was recovered by label"
    assert len(jira.issues) == 1
    assert [u["key"] for u in result["updated"]] == [original_key]


def test_recover_refuses_to_destroy_a_healthy_ledger(tmp_path, jira):
    """A recovery run rewrites every ticket from the SRS with the drift guard blind —
    right when the ledger is genuinely gone, catastrophic when it is not. A mistyped
    flag on a live board must not throw away every hash and every reviewer edit."""
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)
    pj.run(make_args(tmp_path), env=ENV)
    before = (tmp_path / "jira-map.json").read_bytes()

    setup_workspace(tmp_path, tasks, book=jm.load_map(tmp_path / "jira-map.json"))
    with pytest.raises(SystemExit, match="right there"):
        pj.run(make_args(tmp_path, recover=True), env=ENV)

    assert (tmp_path / "jira-map.json").read_bytes() == before


def test_reconcile_records_what_is_on_the_issue_not_what_we_would_have_sent(tmp_path, jira):
    """The interrupted run created the issue; the reviewer may have reworded the row
    since. Recording our guess would make the next UPDATE believe Jira had been edited
    behind our back and refuse a perfectly legitimate change."""
    tasks = payload(task("FR-001", "h1"))
    setup_workspace(tmp_path, tasks)
    jira.die_on_create = True
    with pytest.raises(ConnectionResetError):
        pj.run(make_args(tmp_path), env=ENV)

    jira.die_on_create = False
    jira.issues["PROJ-77"] = {
        "key": "PROJ-77",
        "fields": {
            "labels": ["morkit-srs", "morkit-id-FR-001"],
            "summary": "[FR-001] what actually landed",
            "description": "body",
        },
    }
    setup_workspace(tmp_path, tasks, book=jm.load_map(tmp_path / "jira-map.json"))
    pj.run(make_args(tmp_path), env=ENV)

    entry = jm.load_map(tmp_path / "jira-map.json")["issues"]["FR-001"]
    assert entry["pushed_hash"] == tm.source_hash("[FR-001] what actually landed", "body")

    # ...and because the ledger now describes Jira truthfully, a later update is not
    # blocked by a phantom "someone edited this" error.
    setup_workspace(tmp_path, payload(task("FR-001", "h2")), book=jm.load_map(tmp_path / "jira-map.json"))
    assert pj.run(make_args(tmp_path), env=ENV)["ok"] is True


def test_recovery_cannot_recover_a_hash_so_it_stores_none(tmp_path, jira):
    """No hash can be read back off a Jira issue. `None` is the honest value — and the
    diff reads it as UPDATE. Reading it as "not in the map" would re-create everything."""
    jira.issues["PROJ-5"] = {
        "key": "PROJ-5", "fields": {"labels": ["morkit-srs", "morkit-id-FR-001"]},
    }
    cfg = jc.config_from_env(ENV)
    book = pj._recover(cfg, tmp_path / "jira-map.json", payload()["meta"])

    assert book["issues"]["FR-001"] == {
        "key": "PROJ-5", "state": jm.STATE_CREATED, "source_hash": None,
    }
    action = dt.diff(payload(task("FR-001", "h1")), book)[0]
    assert action.action == dt.UPDATE


# --- preflight ------------------------------------------------------------


def test_preflight_names_the_issue_types_the_project_actually_has(jira):
    """A Kanban project usually offers Task and Bug and no Story. Finding that out
    after someone signed sixty rows is the wrong time."""
    jira.issue_types = ["Task", "Bug"]
    import preflight_check

    result = preflight_check.check(payload(task("FR-001", "h1")), env=ENV)
    assert result["ok"] is False
    assert "no issue type ['Story']" in result["problems"][0]
    assert "Task, Bug" in result["problems"][0]


def test_preflight_warns_but_does_not_block_on_an_unknown_priority(jira):
    """A ticket with no priority still beats no ticket."""
    jira.priorities = ["P1", "P2"]
    import preflight_check

    result = preflight_check.check(payload(task("FR-001", "h1")), env=ENV)
    assert result["ok"] is True
    assert "Medium" in result["warnings"][0]


def test_an_unknown_priority_is_dropped_rather_than_costing_the_ticket(tmp_path, jira):
    """Preflight *promises* those tickets will be created without a priority — and it
    has to be true, because Jira answers 400 to a priority it has never heard of and
    creates nothing. The Priority cell is free text a reviewer can retype, so a typo
    would otherwise cost them the issue rather than the field."""
    jira.priorities = ["P1", "P2"]  # no "Medium" on this instance
    setup_workspace(tmp_path, payload(task("FR-001", "h1")))

    result = pj.run(make_args(tmp_path), env=ENV)

    assert result["ok"] and len(result["created"]) == 1
    assert "priority" not in next(iter(jira.issues.values()))["fields"]


def test_push_blocks_when_the_issue_type_is_missing(tmp_path, jira):
    jira.issue_types = ["Task", "Bug"]
    setup_workspace(tmp_path, payload(task("FR-001", "h1")))
    with pytest.raises(SystemExit, match="no issue type"):
        pj.run(make_args(tmp_path), env=ENV)
    assert jira.count("POST") == 0


def test_labels_survive_the_round_trip(tmp_path, jira):
    """Recovery strips `morkit-id-` off the label to get the id back. If the label we
    send does not carry it, a lost ledger cannot be rebuilt."""
    setup_workspace(tmp_path, payload(task("FR-001", "h1")))
    pj.run(make_args(tmp_path), env=ENV)
    labels = next(iter(jira.issues.values()))["fields"]["labels"]
    assert labels == ["morkit-srs", "morkit-id-FR-001"]
    assert tm.LABEL_ID_PREFIX + "FR-001" in labels
