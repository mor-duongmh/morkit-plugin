"""Send the approved breakdown to Jira. The only script that writes to a live system.

Order matters, and it is this:

    lock -> approved? -> same tasks.json? -> same project? -> re-diff -> preflight -> send

The approval check comes before anything reaches the network, so a refused push
makes zero requests — `Config.calls` proves it in the tests.

The re-diff is the load-bearing step. The `Action` column in the breakdown was
computed when the file was rendered and a human can retype it; if we obeyed it,
running this command twice would say CREATE twice and duplicate the entire backlog.
The ledger decides. The file only says which rows the reviewer allowed, and what
wording they want.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import breakdown_file as bf  # noqa: E402
import diff_tasks as dt  # noqa: E402
import jira_client as jc  # noqa: E402
import jira_map as jm  # noqa: E402
import task_mapper as tm  # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _label_for(task: dict) -> str:
    return task["labels"][1]


def _send_one(cfg, action, row, jira_map, map_path, force, allowed_priorities=None):
    """Write intent, send, record. In that order — the order is the guarantee.

    If the process dies between the POST leaving and the reply arriving, the issue
    exists in Jira and nothing here knows it. The `creating` breadcrumb is what lets
    the next run look the issue up by its label instead of creating a second one.
    """
    task = action.task
    summary = row["summary"] or task["summary"]
    priority = _usable_priority(row["priority"], allowed_priorities)

    if action.action == dt.RECONCILE:
        key = jc.find_by_label(cfg, _label_for(task))
        if key:
            # Hash what is ON the issue, not what we would have sent. The interrupted
            # run created it; the reviewer may have reworded the row since. Recording
            # our guess here would make the next UPDATE think Jira had been edited
            # behind our back and refuse a perfectly legitimate change.
            live = jc.get_issue(cfg, key)
            _record(jira_map, action.source_id, key, task, live["summary"], live["description"])
            jm.save_map_atomic(map_path, jira_map)
            return "reconciled", key
        action = dt.Action(action.source_id, dt.CREATE, task=task)  # it never landed

    if action.action == dt.CREATE:
        jm.set_entry(
            jira_map, action.source_id, state=jm.STATE_CREATING,
            source_hash=task["source_hash"],
        )
        jm.save_map_atomic(map_path, jira_map)  # BEFORE the request, on purpose

        key = jc.create_issue(cfg, task, summary, priority)
        verb = "created"
    else:  # UPDATE
        key = action.key
        if not force:
            _refuse_if_jira_moved_on(cfg, jira_map, action.source_id, key)
        jc.update_issue(cfg, key, task, summary, priority)
        verb = "updated"

    _record(jira_map, action.source_id, key, task, summary, task["description"])
    jm.save_map_atomic(map_path, jira_map)
    return verb, key


def _record(jira_map, source_id, key, task, sent_summary, sent_description) -> None:
    jm.set_entry(
        jira_map, source_id,
        key=key,
        state=jm.STATE_CREATED,
        # The MACHINE hash — never the hash of the reviewer's wording. Storing the
        # edited text's hash here is what makes the next run "fix" their edit away.
        source_hash=task["source_hash"],
        pushed_hash=tm.source_hash(sent_summary, sent_description),
        pushed_at=_now(),
    )
    overrides = {"summary": sent_summary} if sent_summary != task["summary"] else {}
    jira_map["issues"][source_id]["overrides"] = overrides


def _usable_priority(name, allowed):
    """Drop a priority this Jira has never heard of.

    Preflight already promises the user those tickets "will be created without a
    priority" — and it must be true, because Jira answers 400 to an unknown priority
    name and creates nothing. The Priority column is free text a reviewer can retype,
    so a typo would otherwise cost them the ticket, not the field.
    """
    if not name or allowed is None:
        return name  # offline: nothing to check against
    return name if name in allowed else None


def _refuse_if_jira_moved_on(cfg, jira_map, source_id, key):
    """An UPDATE overwrites summary and description with the SRS render.

    By the time anyone re-runs this, a dev may have refined the acceptance criteria
    on the ticket and QA may have appended notes. Blowing that away because a plan
    file changed is not a trade to make silently.
    """
    entry = (jira_map.get("issues") or {}).get(source_id) or {}
    known = entry.get("pushed_hash")
    if not known:
        return  # after a recovery we have nothing to compare against
    live = jc.get_issue(cfg, key)
    if tm.source_hash(live["summary"], live["description"]) != known:
        raise jc.JiraError(
            f"{key} ({source_id}) has been edited on Jira since we last pushed it. "
            "Updating would overwrite that. Re-run with --force if you really mean to."
        )


def _recover(cfg, map_path, tasks_meta):
    """Rebuild the ledger from Jira labels when the file is gone.

    Recovered entries carry `source_hash: null`, which the diff reads as UPDATE — so a
    recovery run rewrites every ticket from the SRS, with the drift guard blind (there
    is no `pushed_hash` to compare against). That is the right trade when the ledger is
    genuinely lost and the alternative is a duplicated backlog. It is a catastrophe on
    a healthy ledger: it would discard every hash and every reviewer override, then
    overwrite a live board. So: only when there is actually nothing to recover from.
    """
    if map_path.exists():
        raise SystemExit(
            f"--recover is for a lost ledger, and {map_path} is right there. Rebuilding "
            "would throw away the hashes and the summary edits it holds, and then rewrite "
            "every ticket from the SRS. If you truly want that, move the file aside first."
        )

    book = jm.new_map(cfg.project_key, cfg.base_url, tasks_meta["model_path"], tasks_meta["model_sha256"])
    prefix = tm.LABEL_ID_PREFIX
    for issue in jc.search_by_label(cfg, jc.LABEL_ALL):
        for label in issue.get("fields", {}).get("labels") or []:
            if label.startswith(prefix):
                book["issues"][label[len(prefix):]] = {
                    "key": issue["key"], "state": jm.STATE_CREATED, "source_hash": None,
                }
    jm.save_map_atomic(map_path, book)
    return book


def run(args, env=None) -> dict:
    breakdown_path = Path(args.breakdown)
    tasks_path = Path(args.tasks)
    map_path = Path(args.map)

    if args.workspace:
        # Assign the results back — resolve_within RETURNS the safe path. Checking one
        # path and then writing to another is not a guard, and a relative --map would
        # land in the cwd instead of the workspace, where the next run would not find
        # it: every requirement would look new, and the backlog would be created twice.
        map_path = jm.resolve_within(args.workspace, map_path)
        breakdown_path = jm.resolve_within(args.workspace, breakdown_path)
        tasks_path = jm.resolve_within(args.workspace, tasks_path)

    raw_tasks = tasks_path.read_bytes()
    tasks_payload = json.loads(raw_tasks)
    tasks_sha256 = hashlib.sha256(raw_tasks).hexdigest()
    text = breakdown_path.read_text(encoding="utf-8")

    # --- gates, before anything can reach the network ---
    if not bf.is_approved(text):
        status = bf.frontmatter(text).get("status", "?")
        raise SystemExit(
            f"Not approved (status: {status}). Open {breakdown_path}, review the table, "
            "and set `status: approved` in the frontmatter. Nothing was sent."
        )

    parsed = bf.parse(text, tasks_payload, tasks_sha256)  # raises if stale / unknown row
    # Offline still needs the project key and base URL — the approval is bound to them —
    # but not a token, because nothing will be sent. Demanding one would make the
    # rehearsal path useless to the very person it exists for: someone without a token.
    cfg = jc.config_from_env(env, require_credential=not args.offline)
    jm.assert_bindings(parsed["frontmatter"], cfg.project_key, cfg.base_url)

    with jm.map_lock(map_path):
        book = jm.load_map(map_path)
        if book is None:
            book = jm.new_map(
                cfg.project_key, cfg.base_url,
                tasks_payload["meta"]["model_path"], tasks_payload["meta"]["model_sha256"],
            )
        jm.assert_same_model(book, tasks_payload["meta"])

        if args.recover:
            book = _recover(cfg, map_path, tasks_payload["meta"])

        priorities = None if args.offline else _check_preflight(cfg, tasks_payload)

        allowed = {r["source_id"]: r for r in parsed["rows"] if r["push"]}
        actions = dt.diff(tasks_payload, book)  # the ledger decides, not the file
        result = _apply(cfg, actions, allowed, book, map_path, args, priorities)

        if not args.dry_run and not result["failed"]:
            breakdown_path.write_text(bf.mark_pushed(text), encoding="utf-8")

    result["ok"] = not result["failed"]
    result["requests"] = cfg.calls
    return result


# We report these and never touch them. Closing a ticket is not reversible, and
# "gone from the SRS" is not the same claim as "should not exist" — that is a
# human's call to make, on their board, with context we do not have.
_REPORT_ONLY = {dt.ORPHAN: "orphans", dt.DEPRECATED: "deprecated"}


def _apply(cfg, actions, allowed, book, map_path, args, priorities=None) -> dict:
    result = {"created": [], "updated": [], "reconciled": [], "skipped": [], "held_back": [],
              "orphans": [], "deprecated": [], "would": [], "failed": []}

    for action in actions:
        bucket = _classify(action, allowed)
        if bucket in ("orphans", "deprecated"):
            result[bucket].append(
                {"source_id": action.source_id, "key": action.key, "note": action.note}
            )
        elif bucket in ("skipped", "held_back"):
            result[bucket].append(action.source_id)
        elif args.dry_run:
            result["would"].append({"source_id": action.source_id, "action": action.action})
        else:
            _send_and_record(cfg, action, allowed, book, map_path, args, result, priorities)

    return result


def _classify(action, allowed) -> str:
    if action.action in _REPORT_ONLY:
        return _REPORT_ONLY[action.action]
    if not action.touches_jira:
        return "skipped"
    if action.source_id not in allowed:
        return "held_back"  # the reviewer unticked it
    return "send"


def _send_and_record(cfg, action, allowed, book, map_path, args, result, priorities=None) -> None:
    try:
        verb, key = _send_one(
            cfg, action, allowed[action.source_id], book, map_path, args.force, priorities
        )
        result[verb].append({"source_id": action.source_id, "key": key})
    except jc.JiraError as exc:
        # One bad issue does not abandon the rest; the ledger already holds whatever
        # landed, so a re-run picks up exactly where this left off.
        result["failed"].append({"source_id": action.source_id, "error": jc.redact(str(exc), cfg)})


def _check_preflight(cfg, tasks_payload):
    """Blocks on a missing issue type; returns the instance's real priority names."""
    pre = jc.preflight(cfg)
    wanted = {
        cfg.story_type if t["issue_type"] == "Story" else cfg.task_type
        for t in tasks_payload["tasks"]
    }
    missing = pre.issue_type_missing(wanted)
    if missing:
        raise SystemExit(
            f"Project {cfg.project_key} has no issue type {missing}. It offers: "
            f"{', '.join(pre.issue_types)}. Set JIRA_ISSUE_TYPE_STORY / JIRA_ISSUE_TYPE_TASK."
        )
    return set(pre.priorities)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Push an approved breakdown to Jira")
    parser.add_argument("--breakdown", required=True)
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--map", required=True)
    parser.add_argument("--workspace", help="confine --map/--breakdown under this dir")
    parser.add_argument("--dry-run", action="store_true", help="preflight + diff, send nothing")
    parser.add_argument("--offline", action="store_true", help="no network at all")
    parser.add_argument("--recover", action="store_true", help="rebuild the ledger from Jira labels")
    parser.add_argument("--force", action="store_true", help="update even if Jira was edited since")
    args = parser.parse_args(argv)

    try:
        result = run(args)
    except (
        jc.ConfigError,      # the environment is not safe to run against
        jc.JiraError,        # preflight or recovery failed outside the per-row guard
        jm.BindingError,     # the approval does not match the target
        jm.LockedError,      # another push holds the lock
        jm.UnsafePathError,  # --map/--out tried to leave the workspace
        bf.BreakdownError,   # the gate file cannot be trusted
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
