"""Apply a PatchPlan to a markdown doc atomically.

Operations:
    INSERT             — add new block at sorted position by ID
    REPLACE            — overwrite block body for existing section
    MOVE_TO_APPENDIX   — relocate to Appendix Z with [DEPRECATED] marker
    SKIP               — no-op (manual edits or untracked sections preserved)

Atomic write: writes to {doc}.tmp, validates by re-parsing, then renames
(os.replace, atomic on POSIX + Windows). Backup kept at {doc}.bak.

Updates `.docs-hero-meta.json` with new section hashes + version.

CLI:
    apply-patch.py --plan plan.json --doc docs/srs.md --meta docs/.docs-hero-meta.json
                   [--dry-run] [--no-backup]
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.canonicalize import compute_hash  # noqa: E402
from lib.deprecation_mover import APPENDIX_Z_HEADING, appendix_z_preamble, move_to_appendix_z  # noqa: E402
from lib.diff_schema import (  # noqa: E402
    DocMeta,
    PatchPlan,
    RevisionEntry,
    load_meta,
    load_patch_plan,
    now_iso,
    save_meta,
)
from lib.id_allocator import parse_id  # noqa: E402
from lib.markdown_ast import (  # noqa: E402
    Block,
    parse_doc,
    serialize_blocks,
    split_preamble_postamble,
)


def _id_sort_key(section_id: str) -> tuple:
    """Numeric-aware sort: FR-001 < FR-002 < FR-010."""
    parsed = parse_id(section_id)
    if parsed is None:
        return (section_id,)
    prefix, num = parsed
    return (prefix, num)


def apply_patch(
    plan: PatchPlan, doc_path: Path, meta_path: Path, dry_run: bool = False, no_backup: bool = False
) -> str:
    """Apply patch plan; returns final markdown text. If dry_run=True, no writes."""
    if not doc_path.exists():
        # Allow patching from empty (init-like flow)
        text = ""
    else:
        text = doc_path.read_text(encoding="utf-8")

    blocks = parse_doc(text)
    preamble, postamble = split_preamble_postamble(text, blocks)
    section_order: list[str] = sorted(blocks.keys(), key=lambda sid: blocks[sid].line_start)

    # Apply ops
    for op in plan.ops:
        if op.op == "INSERT":
            blocks[op.section_id] = Block(
                id=op.section_id,
                heading_level=3,
                heading_text=op.section_id,
                body_md=(op.block_md or "") + "\n",
                line_start=0,
                line_end=0,
            )
            if op.section_id not in section_order:
                section_order.append(op.section_id)

        elif op.op == "REPLACE":
            if op.section_id not in blocks:
                # Treat as INSERT
                blocks[op.section_id] = Block(
                    id=op.section_id,
                    heading_level=3,
                    heading_text=op.section_id,
                    body_md=(op.block_md or "") + "\n",
                    line_start=0,
                    line_end=0,
                )
                if op.section_id not in section_order:
                    section_order.append(op.section_id)
            else:
                old = blocks[op.section_id]
                blocks[op.section_id] = Block(
                    id=op.section_id,
                    heading_level=old.heading_level,
                    heading_text=old.heading_text,
                    body_md=(op.block_md or "") + "\n",
                    line_start=old.line_start,
                    line_end=old.line_end,
                    parent_section=old.parent_section,
                )

        elif op.op == "MOVE_TO_APPENDIX":
            blocks, section_order = move_to_appendix_z(
                blocks,
                section_order,
                op.section_id,
                op.marker or "[DEPRECATED]",
                op.reason or "Deprecated",
            )

        # SKIP: no-op

    # Re-sort: tracked sections by ID, then deprecated at end (Appendix Z)
    main_sections = [sid for sid in section_order if not sid.startswith("DEPRECATED-")]
    deprecated_sections = [sid for sid in section_order if sid.startswith("DEPRECATED-")]
    main_sections.sort(key=_id_sort_key)
    section_order = main_sections + deprecated_sections

    # Add Appendix Z preamble if needed
    if deprecated_sections and APPENDIX_Z_HEADING not in (postamble or ""):
        postamble = appendix_z_preamble() + (postamble or "")

    # Append revision history if revision_entry present
    if plan.revision_entry:
        postamble = _append_revision(postamble, plan.revision_entry)

    final_text = serialize_blocks(blocks, section_order, preamble, postamble)

    # Sanity check: result must be parseable (markdown not corrupted)
    try:
        parse_doc(final_text)
    except Exception as exc:
        raise RuntimeError(f"apply-patch: post-render parse failed: {exc}") from exc

    if dry_run:
        return final_text

    # Atomic write
    tmp_path = doc_path.with_suffix(doc_path.suffix + ".tmp")
    tmp_path.write_text(final_text, encoding="utf-8")
    if not no_backup and doc_path.exists():
        backup = doc_path.with_suffix(doc_path.suffix + ".bak")
        if backup.exists():
            backup.unlink()
        doc_path.rename(backup)
    os.replace(tmp_path, doc_path)

    # Update meta sidecar — use post-write parsed blocks so hashes match
    # what detect-manual-edits will compute on the next run.
    _update_meta_from_file(meta_path, doc_path, plan)
    return final_text


def _update_meta_from_file(meta_path: Path, doc_path: Path, plan: PatchPlan) -> None:
    """Re-parse the on-disk doc and write hashes that round-trip through parse."""
    text = doc_path.read_text(encoding="utf-8")
    reparsed = parse_doc(text)

    meta = load_meta(meta_path)
    rel_key = doc_path.name
    try:
        rel_key = str(doc_path.relative_to(meta_path.parent))
    except ValueError:
        pass

    section_order_disk = sorted(reparsed.keys(), key=lambda sid: reparsed[sid].line_start)
    section_hashes = {sid: compute_hash(reparsed[sid].body_md) for sid in section_order_disk}
    deprecated = [sid for sid in section_order_disk if sid.startswith("DEPRECATED-")]

    meta.docs[rel_key] = DocMeta(
        doc_version=plan.next_version,
        last_render=now_iso(),
        section_hashes=section_hashes,
        section_order=section_order_disk,
        deprecated=deprecated,
    )
    save_meta(meta, meta_path)


def _append_revision(postamble: str, entry: RevisionEntry) -> str:
    """Append a row to the revision history table, or create it if missing."""
    row = (
        f"| {entry.version} | {entry.date} | {entry.author} | {entry.changes_summary} |\n"
    )
    if "Revision History" in (postamble or "") or "改訂履歴" in (postamble or ""):
        # Best-effort: append before next non-table line after the table
        lines = postamble.splitlines(keepends=True)
        # Find last table row in the revision section
        last_pipe_idx = -1
        for i, line in enumerate(lines):
            if line.lstrip().startswith("|"):
                last_pipe_idx = i
        if last_pipe_idx >= 0:
            lines.insert(last_pipe_idx + 1, row)
            return "".join(lines)
    # No revision section yet — append minimal one
    section = (
        "\n## Revision History\n\n"
        "| Version | Date | Author | Changes |\n"
        "|---|---|---|---|\n"
        f"{row}"
    )
    return (postamble or "") + section


def _update_meta(
    meta_path: Path,
    doc_path: Path,
    plan: PatchPlan,
    blocks: dict[str, Block],
    section_order: list[str],
) -> None:
    meta = load_meta(meta_path)
    rel_key = doc_path.name
    try:
        rel_key = str(doc_path.relative_to(meta_path.parent))
    except ValueError:
        pass

    section_hashes = {sid: compute_hash(blocks[sid].body_md) for sid in section_order if sid in blocks}
    deprecated = [sid for sid in section_order if sid.startswith("DEPRECATED-")]

    meta.docs[rel_key] = DocMeta(
        doc_version=plan.next_version,
        last_render=now_iso(),
        section_hashes=section_hashes,
        section_order=list(section_order),
        deprecated=deprecated,
    )
    save_meta(meta, meta_path)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--plan", required=True)
    p.add_argument("--doc", required=True)
    p.add_argument("--meta", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-backup", action="store_true")
    args = p.parse_args()

    plan = load_patch_plan(args.plan)
    doc_path = Path(args.doc)
    meta_path = Path(args.meta)

    final = apply_patch(plan, doc_path, meta_path, dry_run=args.dry_run, no_backup=args.no_backup)
    if args.dry_run:
        print(final)
        return 0

    print(
        f"Applied {len(plan.ops)} ops to {doc_path} "
        f"({plan.current_version} → {plan.next_version})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
