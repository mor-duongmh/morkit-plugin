"""Step 1 of codebase-summary sync — generate proposal from tree scan.

Compares packages + tech-stack items + entry-point modules detected by
`parse_codebase_tree.scan_tree()` with what's already documented in
`docs/codebase-summary.md` (parsed by `PKG-...` / `TCH-...` / `MOD-...` refs).
Emits markdown proposal with `[ ]` checkboxes; **does NOT modify the doc.**

CLI:
    codebase_summary_sync_propose.py --codebase-paths "." \
        --existing-doc docs/codebase-summary.md \
        --output .tmp/codebase-summary-sync-proposal.md
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))

from parse_codebase_tree import (  # noqa: E402
    ModuleEntryDef,
    PackageInfoDef,
    TechStackItemDef,
    scan_tree,
)

_REF_PATTERNS = {
    "PKG": re.compile(r"\bPKG-[A-Za-z0-9_-]+\b"),
    "TCH": re.compile(r"\bTCH-[A-Za-z0-9_-]+\b"),
    "MOD": re.compile(r"\bMOD-[A-Za-z0-9_-]+\b"),
}


def parse_existing_ids(doc_path: Path) -> dict[str, set[str]]:
    """Return {kind: {id, ...}} for PKG / TCH / MOD references in the doc."""
    out: dict[str, set[str]] = {k: set() for k in _REF_PATTERNS}
    if not doc_path.exists():
        return out
    text = doc_path.read_text(encoding="utf-8")
    for kind, pat in _REF_PATTERNS.items():
        out[kind] = set(pat.findall(text))
    return out


def diff_simple_ids(
    code_ids: set[str], doc_ids: set[str]
) -> tuple[list[str], list[str]]:
    return sorted(code_ids - doc_ids), sorted(doc_ids - code_ids)


def _render_pkg_block(p: PackageInfoDef, op: str = "ADD") -> str:
    return (
        f"### [ ] {op} {p.id}\n"
        f"- Name: `{p.name}`\n"
        f"- Path: `{p.path}`\n"
        f"- Manager: {p.manager}\n"
        f"- Version: {p.version or '-'}\n"
        f"- Deps: {p.dep_count}\n\n"
    )


def _render_tch_block(t: TechStackItemDef, op: str = "ADD") -> str:
    return (
        f"### [ ] {op} {t.id}\n"
        f"- Name: `{t.name}`\n"
        f"- Category: {t.category}\n"
        f"- Confidence: {t.confidence}\n\n"
    )


def _render_mod_block(m: ModuleEntryDef, op: str = "ADD") -> str:
    return (
        f"### [ ] {op} {m.id}\n"
        f"- Path: `{m.path}`\n"
        f"- Language: {m.language or '-'}\n"
        f"- LOC: {m.loc}\n"
        f"- Entry point: {m.is_entry_point}\n\n"
    )


def _render_deprecate(kind: str, ident: str) -> str:
    return (
        f"### [ ] DEPRECATE {ident}\n"
        f"- {kind} `{ident}` documented but no match in scanned paths\n"
        f"- Risk: ⚠️ verify before deprecating — may have moved/renamed\n\n"
    )


def render_proposal(
    code_paths: list[str],
    existing_doc: Path,
    pkgs_add: list[PackageInfoDef],
    pkgs_dep: list[str],
    tech_add: list[TechStackItemDef],
    tech_dep: list[str],
    mods_add: list[ModuleEntryDef],
    mods_dep: list[str],
) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    out: list[str] = []
    out.append(f"# Codebase Summary Sync Proposal — {ts}\n\n")
    out.append(f"**Codebase scanned:** {', '.join(code_paths)}\n")
    out.append(f"**Existing doc:** `{existing_doc}`\n")
    out.append(
        f"**Detected:** {len(pkgs_add) + len(pkgs_dep)} packages, "
        f"{len(tech_add) + len(tech_dep)} tech items, "
        f"{len(mods_add) + len(mods_dep)} entry points\n"
    )
    out.append("**Status:** REVIEW REQUIRED — no doc changes yet\n\n---\n\n")

    out.append(f"## Packages — ADD ({len(pkgs_add)})\n\n")
    for p in pkgs_add:
        out.append(_render_pkg_block(p))
    out.append(f"## Packages — DEPRECATE ({len(pkgs_dep)})\n\n")
    for pid in pkgs_dep:
        out.append(_render_deprecate("Package", pid))
    out.append("---\n\n")

    out.append(f"## Tech Stack — ADD ({len(tech_add)})\n\n")
    for t in tech_add:
        out.append(_render_tch_block(t))
    out.append(f"## Tech Stack — DEPRECATE ({len(tech_dep)})\n\n")
    for tid in tech_dep:
        out.append(_render_deprecate("TechStack", tid))
    out.append("---\n\n")

    out.append(f"## Entry Points — ADD ({len(mods_add)})\n\n")
    for m in mods_add:
        out.append(_render_mod_block(m))
    out.append(f"## Entry Points — DEPRECATE ({len(mods_dep)})\n\n")
    for mid in mods_dep:
        out.append(_render_deprecate("Entry point", mid))
    out.append("---\n\n")

    out.append(
        "## How to apply\n\n"
        "1. Edit checkboxes above (`[x]` = apply, `[ ]` = skip)\n"
        "2. Save this file\n"
        "3. Run: `python codebase_summary_sync_apply.py "
        "--proposal {this-file} --output .tmp/codebase-summary-delta.json`\n"
    )
    return "".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--codebase-paths", required=True, help="Comma-separated")
    p.add_argument("--existing-doc", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    paths = [s.strip() for s in args.codebase_paths.split(",") if s.strip()]
    res = scan_tree(paths)

    code_pkg_ids = {p.id for p in res.packages}
    code_tch_ids = {t.id for t in res.tech_stack}
    # Only entry-point modules participate in sync (the full list is too large)
    entry_modules = [m for m in res.modules if m.is_entry_point]
    code_mod_ids = {m.id for m in entry_modules}

    doc_ids = parse_existing_ids(Path(args.existing_doc))
    pkg_add, pkg_dep = diff_simple_ids(code_pkg_ids, doc_ids["PKG"])
    tch_add, tch_dep = diff_simple_ids(code_tch_ids, doc_ids["TCH"])
    mod_add, mod_dep = diff_simple_ids(code_mod_ids, doc_ids["MOD"])

    pkgs_by_id = {p.id: p for p in res.packages}
    tch_by_id = {t.id: t for t in res.tech_stack}
    mods_by_id = {m.id: m for m in entry_modules}

    text = render_proposal(
        paths,
        Path(args.existing_doc),
        [pkgs_by_id[i] for i in pkg_add],
        pkg_dep,
        [tch_by_id[i] for i in tch_add],
        tch_dep,
        [mods_by_id[i] for i in mod_add],
        mod_dep,
    )
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")

    print(
        f"Proposal: {len(pkg_add) + len(tch_add) + len(mod_add)} ADD / "
        f"{len(pkg_dep) + len(tch_dep) + len(mod_dep)} DEPRECATE -> {args.output}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
