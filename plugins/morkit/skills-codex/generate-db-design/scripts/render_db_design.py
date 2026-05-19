"""Render database-design.md from a ProjectModel JSON.

Generates `docs/database-design.md` with embedded Mermaid ERD plus per-table /
per-index / per-relationship / per-enum H3 anchors so the diff engine can patch
sections individually.

CLI:
    render_db_design.py --project-model {path}.json --language EN --output docs/database-design.md
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))
sys.path.insert(0, str(_THIS_DIR))

from generate_mermaid_erd import generate_erd  # noqa: E402
from lib.language_pack import Language, t  # noqa: E402
from lib.normalized_schema import (  # noqa: E402
    Database,
    Enum_,
    Index,
    ProjectModel,
    Relationship,
    Table,
    load_project_model,
)


def _heading(level: int, text: str) -> str:
    return f"{'#' * level} {text}\n\n"


# --- Renderers ---


def _render_meta(model: ProjectModel, lang: Language) -> str:
    db = model.database
    today = date.today().isoformat()
    title = "データベース設計書" if lang == Language.JP else (
        "Database Design" if lang == Language.EN else "Thiết kế cơ sở dữ liệu"
    )
    return (
        f"# {title} — {model.meta.project_name}\n\n"
        f"| Field | Value |\n|---|---|\n"
        f"| Project | {model.meta.project_name} |\n"
        f"| Engine | {db.engine} |\n"
        f"| Date | {today} |\n"
        f"| Language | {lang.value} |\n\n"
    )


def _render_overview(db: Database, lang: Language) -> str:
    out = _heading(2, f"1. {t('overview', lang)}")
    out += (db.overview or "_TBD_") + "\n\n"
    out += (
        "**Conventions:**\n"
        "- Snake_case table + column names\n"
        "- Plural table names (`users`, not `user`)\n"
        "- Surrogate `id` PK (UUID v4 unless noted)\n"
        "- Timestamps: `created_at`, `updated_at` (timestamptz UTC)\n"
        "- Soft delete via `deleted_at` when applicable\n\n"
    )
    return out


def _render_erd(db: Database, lang: Language) -> str:
    if not db.tables:
        return ""
    erd = generate_erd(db.tables, db.relationships)
    out = _heading(2, f"2. {t('erd', lang)}")
    out += "<!-- ERD-START -->\n"
    out += erd + "\n"
    out += "<!-- ERD-END -->\n\n"
    return out


def _render_tables(tables: list[Table], lang: Language) -> str:
    if not tables:
        return ""
    out = _heading(2, f"3. {t('tables', lang)}")
    # Index summary
    out += "| ID | Name | Purpose | Related FR |\n|---|---|---|---|\n"
    for tbl in tables:
        related = ", ".join(tbl.related_fr) or "-"
        out += f"| {tbl.id} | `{tbl.name}` | {tbl.purpose or '-'} | {related} |\n"
    out += "\n"
    # Per-table H3 sections
    for tbl in tables:
        out += _heading(3, f"{tbl.id}: {tbl.name}")
        if tbl.purpose:
            out += f"- **Purpose:** {tbl.purpose}\n"
        if tbl.related_fr:
            out += f"- **Related FR:** {', '.join(tbl.related_fr)}\n"
        if tbl.related_data:
            out += f"- **Related DATA (SRS):** {', '.join(tbl.related_data)}\n"
        out += "\n"

        if tbl.columns:
            out += (
                "| # | Column | Type | PK | FK | Null | Default | Constraint | Description |\n"
                "|---|---|---|---|---|---|---|---|---|\n"
            )
            for i, col in enumerate(tbl.columns, 1):
                pk = "Y" if col.is_pk else "-"
                fk = col.references or ("Y" if col.is_fk else "-")
                nullable = "Y" if col.nullable else "N"
                out += (
                    f"| {i} | `{col.name}` | {col.type} | {pk} | {fk} | "
                    f"{nullable} | {col.default or '-'} | {col.constraint or '-'} | "
                    f"{col.description or '-'} |\n"
                )
            out += "\n"
    return out


def _render_indexes(indexes: list[Index], lang: Language) -> str:
    if not indexes:
        return ""
    out = _heading(2, f"4. {t('indexes', lang)}")
    out += "| ID | Table | Columns | Type | Unique | Purpose |\n|---|---|---|---|---|---|\n"
    for idx in indexes:
        unique = "Y" if idx.unique else "N"
        cols = ", ".join(idx.columns)
        out += f"| {idx.id} | `{idx.table}` | {cols} | {idx.type} | {unique} | {idx.purpose or '-'} |\n"
    out += "\n"
    for idx in indexes:
        out += _heading(3, f"{idx.id}: {idx.table}({', '.join(idx.columns)})")
        out += f"- **Type:** {idx.type}\n"
        out += f"- **Unique:** {'Y' if idx.unique else 'N'}\n"
        if idx.where_clause:
            out += f"- **Partial:** `WHERE {idx.where_clause}`\n"
        if idx.purpose:
            out += f"- **Purpose:** {idx.purpose}\n"
        out += "\n"
    return out


def _render_relationships(rels: list[Relationship], lang: Language) -> str:
    if not rels:
        return ""
    out = _heading(2, f"5. {t('relationships', lang)}")
    out += "| ID | Parent | Child | Type | On Delete | On Update | Label |\n"
    out += "|---|---|---|---|---|---|---|\n"
    for r in rels:
        out += (
            f"| {r.id} | `{r.parent_table}` | `{r.child_table}` | {r.type} | "
            f"{r.on_delete} | {r.on_update} | {r.label or '-'} |\n"
        )
    out += "\n"
    for r in rels:
        out += _heading(3, f"{r.id}: {r.parent_table} → {r.child_table}")
        out += f"- **Type:** {r.type}\n"
        out += f"- **On Delete:** {r.on_delete}\n"
        out += f"- **On Update:** {r.on_update}\n"
        if r.label:
            out += f"- **Label:** {r.label}\n"
        out += "\n"
    return out


def _render_enums(enums: list[Enum_], lang: Language) -> str:
    if not enums:
        return ""
    out = _heading(2, f"6. {t('enums', lang)}")
    for e in enums:
        out += _heading(3, f"{e.id}: {e.name}")
        if e.values:
            out += "| Value | Meaning |\n|---|---|\n"
            for v in e.values:
                out += f"| `{v.value}` | {v.meaning or '-'} |\n"
            out += "\n"
    return out


def _render_revision_history() -> str:
    return (
        "## Revision History\n\n"
        "| Version | Date | Author | Changes |\n"
        "|---|---|---|---|\n"
        f"| 1.0 | {date.today().isoformat()} | docs-hero (auto) | Initial generation |\n"
    )


def render_db_design(model: ProjectModel, lang: Language) -> str:
    db = model.database
    parts = [
        _render_meta(model, lang),
        _render_overview(db, lang),
        _render_erd(db, lang),
        _render_tables(db.tables, lang),
        _render_indexes(db.indexes, lang),
        _render_relationships(db.relationships, lang),
        _render_enums(db.enums, lang),
        _render_revision_history(),
    ]
    return "".join(parts)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--project-model", required=True)
    p.add_argument("--language", default="EN", choices=["JP", "EN", "VN"])
    p.add_argument("--output", required=True)
    args = p.parse_args()

    model = load_project_model(args.project_model)
    text = render_db_design(model, Language(args.language))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Rendered DB design -> {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
