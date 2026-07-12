"""Decide, per requirement, what the push must do. Pure function over (tasks, ledger).

This runs twice, on purpose:

  * before the gate, so the reviewer opens a file that already says which rows are
    new, which changed, and which are untouched — they need to know where to look;
  * again inside push, because the `Action` column in that file is a hand-editable
    markdown cell and must never be what decides whether we CREATE or UPDATE.

The second run is the one that stops a re-run of the push command from duplicating
the whole backlog.
"""

from __future__ import annotations

from dataclasses import dataclass

import jira_map as jm

CREATE = "CREATE"
UPDATE = "UPDATE"
SKIP = "SKIP"
RECONCILE = "RECONCILE"  # ledger says "creating": a crash landed between POST and reply
DEPRECATED = "DEPRECATED"  # the SRS retired it on purpose
ORPHAN = "ORPHAN"  # on Jira, gone from the SRS — we report, we never close


@dataclass(frozen=True)
class Action:
    source_id: str
    action: str
    task: dict | None = None  # None for DEPRECATED / ORPHAN
    key: str | None = None  # existing Jira key, when we have one
    note: str = ""

    @property
    def touches_jira(self) -> bool:
        return self.action in (CREATE, UPDATE, RECONCILE)


def diff(tasks_payload: dict, jira_map: dict | None) -> list[Action]:
    """`tasks.json` + ledger -> one Action per requirement, in a stable order."""
    issues = (jira_map or {}).get("issues") or {}
    meta = tasks_payload.get("meta") or {}
    tasks = tasks_payload.get("tasks") or []
    deprecated_ids = set(meta.get("deprecated_ids") or [])
    skip_nfr = bool(meta.get("skip_nfr"))

    actions = [_for_task(task, issues.get(task["source_id"])) for task in tasks]
    seen = {task["source_id"] for task in tasks}

    for source_id, entry in issues.items():
        if source_id in seen:
            continue
        if source_id in deprecated_ids:
            actions.append(
                Action(source_id, DEPRECATED, key=entry.get("key"),
                       note="retired in the SRS (status: deprecated)")
            )
        elif skip_nfr and source_id.startswith("NFR-"):
            # Filtered out by --skip-nfr, not deleted. Reporting these as orphaned
            # would tell the reviewer to consider closing perfectly valid tickets.
            continue
        else:
            actions.append(
                Action(source_id, ORPHAN, key=entry.get("key"),
                       note="on Jira but no longer in the SRS")
            )

    return actions


def _for_task(task: dict, entry: dict | None) -> Action:
    source_id = task["source_id"]
    if entry is None:
        return Action(source_id, CREATE, task=task)

    key = entry.get("key")
    if entry.get("state") == jm.STATE_CREATING:
        return Action(
            source_id, RECONCILE, task=task, key=key,
            note="a previous run died mid-create; check Jira before creating again",
        )

    stored = entry.get("source_hash")
    if stored is None:
        # Recovery rebuilt the ledger from Jira labels; a hash cannot be recovered
        # from an issue. UPDATE is the safe reading — treating it as "not in the map"
        # would re-create the entire backlog.
        return Action(source_id, UPDATE, task=task, key=key,
                      note="hash unknown after recovery")

    if stored == task["source_hash"]:
        return Action(source_id, SKIP, task=task, key=key)

    return Action(source_id, UPDATE, task=task, key=key)


def override_warning(action: Action, jira_map: dict | None) -> str:
    """An UPDATE rewrites the issue from the SRS — including over a reviewer's edit.

    Say so in the gate file. Losing a hand-written summary is acceptable when the
    requirement itself changed; losing it *silently* is not.
    """
    if action.action != UPDATE or not jira_map:
        return ""
    if jm.get_override(jira_map, action.source_id, "summary"):
        return "your earlier summary edit will be overwritten by the new SRS text"
    return ""
