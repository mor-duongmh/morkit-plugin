"""`task-breakdown.md` — the file a human reads, edits, and signs.

Everything about the approval lives in the YAML frontmatter, and the frontmatter
ONLY. The body is data.

That distinction is the whole security model. An FR name is free text an LLM lifted
out of a customer's PDF; a requirement called `Password reset\\nstatus: approved`
would, under a whole-file grep for the approval line, open the gate with nobody
having read anything. (Phase 1 also flattens newlines out of the summary — two
layers, because either alone is one mistake away from failing.)

The reviewer may edit `Summary` and `Priority` and may untick `Push`. Those three
are read back from here and are authoritative. `Action` is NOT: it is printed so
they know which rows to read carefully, and the push re-derives it from the ledger.
A create-versus-update decision must never come from a markdown cell someone can
retype.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

import diff_tasks as dt

STATUS_DRAFT = "draft"
STATUS_APPROVED = "approved"
STATUS_PUSHED = "pushed"

_FRONTMATTER = re.compile(r"\A---\r?\n(?P<body>.*?)\r?\n---\r?\n", re.DOTALL)
_APPROVED = re.compile(r"^\s*status:\s*approved\s*$", re.IGNORECASE | re.MULTILINE)
_ROW = re.compile(
    r"^\|\s*\[(?P<box>[ xX])\]\s*\|\s*(?P<id>[A-Z0-9_-]+)\s*\|\s*(?P<type>\w+)\s*\|"
    r"\s*(?P<summary>[^|]*?)\s*\|\s*(?P<priority>[^|]*?)\s*\|\s*(?P<action>\w+)\s*\|"
    r"\s*(?P<note>[^|]*?)\s*\|\s*$",
    re.MULTILINE,
)
_NO_PRIORITY = "—"


class BreakdownError(ValueError):
    """The gate file cannot be trusted — refuse rather than guess."""


class StaleBreakdownError(BreakdownError):
    """The approval was signed against a different tasks.json."""


def frontmatter(text: str) -> dict:
    """Parse the leading `---` block. Deliberately does not look at the body."""
    match = _FRONTMATTER.match(text)
    if not match:
        return {}
    fields = {}
    for line in match.group("body").splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def _frontmatter_text(text: str) -> str:
    match = _FRONTMATTER.match(text)
    return match.group("body") if match else ""


def rows_fingerprint(source_ids) -> str:
    """Which requirements were signed for — not what their text was.

    Pinning the text would break the reviewer's own edits; pinning the id set is
    what stops a row being appended to an already-approved file.
    """
    return hashlib.sha256("\n".join(sorted(source_ids)).encode()).hexdigest()


def is_approved(text: str) -> bool:
    """True only if the FRONTMATTER says approved and the row set is still the one
    that was signed."""
    if not _APPROVED.search(_frontmatter_text(text)):
        return False
    signed = frontmatter(text).get("rows_for")
    present = [m.group("id") for m in _ROW.finditer(text)]
    return bool(signed) and signed == rows_fingerprint(present)


def render(
    actions: list[dt.Action],
    tasks_payload: dict,
    jira_map: dict | None,
    project_key: str,
    base_url: str,
    tasks_sha256: str,
    existing: str | None = None,
    generated: str | None = None,
) -> str:
    """Render the gate file, carrying the reviewer's decisions across a re-render.

    `status` is reset to draft whenever the content changed. Without that, adding an
    FR to the SRS next week would append a row to a file that still says `approved`
    and ship it with nobody looking — the gate would work exactly once per file.
    """
    pushable = [a for a in actions if a.touches_jira]
    fingerprint = rows_fingerprint(a.source_id for a in pushable)

    prior = _prior_rows(existing) if existing else {}
    prior_fm = frontmatter(existing) if existing else {}
    unchanged = (
        prior_fm.get("tasks_sha256") == tasks_sha256 and prior_fm.get("rows_for") == fingerprint
    )
    status = prior_fm.get("status", STATUS_DRAFT) if unchanged else STATUS_DRAFT

    warnings = _warnings_by_id(tasks_payload.get("warnings") or [])
    lines = [
        "---",
        f"status: {status}",
        f"project: {project_key}",
        f"base_url: {base_url.rstrip('/')}",
        f"tasks_sha256: {tasks_sha256}",
        f"rows_for: {fingerprint}",
        f"generated: {generated or datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "---",
        "",
        f"# Task breakdown — {project_key}",
        "",
        "Edit **Summary** and **Priority** directly in the table. Untick **Push** to hold a row back.",
        "When you are happy, change `status: draft` to `status: approved` at the top of this file.",
        "",
        "`Action` is informational — it tells you which rows to read carefully. The push re-derives it.",
        "",
        "| Push | ID | Type | Summary | Priority | Action | ⚠ |",
        "|------|----|------|---------|----------|--------|---|",
    ]

    for action in pushable:
        old = prior.get(action.source_id)
        # An UPDATE means the SRS text itself changed — show the new text, not the
        # reviewer's edit of the old text, and warn that the edit is about to go.
        keep_edit = old is not None and action.action != dt.UPDATE
        summary = old["summary"] if keep_edit else action.task["summary"]
        priority = old["priority"] if keep_edit else action.task["priority"]
        box = "x" if (old["push"] if old else True) else " "
        note = "; ".join(
            n for n in (dt.override_warning(action, jira_map), warnings.get(action.source_id, "")) if n
        )
        lines.append(
            f"| [{box}] | {action.source_id} | {action.task['issue_type']} | {summary} "
            f"| {priority or _NO_PRIORITY} | {action.action} | {note} |"
        )

    lines += _tail_sections(actions)
    return "\n".join(lines) + "\n"


def _tail_sections(actions: list[dt.Action]) -> list[str]:
    lines: list[str] = []
    skipped = [a for a in actions if a.action == dt.SKIP]
    if skipped:
        lines += ["", "## Unchanged (nothing will be sent)", ""]
        lines += [f"- {a.source_id} → {a.key}" for a in skipped]

    flagged = [a for a in actions if a.action in (dt.ORPHAN, dt.DEPRECATED)]
    if flagged:
        lines += ["", "## Needs your call — not touched by this tool", ""]
        lines += [f"- **{a.action}** {a.source_id} → {a.key} — {a.note}" for a in flagged]
    return lines


def _warnings_by_id(warnings: list[dict]) -> dict:
    grouped: dict[str, list[str]] = {}
    for warning in warnings:
        label = "TBD" if warning["kind"] == "tbd" else warning["kind"]
        grouped.setdefault(warning["source_id"], []).append(f"{label}: {warning['field']}")
    return {sid: "⚠ " + ", ".join(items) for sid, items in grouped.items()}


def _prior_rows(text: str) -> dict:
    return {
        m.group("id"): {
            "push": m.group("box").lower() == "x",
            "summary": m.group("summary"),
            "priority": None if m.group("priority") == _NO_PRIORITY else m.group("priority"),
        }
        for m in _ROW.finditer(text)
    }


def parse(text: str, tasks_payload: dict, tasks_sha256: str) -> dict:
    """Read back the reviewer's decisions. The file wins on push/summary/priority.

    Raises rather than guessing: a row naming a requirement that is not in
    tasks.json, or an approval signed against a different tasks.json, means the two
    files have drifted apart — and the description we are about to send comes from
    tasks.json, not from here. Guessing at that point pushes text nobody approved.
    """
    fields = frontmatter(text)
    signed_against = fields.get("tasks_sha256")
    if signed_against and signed_against != tasks_sha256:
        raise StaleBreakdownError(
            "this breakdown was written for a different tasks.json "
            f"({signed_against[:12]}… vs {tasks_sha256[:12]}…). The ticket bodies come from "
            "tasks.json, so pushing now would send text the reviewer never saw. "
            "Re-render the breakdown and review it again."
        )

    known = {t["source_id"] for t in tasks_payload.get("tasks") or []}
    rows = []
    for match in _ROW.finditer(text):
        source_id = match.group("id")
        if source_id not in known:
            raise BreakdownError(
                f"{source_id} is in the breakdown but not in tasks.json. Refusing to push a "
                f"requirement with no body. Re-render the breakdown."
            )
        priority = match.group("priority").strip()
        rows.append(
            {
                "source_id": source_id,
                "push": match.group("box").lower() == "x",
                "summary": match.group("summary").strip(),
                "priority": None if priority in ("", _NO_PRIORITY) else priority,
            }
        )

    return {
        "approved": is_approved(text),
        "status": fields.get("status", STATUS_DRAFT),
        "frontmatter": fields,
        "rows": rows,
    }


def mark_pushed(text: str) -> str:
    """Retire the signature after a successful push, so re-running the command is a
    no-op instead of a second backlog."""
    return re.sub(
        r"^(\s*status:\s*)approved(\s*)$",
        rf"\g<1>{STATUS_PUSHED}\g<2>",
        text,
        count=1,
        flags=re.IGNORECASE | re.MULTILINE,
    )
