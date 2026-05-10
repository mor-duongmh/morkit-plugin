"""Generate a Mermaid `erDiagram` block from tables + relationships.

Importable: `generate_erd(tables, relationships) -> str`
CLI: read ProjectModel JSON, write Mermaid to file or stdout.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))

from lib.normalized_schema import (  # noqa: E402
    Relationship,
    Table,
    load_project_model,
)


_CARDINALITY = {
    "1:1": "||--||",
    "1:N": "||--o{",
    "N:1": "}o--||",
    "N:N": "}o--o{",
    "1:0..1": "||--o|",
}

_TYPE_MAP = {
    "VARCHAR": "varchar",
    "CHAR": "char",
    "TEXT": "text",
    "INT": "int",
    "INTEGER": "int",
    "SMALLINT": "smallint",
    "BIGINT": "bigint",
    "DECIMAL": "decimal",
    "NUMERIC": "decimal",
    "FLOAT": "float",
    "REAL": "float",
    "DOUBLE": "double",
    "BOOLEAN": "boolean",
    "BOOL": "boolean",
    "TIMESTAMP": "timestamp",
    "TIMESTAMPTZ": "timestamp",
    "DATETIME": "datetime",
    "DATE": "date",
    "TIME": "time",
    "UUID": "uuid",
    "JSON": "json",
    "JSONB": "json",
    "BYTEA": "bytea",
    "BLOB": "blob",
}


def mermaid_cardinality(rel_type: str) -> str:
    return _CARDINALITY.get(rel_type, "||--o{")


def mermaid_type(sql_type: str) -> str:
    """Normalize an SQL type for Mermaid rendering."""
    if not sql_type:
        return "string"
    base = sql_type.split("(")[0].strip().upper()
    return _TYPE_MAP.get(base, base.lower() or "string")


def _safe_table_name(name: str) -> str:
    """Mermaid identifiers allow alphanumerics + underscore. Strip the rest."""
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name).upper()


def generate_erd(tables: list[Table], relationships: list[Relationship]) -> str:
    """Build a Mermaid `erDiagram` markdown block."""
    lines: list[str] = ["```mermaid", "erDiagram"]

    for rel in relationships:
        card = mermaid_cardinality(rel.type)
        parent = _safe_table_name(rel.parent_table)
        child = _safe_table_name(rel.child_table)
        label = (rel.label or rel.parent_table).replace('"', "'")
        lines.append(f'    {parent} {card} {child} : "{label}"')

    if relationships and tables:
        lines.append("")

    for table in tables:
        tname = _safe_table_name(table.name)
        lines.append(f"    {tname} {{")
        for col in table.columns:
            mtype = mermaid_type(col.type)
            keys: list[str] = []
            if col.is_pk:
                keys.append("PK")
            if col.is_fk:
                keys.append("FK")
            if col.is_unique and not col.is_pk:
                keys.append("UK")
            key_marker = (" " + " ".join(keys)) if keys else ""
            comment = (col.constraint or col.description or "").replace('"', "'")
            comment_str = f' "{comment}"' if comment else ""
            lines.append(f"        {mtype} {col.name}{key_marker}{comment_str}")
        lines.append("    }")
        lines.append("")

    lines.append("```")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--project-model", required=True)
    p.add_argument("--output", help="Optional output path; stdout if omitted")
    args = p.parse_args()

    model = load_project_model(args.project_model)
    text = generate_erd(model.database.tables, model.database.relationships)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
        print(f"ERD written -> {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
