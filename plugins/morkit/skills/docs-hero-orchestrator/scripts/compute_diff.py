"""Compute a PatchPlan from a Delta + ManualEditReport.

Takes:
    delta.json             — proposed changes (ADD/UPDATE/DEPRECATE entities)
    manual-edits.json      — current state of doc sections (clean/manual_edit/...)
    existing doc           — to determine current version

Decisions per change:
    ADD:
      - If entity_id already exists in doc → convert to UPDATE (with same logic)
      - Else: INSERT op at sorted position
    UPDATE:
      - If section status == "manual_edit" or "untracked" → SKIP (preserve user edits)
      - If "deleted_by_user" → SKIP (don't resurrect)
      - If "clean" → REPLACE op
    DEPRECATE:
      - Always MOVE_TO_APPENDIX (with marker)

Version bump:
    DEPRECATE → major bump (breaking)
    ADD/UPDATE → minor bump
    No-op → no bump

CLI:
    compute-diff.py --delta delta.json --doc docs/srs.md --manual-edits edits.json --output plan.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.diff_schema import (  # noqa: E402
    PatchOp,
    PatchPlan,
    RevisionEntry,
    SectionStatus,
    load_manual_edit_report,
    now_iso,
    save_patch_plan,
)
from lib.normalized_schema import Change, Delta, load_delta  # noqa: E402

# Map entity_type → section ID prefix (matches phase-04..06 convention)
_PREFIX_FROM_TYPE = {
    "FR": "FR",
    "NFR": "NFR",
    "SCREEN": "SCREEN",
    "DATA": "DATA",
    "INT": "INT",
    "TABLE": "TBL",
    "INDEX": "IDX",
    "REL": "REL",
    "ENUM": "ENUM",
    "ENDPOINT": "ENDPOINT",
    "ERROR_CODE": "ERR",
    "WEBHOOK": "WEBHOOK",
}


def _bump_version(current: str, has_breaking: bool, has_change: bool) -> str:
    parts = current.split(".")
    while len(parts) < 3:
        parts.append("0")
    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return current
    if has_breaking:
        return f"{major + 1}.0.0"
    if has_change:
        return f"{major}.{minor + 1}.0"
    return current


def _section_status_lookup(report_sections: list[SectionStatus]) -> dict[str, SectionStatus]:
    return {s.section_id: s for s in report_sections}


def _format_block_md(change: Change) -> str:
    """Render entity payload as markdown block.

    Minimal: heading + key fields. Per-template renderers in sub-skills produce
    fancier output; this is the fallback for compute-diff phase.
    """
    payload = change.payload or {}
    entity_id = change.entity_id
    name = payload.get("name") or entity_id
    description = payload.get("description", "")
    main_flow = payload.get("main_flow") or []
    priority = payload.get("priority", "")

    lines = [f"### {entity_id}: {name}", ""]
    if description:
        lines.append(f"- **Description:** {description}")
    if priority:
        lines.append(f"- **Priority:** {priority}")
    if main_flow:
        lines.append("- **Main flow:**")
        for i, step in enumerate(main_flow, start=1):
            lines.append(f"  {i}. {step}")
    if payload.get("source"):
        lines.append(f"- **Source:** {payload['source'].get('origin', 'unknown')}")
    lines.append("")
    return "\n".join(lines)


def compute_diff(
    delta: Delta,
    manual_edit_report,
    current_version: str = "1.0",
) -> PatchPlan:
    """Build a PatchPlan from delta + manual edit report."""
    status_lookup = _section_status_lookup(manual_edit_report.sections)
    existing_ids = {s.section_id for s in manual_edit_report.sections if s.status != "deleted_by_user"}

    ops: list[PatchOp] = []
    conflicts: list[SectionStatus] = []
    has_breaking = False
    has_change = False
    summary_parts: list[str] = []

    for change in delta.changes:
        # Map delta entity_id → doc section_id (delta uses entity prefix; doc uses canonical)
        section_id = _resolve_section_id(change)

        if change.op == "ADD":
            if section_id in existing_ids:
                # Convert to UPDATE
                _handle_update(
                    section_id, change, status_lookup, ops, conflicts, summary_parts
                )
                has_change = True
            else:
                ops.append(
                    PatchOp(
                        op="INSERT",
                        section_id=section_id,
                        block_md=_format_block_md(change),
                        reason=change.reason,
                    )
                )
                summary_parts.append(f"ADD {section_id}")
                has_change = True

        elif change.op == "UPDATE":
            _handle_update(
                section_id, change, status_lookup, ops, conflicts, summary_parts
            )
            has_change = True

        elif change.op == "DEPRECATE":
            ops.append(
                PatchOp(
                    op="MOVE_TO_APPENDIX",
                    section_id=section_id,
                    marker=f"[DEPRECATED v{current_version}]",
                    reason=change.reason or "Deprecated",
                )
            )
            summary_parts.append(f"DEPRECATE {section_id}")
            has_breaking = True
            has_change = True

    next_version = _bump_version(current_version, has_breaking, has_change)
    revision = (
        RevisionEntry(
            version=next_version,
            date=now_iso().split("T")[0],
            changes_summary="; ".join(summary_parts) if summary_parts else "No changes",
        )
        if has_change
        else None
    )

    return PatchPlan(
        doc_path=manual_edit_report.doc_path,
        current_version=current_version,
        next_version=next_version,
        ops=ops,
        revision_entry=revision,
        conflicts=conflicts,
    )


def _resolve_section_id(change: Change) -> str:
    """Map delta entity_id → canonical doc section_id."""
    expected_prefix = _PREFIX_FROM_TYPE.get(change.entity_type, change.entity_type)
    eid = change.entity_id

    # If entity_id already starts with expected prefix, return as-is
    if eid.startswith(expected_prefix + "-"):
        return eid

    # Sometimes delta uses raw method+path for ENDPOINT (e.g. "POST /users")
    if change.entity_type == "ENDPOINT" and " " in eid:
        method, path = eid.split(maxsplit=1)
        from lib.markdown_ast import _slugify_path  # type: ignore[attr-defined]

        return f"ENDPOINT-{method.upper()}-{_slugify_path(path)}"

    return f"{expected_prefix}-{eid}"


def _handle_update(
    section_id: str,
    change: Change,
    status_lookup: dict[str, SectionStatus],
    ops: list[PatchOp],
    conflicts: list[SectionStatus],
    summary_parts: list[str],
) -> None:
    status = status_lookup.get(section_id)
    if status is None or status.status in ("manual_edit", "untracked", "deleted_by_user"):
        # SKIP — preserve manual edits or don't resurrect deletions
        skip_reason = status.status if status else "section_missing"
        ops.append(
            PatchOp(
                op="SKIP",
                section_id=section_id,
                reason=skip_reason,
                proposed_change=change.model_dump(exclude_none=True),
            )
        )
        if status is not None:
            conflicts.append(status)
        summary_parts.append(f"SKIP {section_id} ({skip_reason})")
        return

    # Clean → REPLACE
    ops.append(
        PatchOp(
            op="REPLACE",
            section_id=section_id,
            block_md=_format_block_md(change),
            old_hash=status.current_hash,
            reason=change.reason,
        )
    )
    summary_parts.append(f"UPDATE {section_id}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--delta", required=True)
    p.add_argument("--doc", required=True, help="Path to existing doc (for current version)")
    p.add_argument("--manual-edits", required=True)
    p.add_argument("--current-version", default="1.0")
    p.add_argument("--output", required=True)
    args = p.parse_args()

    delta = load_delta(args.delta)
    report = load_manual_edit_report(args.manual_edits)
    plan = compute_diff(delta, report, current_version=args.current_version)
    save_patch_plan(plan, args.output)
    print(
        f"Plan: {len(plan.ops)} ops ({len(plan.conflicts)} conflicts), "
        f"{plan.current_version} → {plan.next_version} -> {args.output}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
