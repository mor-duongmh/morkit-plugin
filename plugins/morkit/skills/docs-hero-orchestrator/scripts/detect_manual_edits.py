"""Detect manually-edited sections by comparing current hashes vs meta sidecar.

Statuses:
    clean            — current hash == expected hash (no edits since last render)
    manual_edit      — hashes differ (user edited the section)
    untracked        — section in doc but not in meta (user added new section)
    deleted_by_user  — section in meta but not in doc (user removed it)

CLI:
    detect-manual-edits.py --doc docs/srs.md --meta docs/.docs-hero-meta.json --output report.json

Public API:
    detect_manual_edits(doc_path, meta_path) -> ManualEditReport
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.canonicalize import compute_hash  # noqa: E402
from lib.diff_schema import (  # noqa: E402
    ManualEditReport,
    ManualEditSummary,
    SectionStatus,
    load_meta,
    now_iso,
    save_manual_edit_report,
)
from lib.markdown_ast import parse_doc  # noqa: E402


def detect_manual_edits(
    doc_path: str | Path, meta_path: str | Path
) -> ManualEditReport:
    """Build report of section statuses for one doc."""
    doc_path = Path(doc_path)
    meta_path = Path(meta_path)

    if not doc_path.exists():
        raise FileNotFoundError(f"Doc not found: {doc_path}")

    text = doc_path.read_text(encoding="utf-8")
    blocks = parse_doc(text)

    # Resolve meta entry for this doc
    expected_hashes: dict[str, str] = {}
    if meta_path.exists():
        meta = load_meta(meta_path)
        # Find matching doc entry: try relative variants + filename
        candidates = [
            doc_path.name,
            str(doc_path),
        ]
        meta_dir = meta_path.parent
        try:
            candidates.append(str(doc_path.relative_to(meta_dir)))
        except ValueError:
            pass
        for cand in candidates:
            if cand in meta.docs:
                expected_hashes = dict(meta.docs[cand].section_hashes)
                break

    sections: list[SectionStatus] = []
    seen_in_doc: set[str] = set()

    for sid, block in blocks.items():
        seen_in_doc.add(sid)
        current_hash = compute_hash(block.body_md)
        expected_hash = expected_hashes.get(sid)

        if expected_hash is None:
            status = "untracked"
        elif expected_hash == current_hash:
            status = "clean"
        else:
            status = "manual_edit"

        sections.append(
            SectionStatus(
                section_id=sid,
                status=status,  # type: ignore[arg-type]
                expected_hash=expected_hash,
                current_hash=current_hash,
                line_range=(block.line_start, block.line_end),
            )
        )

    # Sections in meta but missing from doc
    for sid, expected_hash in expected_hashes.items():
        if sid not in seen_in_doc:
            sections.append(
                SectionStatus(
                    section_id=sid,
                    status="deleted_by_user",
                    expected_hash=expected_hash,
                    current_hash=None,
                )
            )

    summary = ManualEditSummary(
        total_sections=len(sections),
        clean=sum(1 for s in sections if s.status == "clean"),
        manual_edit=sum(1 for s in sections if s.status == "manual_edit"),
        untracked=sum(1 for s in sections if s.status == "untracked"),
        deleted_by_user=sum(1 for s in sections if s.status == "deleted_by_user"),
    )

    return ManualEditReport(
        doc_path=str(doc_path),
        scan_at=now_iso(),
        summary=summary,
        sections=sections,
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--doc", required=True)
    p.add_argument("--meta", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    report = detect_manual_edits(args.doc, args.meta)
    save_manual_edit_report(report, args.output)
    s = report.summary
    print(
        f"Scanned {report.doc_path}: {s.clean} clean, {s.manual_edit} edits, "
        f"{s.untracked} untracked, {s.deleted_by_user} deleted -> {args.output}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
