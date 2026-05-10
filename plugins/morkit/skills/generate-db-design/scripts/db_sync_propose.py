"""Step 1 of DB sync — generate human-readable proposal from ORM model scan.

Compares tables detected via `parse_codebase_models.scan_models()` with tables
already documented in `docs/database-design.md` (parsed by H3 anchors `### TBL-...`).
Emits a markdown proposal with `[ ]` checkboxes; **does NOT modify the existing doc.**

CLI:
    db_sync_propose.py --codebase-paths "src/models,src/entities" \
        --existing-doc docs/database-design.md \
        --output .tmp/db-sync-proposal.md
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))

from parse_codebase_models import TableDef, scan_models  # noqa: E402

# Match H3 table anchor: ### TBL-001-users: name  (or ### TBL-USERS, ### TBL-001)
_TABLE_HEADER = re.compile(r"^###\s+(TBL-[A-Za-z0-9_-]+)\b", re.MULTILINE)
# Capture documented table NAME from H3 line "### TBL-xxx: <name>"
_TABLE_NAME = re.compile(
    r"^###\s+TBL-[A-Za-z0-9_-]+\s*:\s*(?P<name>[A-Za-z0-9_]+)\s*$",
    re.MULTILINE,
)


def parse_existing_tables(doc_path: Path) -> set[str]:
    """Return set of table NAMES (snake_case) documented in database-design.md."""
    if not doc_path.exists():
        return set()
    text = doc_path.read_text(encoding="utf-8")
    names: set[str] = set()
    for m in _TABLE_NAME.finditer(text):
        names.add(m.group("name").lower())
    # Also accept anchors without a name suffix; in that case skip — name unknown
    return names


def diff_tables(
    code_tables: list[TableDef], doc_names: set[str]
) -> tuple[list[TableDef], list[str]]:
    """Return (to_add, to_deprecate) — by table name."""
    code_names = {t.name.lower() for t in code_tables}
    by_name = {t.name.lower(): t for t in code_tables}

    add_names = code_names - doc_names
    deprecate_names = doc_names - code_names

    to_add = [by_name[n] for n in sorted(add_names)]
    to_deprecate = sorted(deprecate_names)
    return to_add, to_deprecate


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _render_add_block(t: TableDef) -> str:
    sec_id = f"TBL-{_slug(t.name)}"
    cols = ", ".join(c.name for c in t.columns[:8])
    if len(t.columns) > 8:
        cols += f", … ({len(t.columns)} total)"
    return (
        f"### [ ] ADD {sec_id}\n"
        f"- Table: `{t.name}`\n"
        f"- Source: `{t.file}:{t.line}` ({t.framework})\n"
        f"- Columns: {cols or 'none detected'}\n\n"
    )


def _render_deprecate_block(name: str) -> str:
    sec_id = f"TBL-{_slug(name)}"
    return (
        f"### [ ] DEPRECATE {sec_id}\n"
        f"- Table `{name}` documented but no model found in scanned paths\n"
        f"- Risk: ⚠️ verify before deprecating — may have been renamed/moved\n\n"
    )


def render_proposal(
    code_paths: list[str],
    existing_doc: Path,
    code_tables: list[TableDef],
    to_add: list[TableDef],
    to_deprecate: list[str],
) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    out: list[str] = []
    out.append(f"# DB Sync Proposal — {ts}\n\n")
    out.append(f"**Codebase scanned:** {', '.join(code_paths)}\n")
    out.append(f"**Existing doc:** `{existing_doc}`\n")
    out.append(f"**Detected tables in code:** {len(code_tables)}\n")
    out.append("**Status:** REVIEW REQUIRED — no doc changes yet\n\n---\n\n")

    out.append(f"## ADD candidates ({len(to_add)})\n\n")
    if not to_add:
        out.append("_None._\n\n")
    else:
        for t in to_add:
            out.append(_render_add_block(t))
    out.append("---\n\n")

    out.append(f"## DEPRECATE candidates ({len(to_deprecate)})\n\n")
    if not to_deprecate:
        out.append("_None._\n\n")
    else:
        for name in to_deprecate:
            out.append(_render_deprecate_block(name))
    out.append("---\n\n")

    out.append(
        "## How to apply\n\n"
        "1. Edit checkboxes above (`[x]` = apply, `[ ]` = skip)\n"
        "2. Save this file\n"
        "3. Run: `python db_sync_apply.py --proposal {this-file} --output .tmp/db-delta.json`\n"
    )
    return "".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--codebase-paths", required=True, help="Comma-separated")
    p.add_argument("--existing-doc", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    paths = [s.strip() for s in args.codebase_paths.split(",") if s.strip()]
    code_tables = scan_models(paths)
    doc_names = parse_existing_tables(Path(args.existing_doc))

    to_add, to_deprecate = diff_tables(code_tables, doc_names)

    text = render_proposal(paths, Path(args.existing_doc), code_tables, to_add, to_deprecate)
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
