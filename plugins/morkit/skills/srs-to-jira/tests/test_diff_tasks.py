"""Phase 2 — diff + ledger.

`test_a_reviewers_edit_survives_the_next_run` is the canary. It is the reason the
ledger keeps two hashes instead of one; if someone ever collapses them back into a
single `content_hash`, this test is what fails, and the comment it fails with is the
explanation.
"""

from __future__ import annotations

import json
import multiprocessing
import time

import pytest

import diff_tasks as dt
import jira_map as jm

PROJECT = "PROJ"
BASE_URL = "https://jira.example.com"
MODEL_SHA = "a" * 64


def task(source_id, source_hash, issue_type="Story", summary=None):
    return {
        "source_id": source_id,
        "issue_type": issue_type,
        "summary": summary or f"[{source_id}] thing",
        "description": "body",
        "priority": "Medium",
        "labels": ["morkit-srs", f"morkit-id-{source_id}"],
        "source_hash": source_hash,
    }


def payload(*tasks, skip_nfr=False, deprecated=()):
    return {
        "meta": {
            "lang": "EN",
            "skip_nfr": skip_nfr,
            "model_path": "m.json",
            "model_sha256": MODEL_SHA,
            "deprecated_ids": list(deprecated),
        },
        "warnings": [],
        "tasks": list(tasks),
    }


def ledger(**issues):
    data = jm.new_map(PROJECT, BASE_URL, "m.json", MODEL_SHA)
    data["issues"] = issues
    return data


def created(key, source_hash, pushed_hash=None, overrides=None):
    return {
        "key": key,
        "state": jm.STATE_CREATED,
        "source_hash": source_hash,
        "pushed_hash": pushed_hash or source_hash,
        "overrides": overrides or {},
    }


def actions_by_id(actions):
    return {a.source_id: a for a in actions}


# --- the four routine states --------------------------------------------


def test_no_ledger_means_everything_is_new():
    actions = dt.diff(payload(task("FR-001", "h1"), task("FR-002", "h2")), None)
    assert [a.action for a in actions] == [dt.CREATE, dt.CREATE]
    assert all(a.touches_jira for a in actions)


def test_unchanged_srs_sends_nothing():
    tasks = payload(task("FR-001", "h1"), task("FR-002", "h2"))
    book = ledger(**{"FR-001": created("P-1", "h1"), "FR-002": created("P-2", "h2")})
    actions = dt.diff(tasks, book)
    assert {a.action for a in actions} == {dt.SKIP}
    assert not any(a.touches_jira for a in actions)


def test_changed_requirement_is_an_update_not_a_create():
    tasks = payload(task("FR-001", "h1"), task("FR-002", "h2-NEW"))
    book = ledger(**{"FR-001": created("P-1", "h1"), "FR-002": created("P-2", "h2")})
    by_id = actions_by_id(dt.diff(tasks, book))
    assert by_id["FR-001"].action == dt.SKIP
    assert by_id["FR-002"].action == dt.UPDATE
    assert by_id["FR-002"].key == "P-2"


# --- the revert loop: the reason for two hashes --------------------------


def test_a_reviewers_edit_survives_the_next_run():
    """The scenario that a single content_hash gets wrong.

    Run 1: the reviewer rewrites the summary; we push *their* text and record it as
    `pushed_hash`, while `source_hash` still describes what the SRS generated.

    Run 2: tasks.json is rebuilt from the unchanged SRS, so it carries the original
    machine hash. If the ledger had stored the hash of the *edited* text, the two
    would disagree, we would issue an UPDATE, and that UPDATE would push the machine
    text back over the human's edit — silently, and looking exactly like normal
    operation. With `source_hash` kept separate, an unchanged SRS is a SKIP.
    """
    machine = task("FR-001", "srs-hash-v1", summary="[FR-001] Password reset")
    edited = "[FR-001] Reset password by email"

    book = ledger(
        **{
            "FR-001": created(
                "P-1", "srs-hash-v1", pushed_hash="hash-of-edited", overrides={"summary": edited}
            )
        }
    )

    action = actions_by_id(dt.diff(payload(machine), book))["FR-001"]
    assert action.action == dt.SKIP, "an unchanged SRS must not touch Jira"
    assert jm.get_override(book, "FR-001", "summary") == edited


def test_a_changed_srs_warns_before_it_overwrites_an_edit():
    """Losing a hand-written summary is acceptable when the requirement itself
    changed. Losing it without saying so is not."""
    book = ledger(
        **{"FR-001": created("P-1", "old", overrides={"summary": "[FR-001] my wording"})}
    )
    action = actions_by_id(dt.diff(payload(task("FR-001", "new")), book))["FR-001"]
    assert action.action == dt.UPDATE
    assert "overwritten" in dt.override_warning(action, book)


# --- crash / recovery states ---------------------------------------------


def test_an_interrupted_create_reconciles_instead_of_duplicating():
    """`creating` is written before the POST. Finding one means a previous run died
    with the request in flight: the issue may well exist on Jira."""
    book = ledger(**{"FR-001": {"key": None, "state": jm.STATE_CREATING, "source_hash": "h1"}})
    action = actions_by_id(dt.diff(payload(task("FR-001", "h1")), book))["FR-001"]
    assert action.action == dt.RECONCILE
    assert action.touches_jira


def test_a_recovered_ledger_updates_rather_than_recreating():
    """JQL recovery can rebuild id → key from labels, but no hash can be recovered
    from a Jira issue. Reading a missing hash as "not in the map" would re-create the
    entire backlog; an unnecessary UPDATE is merely wasteful."""
    book = ledger(**{"FR-001": {"key": "P-1", "state": jm.STATE_CREATED, "source_hash": None}})
    action = actions_by_id(dt.diff(payload(task("FR-001", "h1")), book))["FR-001"]
    assert action.action == dt.UPDATE
    assert "recovery" in action.note


