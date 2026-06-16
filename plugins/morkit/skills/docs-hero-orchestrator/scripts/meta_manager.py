"""Manage `.docs-hero-meta.json` sidecar across docs/.

Operations:
    rebuild  — Walk docs_dir, parse each .md, compute hashes, write meta.
    verify   — Compare current doc hashes vs meta; report drift.
    summary  — Print stats.
    reset    — Reset entry for one doc.

Public API:
    rebuild_meta(docs_dir, meta_path) -> MetaSidecar
    verify_meta(docs_dir, meta_path) -> dict
    reset_doc(meta, doc_path) -> MetaSidecar
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.canonicalize import compute_hash  # noqa: E402
from lib.diff_schema import DocMeta, MetaSidecar, now_iso, save_meta  # noqa: E402
from lib.markdown_ast import parse_doc  # noqa: E402

# Detect doc version from a revision history row like:
# | 1.1 | 2026-05-03 | docs-hero | Added FR-008 |
_VERSION_ROW = re.compile(r"^\|\s*(\d+\.\d+(?:\.\d+)?)\s*\|", re.MULTILINE)


def _build_doc_meta(md_path: Path) -> DocMeta:
    text = md_path.read_text(encoding="utf-8")
    blocks = parse_doc(text)
    section_hashes: dict[str, str] = {}
    section_order: list[str] = []

    # Sort by line_start so order matches doc layout
    for sid, block in sorted(blocks.items(), key=lambda kv: kv[1].line_start):
        section_hashes[sid] = compute_hash(block.body_md)
        section_order.append(sid)

    # Detect doc version (latest row in revision history)
    version_match = _VERSION_ROW.findall(text)
    # The last matched version cell is typically the latest revision
    doc_version = version_match[-1] if version_match else "1.0"

    return DocMeta(
        doc_version=doc_version,
        last_render=now_iso(),
        section_hashes=section_hashes,
        section_order=section_order,
        deprecated=[],
    )


def rebuild_meta(docs_dir: str | Path, meta_path: str | Path) -> MetaSidecar:
    """Walk docs/ recursively, build fresh meta from current state."""
    docs_root = Path(docs_dir)
    if not docs_root.exists():
        raise FileNotFoundError(f"docs dir not found: {docs_root}")

    meta = MetaSidecar(generated_at=now_iso())
    for md_file in sorted(docs_root.rglob("*.md")):
        rel_path = str(md_file.relative_to(docs_root))
        meta.docs[rel_path] = _build_doc_meta(md_file)

    save_meta(meta, meta_path)
    return meta


def verify_meta(docs_dir: str | Path, meta_path: str | Path) -> dict:
    """Compare meta vs current docs state, return drift summary."""
    docs_root = Path(docs_dir)
    meta = MetaSidecar(generated_at=now_iso())
    if Path(meta_path).exists():
        from lib.diff_schema import load_meta

        meta = load_meta(meta_path)

    drift: dict[str, dict] = {}
    for rel_path, doc_meta in meta.docs.items():
        md_file = docs_root / rel_path
        if not md_file.exists():
            drift[rel_path] = {"status": "missing"}
            continue
        current_meta = _build_doc_meta(md_file)
        diff_sections = []
        for sid, expected_hash in doc_meta.section_hashes.items():
            current_hash = current_meta.section_hashes.get(sid)
            if current_hash is None:
                diff_sections.append({"section_id": sid, "status": "deleted"})
            elif current_hash != expected_hash:
                diff_sections.append({"section_id": sid, "status": "modified"})
        for sid in current_meta.section_hashes:
            if sid not in doc_meta.section_hashes:
                diff_sections.append({"section_id": sid, "status": "added"})
        if diff_sections:
            drift[rel_path] = {"status": "drift", "sections": diff_sections}

    return {"docs_with_drift": len(drift), "details": drift}


def reset_doc(meta: MetaSidecar, doc_relpath: str) -> MetaSidecar:
    """Remove a doc entry (forces rebuild on next run)."""
    meta.docs.pop(doc_relpath, None)
    return meta


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("operation", choices=["rebuild", "verify", "summary", "reset"])
    p.add_argument("--docs-dir", required=True)
    p.add_argument("--meta", default=None, help="Default: <docs-dir>/.docs-hero-meta.json")
    p.add_argument("--doc", help="For reset: doc path relative to docs-dir")
    args = p.parse_args()

    meta_path = args.meta or str(Path(args.docs_dir) / ".docs-hero-meta.json")

    if args.operation == "rebuild":
        meta = rebuild_meta(args.docs_dir, meta_path)
        total_sections = sum(len(d.section_hashes) for d in meta.docs.values())
        print(
            f"Rebuilt meta for {len(meta.docs)} docs ({total_sections} sections) -> {meta_path}",
            file=sys.stderr,
        )

    elif args.operation == "verify":
        drift = verify_meta(args.docs_dir, meta_path)
        if drift["docs_with_drift"] == 0:
            print("✓ All docs match meta", file=sys.stderr)
        else:
            print(
                f"✗ Drift detected in {drift['docs_with_drift']} docs",
                file=sys.stderr,
            )
            for rel_path, info in drift["details"].items():
                print(f"  - {rel_path}: {info['status']}", file=sys.stderr)
        return 0 if drift["docs_with_drift"] == 0 else 1

    elif args.operation == "summary":
        from lib.diff_schema import load_meta

        meta = load_meta(meta_path)
        for rel_path, doc_meta in meta.docs.items():
            print(
                f"{rel_path} (v{doc_meta.doc_version}, "
                f"{len(doc_meta.section_hashes)} sections)",
                file=sys.stderr,
            )

    elif args.operation == "reset":
        if not args.doc:
            p.error("--doc required for reset")
        from lib.diff_schema import load_meta

        meta = load_meta(meta_path)
        meta = reset_doc(meta, args.doc)
        save_meta(meta, meta_path)
        print(f"Reset {args.doc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
