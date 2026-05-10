"""Step 1 of arch sync — generate proposal from codebase Component scan.

Compares Components detected via `parse_codebase_arch.scan_components()` with
Components already documented in `docs/system-architecture.md` (parsed by H3
anchors `### CMP-...`). Emits markdown proposal with `[ ]` checkboxes;
**does NOT modify the existing doc.**

CLI:
    system_architecture_sync_propose.py --codebase-paths "." \
        --existing-doc docs/system-architecture.md \
        --output .tmp/arch-sync-proposal.md
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))

from parse_codebase_arch import ComponentDef, scan_components  # noqa: E402

# Match H3 component anchor: ### CMP-001-name  (or ### CMP-AUTH, ### CMP-001)
_CMP_HEADER = re.compile(r"^###\s+(CMP-[A-Za-z0-9_-]+)\b", re.MULTILINE)


def parse_existing_components(doc_path: Path) -> set[str]:
    """Return set of Component IDs (CMP-NNN) documented in system-architecture.md."""
    if not doc_path.exists():
        return set()
    text = doc_path.read_text(encoding="utf-8")
    return {m.group(1) for m in _CMP_HEADER.finditer(text)}


def diff_components(
    code: list[ComponentDef], doc_ids: set[str]
) -> tuple[list[ComponentDef], list[str]]:
    """Return (to_add, to_deprecate) by component ID."""
    code_ids = {c.id for c in code}
    by_id = {c.id: c for c in code}
    to_add = [by_id[i] for i in sorted(code_ids - doc_ids)]
    to_deprecate = sorted(doc_ids - code_ids)
    return to_add, to_deprecate


def _render_add_block(c: ComponentDef) -> str:
    techs = ", ".join(c.tech) if c.tech else "(none detected)"
    deps = ", ".join(c.depends_on) if c.depends_on else "-"
    src = c.path or c.detection_source
    return (
        f"### [ ] ADD {c.id}\n"
        f"- Name: `{c.name}`\n"
        f"- Kind: {c.kind}\n"
        f"- Source: `{src}` (via {c.detection_source})\n"
        f"- Tech: {techs}\n"
        f"- Depends on: {deps}\n\n"
    )


def _render_deprecate_block(cid: str) -> str:
    return (
        f"### [ ] DEPRECATE {cid}\n"
        f"- Component `{cid}` documented but no match in scanned paths\n"
        f"- Risk: ⚠️ verify before deprecating — may have been renamed/moved\n\n"
    )


def render_proposal(
    code_paths: list[str],
    existing_doc: Path,
    code_components: list[ComponentDef],
    to_add: list[ComponentDef],
    to_deprecate: list[str],
) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    out: list[str] = []
    out.append(f"# Architecture Sync Proposal — {ts}\n\n")
    out.append(f"**Codebase scanned:** {', '.join(code_paths)}\n")
    out.append(f"**Existing doc:** `{existing_doc}`\n")
    out.append(f"**Detected components in code:** {len(code_components)}\n")
    out.append("**Status:** REVIEW REQUIRED — no doc changes yet\n\n---\n\n")

    out.append(f"## ADD candidates ({len(to_add)})\n\n")
    if not to_add:
        out.append("_None._\n\n")
    else:
        for c in to_add:
            out.append(_render_add_block(c))
    out.append("---\n\n")

    out.append(f"## DEPRECATE candidates ({len(to_deprecate)})\n\n")
    if not to_deprecate:
        out.append("_None._\n\n")
    else:
        for cid in to_deprecate:
            out.append(_render_deprecate_block(cid))
    out.append("---\n\n")

    out.append(
        "## How to apply\n\n"
        "1. Edit checkboxes above (`[x]` = apply, `[ ]` = skip)\n"
        "2. Save this file\n"
        "3. Run: `python system_architecture_sync_apply.py --proposal {this-file} "
        "--output .tmp/arch-delta.json`\n"
    )
    return "".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--codebase-paths", required=True, help="Comma-separated")
    p.add_argument("--existing-doc", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    paths = [s.strip() for s in args.codebase_paths.split(",") if s.strip()]
    code_components = scan_components(paths)
    doc_ids = parse_existing_components(Path(args.existing_doc))

    to_add, to_deprecate = diff_components(code_components, doc_ids)

    text = render_proposal(
        paths, Path(args.existing_doc), code_components, to_add, to_deprecate
    )
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")

    print(
        f"Proposal: {len(to_add)} ADD / {len(to_deprecate)} DEPRECATE -> {args.output}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