# --- things we report but never touch ------------------------------------


def test_skip_nfr_does_not_orphan_the_nfrs_it_filtered():
    """Without meta.skip_nfr, every already-pushed NFR would be reported as gone from
    the SRS and the reviewer told to consider closing perfectly good tickets."""
    book = ledger(**{"FR-001": created("P-1", "h1"), "NFR-01": created("P-9", "h9")})
    actions = dt.diff(payload(task("FR-001", "h1"), skip_nfr=True), book)
    assert [a.action for a in actions] == [dt.SKIP]


def test_deprecated_is_reported_separately_from_orphaned():
    """`status: deprecated` is how the SRS retires a requirement on purpose — it is
    not the same as an id that simply vanished."""
    book = ledger(**{"FR-004": created("P-4", "h4"), "FR-009": created("P-9", "h9")})
    by_id = actions_by_id(dt.diff(payload(deprecated=["FR-004"]), book))
    assert by_id["FR-004"].action == dt.DEPRECATED
    assert by_id["FR-009"].action == dt.ORPHAN
    # Neither is ever sent anywhere: closing a ticket is not reversible.
    assert not by_id["FR-004"].touches_jira and not by_id["FR-009"].touches_jira


# --- ledger safety --------------------------------------------------------


def test_the_approved_file_decides_the_target_not_the_environment():
    """The reviewer signed a file that names a project. If the shell disagrees, that
    is a mistake to stop on — not a preference to follow."""
    with pytest.raises(jm.BindingError, match="did not approve"):
        jm.assert_bindings({"project": "SBX", "base_url": BASE_URL}, "PROD", BASE_URL)
    jm.assert_bindings({"project": PROJECT, "base_url": BASE_URL + "/"}, PROJECT, BASE_URL)


def test_two_different_srs_cannot_share_one_ledger():
    book = ledger(**{"FR-001": created("P-1", "h1")})
    with pytest.raises(jm.BindingError, match="different project-model"):
        jm.assert_same_model(book, {"model_sha256": "b" * 64})


def test_a_path_cannot_escape_the_workspace(tmp_path):
    """These paths are built by the model from chat text. A prompt-injected SRS could
    otherwise aim --map at a real file, and os.replace would destroy it atomically."""
    with pytest.raises(jm.UnsafePathError):
        jm.resolve_within(tmp_path, "../../.ssh/config")
    assert jm.resolve_within(tmp_path, "jira/map.json").is_relative_to(tmp_path)


def test_a_crash_mid_write_leaves_the_old_ledger_intact(tmp_path, monkeypatch):
    path = tmp_path / "jira-map.json"
    jm.save_map_atomic(path, ledger(**{"FR-001": created("P-1", "h1")}))
    before = path.read_bytes()

    def boom(*_args, **_kwargs):
        raise OSError("disk died mid-write")

    monkeypatch.setattr(jm.os, "replace", boom)
    with pytest.raises(OSError):
        jm.save_map_atomic(path, ledger(**{"FR-002": created("P-2", "h2")}))

    assert path.read_bytes() == before  # not truncated, not half-written
    assert not list(tmp_path.glob(".jira-map-*.tmp"))  # temp file cleaned up


def _hold_lock(path, ready, done):
    with jm.map_lock(path):
        ready.set()
        done.wait(5)


def test_a_second_push_cannot_run_while_one_is_in_flight(tmp_path):
    """An atomic write survives a crash; it does nothing about two pushes at once.
    Both would read the same ledger, both create tickets, and the last writer would
    orphan the other's — invisible to every later diff."""
    path = tmp_path / "jira-map.json"
    ready, done = multiprocessing.Event(), multiprocessing.Event()
    holder = multiprocessing.Process(target=_hold_lock, args=(str(path), ready, done))
    holder.start()
    try:
        assert ready.wait(5)
        time.sleep(0.05)
        with pytest.raises(jm.LockedError, match="already running"):
            with jm.map_lock(path):
                pass
    finally:
        done.set()
        holder.join(5)


def test_the_workspace_ignores_itself(tmp_path):
    """It runs inside the customer's repo. `jira-map.json` holds the internal Jira
    hostname and `tasks.json` holds the whole SRS; one `git add -A` commits both."""
    workspace = jm.ensure_private_workspace(tmp_path / "morkit/output/jira/PROJ")
    assert (workspace / ".gitignore").read_text().strip().endswith("*")


def test_it_refuses_to_ignore_a_repository_root(tmp_path, monkeypatch):
    """A bare `--out tasks.json` resolves its parent to `.`. Writing a `*` .gitignore
    there would make git ignore every untracked file in the user's project."""
    (tmp_path / ".git").mkdir()
    with pytest.raises(jm.UnsafePathError, match="project root"):
        jm.ensure_private_workspace(tmp_path)

    monkeypatch.chdir(tmp_path)
    with pytest.raises(jm.UnsafePathError):
        jm.ensure_private_workspace(".")
    assert not (tmp_path / ".gitignore").exists()


def test_ledger_round_trips(tmp_path):
    path = tmp_path / "jira-map.json"
    assert jm.load_map(path) is None  # first run: no ledger yet
    book = ledger(**{"FR-001": created("P-1", "h1")})
    jm.save_map_atomic(path, book)
    assert jm.load_map(path) == book
    assert json.loads(path.read_text())["version"] == jm.VERSION
