"""Human review gate: staging snapshot / surface / promote.

The renderer is untouched — `dispatch_coordinator init --docs-dir <staging>`
already renders into any directory, so staging is just a different target.
This module adds the three mechanics the per-doc review loop needs:

    snapshot — record the PRE-edit section-hash baseline of a staged doc into
               meta.review[doc] (status=pending). Called right after render.
    surface  — list staged-doc sections (+ ID-section diff vs docs/<doc>) as a
               JSON payload the LLM presents to the reviewer.
    promote  — atomic-copy staged → docs/<doc>, then write the PRE-edit baseline
               into DocMeta.section_hashes and flip review status to approved.

Keystone (verified): meta must store the hash of the PRE-edit render, NOT the
reviewer-edited file. Otherwise detect_manual_edits sees the edited section as
`clean` and a later update/sync overwrites the reviewer's change.

CLI:
    review_gate.py snapshot --staged STAGED --doc-name api-docs.md --meta META
    review_gate.py surface  --staged STAGED --doc-name api-docs.md --docs-dir DOCS
    review_gate.py promote  --staged STAGED --doc-name api-docs.md \
                            --docs-dir DOCS --meta META

Public API:
    snapshot(staged_path, doc_name, meta_path) -> ReviewState
    surface(staged_path, doc_name, docs_dir) -> dict
    promote(staged_path, doc_name, docs_dir, meta_path) -> Path
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.canonicalize import compute_hash  # noqa: E402
from lib.diff_schema import (  # noqa: E402
    DocMeta,
    ReviewState,
    load_meta,
    now_iso,
    save_meta,
)
from lib.markdown_ast import extract_section_id, parse_doc  # noqa: E402
from markdown_it import MarkdownIt  # noqa: E402


def _section_hashes(md_text: str) -> tuple[dict[str, str], list[str]]:
    """Return ({section_id -> hash}, section_order) for ID-anchored sections."""
    blocks = parse_doc(md_text)
    order = sorted(blocks.keys(), key=lambda sid: blocks[sid].line_start)
    hashes = {sid: compute_hash(blocks[sid].body_md) for sid in order}
    return hashes, order


def _list_headings(md_text: str) -> list[tuple[int, str, str | None]]:
    """Return (level, title, section_id|None) for every heading in the doc."""
    md = MarkdownIt("commonmark", {"html": False})
    tokens = md.parse(md_text)
    out: list[tuple[int, str, str | None]] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == "heading_open":
            level = int(tok.tag[1])
            inline = tokens[i + 1]
            text = inline.content if inline.type == "inline" else ""
            out.append((level, text.strip(), extract_section_id(text)))
        i += 1
    return out


def snapshot(staged_path, doc_name: str, meta_path) -> ReviewState:
    """Record the PRE-edit baseline of the staged render into meta.review."""
    text = Path(staged_path).read_text(encoding="utf-8")
    hashes, order = _section_hashes(text)
    meta = load_meta(meta_path)
    state = ReviewState(
        status="pending",
        baseline_hashes=hashes,
        baseline_order=order,
        snapshot_at=now_iso(),
    )
    meta.review[doc_name] = state
    save_meta(meta, meta_path)
    return state


def surface(staged_path, doc_name: str, docs_dir) -> dict:
    """Build the review surface: section list + ID-section diff vs existing doc."""
    staged_text = Path(staged_path).read_text(encoding="utf-8")
    sections = [
        {"level": lvl, "title": title, "id": sid}
        for lvl, title, sid in _list_headings(staged_text)
    ]

    existing = Path(docs_dir) / doc_name
    diff = {"added": [], "removed": [], "modified": []}
    exists = existing.exists()
    staged_h, _ = _section_hashes(staged_text)
    if exists:
        existing_h, _ = _section_hashes(existing.read_text(encoding="utf-8"))
        staged_ids, existing_ids = set(staged_h), set(existing_h)
        diff["added"] = sorted(staged_ids - existing_ids)
        diff["removed"] = sorted(existing_ids - staged_ids)
        diff["modified"] = sorted(
            sid for sid in staged_ids & existing_ids if staged_h[sid] != existing_h[sid]
        )
    else:
        diff["added"] = sorted(staged_h)

    return {
        "doc": doc_name,
        "staged_path": str(staged_path),
        "exists": exists,
        "sections": sections,
        "diff": diff,
    }


def promote(staged_path, doc_name: str, docs_dir, meta_path) -> Path:
    """Atomic-copy staged → docs/<doc>; write PRE-edit baseline; mark approved."""
    docs_dir = Path(docs_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)
    dest = docs_dir / doc_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = Path(staged_path).read_text(encoding="utf-8")

    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, dest)

    meta = load_meta(meta_path)
    state = meta.review.get(doc_name)
    if state is None or not state.baseline_hashes:
        # snapshot was skipped — fall back to the current staged content. This
        # cannot protect un-snapshotted review-time edits, so the loop always
        # calls snapshot() first.
        hashes, order = _section_hashes(content)
        state = ReviewState(
            status="pending",
            baseline_hashes=hashes,
            baseline_order=order,
            snapshot_at=now_iso(),
        )
        meta.review[doc_name] = state

    prev = meta.docs.get(doc_name)
    meta.docs[doc_name] = DocMeta(
        doc_version=prev.doc_version if prev else "1.0",
        last_render=now_iso(),
        section_hashes=dict(state.baseline_hashes),
        section_order=list(state.baseline_order),
        deprecated=[],
    )
    state.status = "approved"
    state.promoted_at = now_iso()
    save_meta(meta, meta_path)
    return dest


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="command", required=True)

    snap_p = sub.add_parser("snapshot")
    snap_p.add_argument("--staged", required=True)
    snap_p.add_argument("--doc-name", required=True)
    snap_p.add_argument("--meta", required=True)

    surf_p = sub.add_parser("surface")
    surf_p.add_argument("--staged", required=True)
    surf_p.add_argument("--doc-name", required=True)
    surf_p.add_argument("--docs-dir", required=True)

    prom_p = sub.add_parser("promote")
    prom_p.add_argument("--staged", required=True)
    prom_p.add_argument("--doc-name", required=True)
    prom_p.add_argument("--docs-dir", required=True)
    prom_p.add_argument("--meta", required=True)

    args = p.parse_args()

    if args.command == "snapshot":
        state = snapshot(args.staged, args.doc_name, args.meta)
        print(
            f"snapshot {args.doc_name}: {len(state.baseline_hashes)} sections (pending)",
            file=sys.stderr,
        )
    elif args.command == "surface":
        payload = surface(args.staged, args.doc_name, args.docs_dir)
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    elif args.command == "promote":
        dest = promote(args.staged, args.doc_name, args.docs_dir, args.meta)
        print(f"promoted {args.doc_name} -> {dest} (approved)", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
