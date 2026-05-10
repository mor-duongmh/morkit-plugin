"""Scan a codebase for ORM models / DB schema definitions.

Supported (regex-based, conservative):
    Prisma            — schema.prisma model blocks
    TypeORM           — @Entity() + @Column() / @PrimaryColumn() / @ManyToOne()
    Sequelize         — sequelize.define('Name', { ... })
    Django            — class X(models.Model) + field types
    SQLAlchemy        — class X(Base) + Column(...) / relationship(...)
    GORM (Go)         — struct fields with `gorm:"..."` tags
    Raw SQL           — CREATE TABLE in .sql migration files

Output: list of TableDef dicts saved as JSON.

CLI:
    parse-codebase-models.py --paths "prisma/,src/models" --output models.json

Public API:
    scan_models(paths, ignore=None) -> list[dict]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

_DEFAULT_IGNORES = {".git", "node_modules", "dist", "build", ".next", ".venv", "__pycache__", "vendor"}


@dataclass
class ColumnDef:
    name: str
    type: str
    is_pk: bool = False
    is_fk: bool = False
    is_unique: bool = False
    nullable: bool = True
    default: str | None = None
    references: str | None = None


@dataclass
class TableDef:
    name: str
    columns: list[ColumnDef] = field(default_factory=list)
    framework: str = "unknown"
    file: str = ""
    line: int = 0
    notes: str = ""


# --- Helpers ---


def _camel_to_snake(name: str) -> str:
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return s


def _pluralize(name: str) -> str:
    """Naive pluralizer (matches typical ORM defaults)."""
    if name.endswith("y") and not name.endswith(("ay", "ey", "iy", "oy", "uy")):
        return name[:-1] + "ies"
    if name.endswith(("s", "x", "z", "ch", "sh")):
        return name + "es"
    return name + "s"


# --- Prisma ---

_PRISMA_MODEL = re.compile(r"^model\s+(\w+)\s*\{([^}]*)\}", re.MULTILINE | re.DOTALL)
_PRISMA_FIELD = re.compile(
    r"^\s*(\w+)\s+([\w\[\]?]+)([^\n]*)$", re.MULTILINE
)


def _parse_prisma(content: str, file_path: Path) -> list[TableDef]:
    tables: list[TableDef] = []
    for m in _PRISMA_MODEL.finditer(content):
        name = m.group(1)
        body = m.group(2)
        line_no = content.count("\n", 0, m.start()) + 1
        cols: list[ColumnDef] = []
        for fm in _PRISMA_FIELD.finditer(body):
            field_name = fm.group(1)
            field_type = fm.group(2)
            attrs = fm.group(3)
            # Skip relations (referenced by another field)
            if field_type.endswith("[]") and "@relation" not in attrs:
                continue
            nullable = field_type.endswith("?")
            base_type = field_type.rstrip("?[]")
            is_pk = "@id" in attrs
            is_unique = "@unique" in attrs
            default_match = re.search(r"@default\(([^)]+)\)", attrs)
            ref_match = re.search(r"@relation\(fields:\s*\[(\w+)\],\s*references:\s*\[(\w+)\]", attrs)
            cols.append(
                ColumnDef(
                    name=_camel_to_snake(field_name),
                    type=base_type.upper(),
                    is_pk=is_pk,
                    is_unique=is_unique,
                    nullable=nullable,
                    default=default_match.group(1) if default_match else None,
                    references=(
                        f"{ref_match.group(1)}.{ref_match.group(2)}" if ref_match else None
                    ),
                )
            )
        tables.append(
            TableDef(
                name=_pluralize(_camel_to_snake(name)),
                columns=cols,
                framework="prisma",
                file=str(file_path),
                line=line_no,
            )
        )
    return tables


# --- TypeORM ---

_TYPEORM_ENTITY = re.compile(r"@Entity\s*\(\s*(?:['\"`](\w+)['\"`]\s*)?(?:,\s*\{[^}]*\})?\s*\)\s*\n[^\n]*class\s+(\w+)")
_TYPEORM_COLUMN = re.compile(
    r"@(PrimaryGeneratedColumn|PrimaryColumn|Column)\s*\(([^)]*)\)\s*\n\s*(\w+)\s*[!?:]+\s*(\w+)"
)


def _parse_typeorm(content: str, file_path: Path) -> list[TableDef]:
    tables: list[TableDef] = []
    for em in _TYPEORM_ENTITY.finditer(content):
        explicit_name = em.group(1)
        class_name = em.group(2)
        table_name = explicit_name or _pluralize(_camel_to_snake(class_name))
        line_no = content.count("\n", 0, em.start()) + 1

        # Collect columns appearing after this @Entity until next class / EOF
        end_idx = content.find("class ", em.end() + 1)
        if end_idx == -1:
            end_idx = len(content)
        body = content[em.start():end_idx]
        cols: list[ColumnDef] = []
        for cm in _TYPEORM_COLUMN.finditer(body):
            decorator = cm.group(1)
            options = cm.group(2)
            col_name = cm.group(3)
            ts_type = cm.group(4)
            is_pk = decorator.startswith("Primary")
            nullable = "nullable: true" in options or "nullable:true" in options
            is_unique = "unique: true" in options or "unique:true" in options
            cols.append(
                ColumnDef(
                    name=_camel_to_snake(col_name),
                    type=ts_type.upper(),
                    is_pk=is_pk,
                    nullable=nullable,
                    is_unique=is_unique,
                )
            )
        tables.append(
            TableDef(
                name=table_name,
                columns=cols,
                framework="typeorm",
                file=str(file_path),
                line=line_no,
            )
        )
    return tables


# --- Sequelize ---

_SEQUELIZE_DEFINE = re.compile(
    r"sequelize\s*\.\s*define\s*\(\s*['\"`](\w+)['\"`]\s*,\s*\{([^}]*?)\}",
    re.DOTALL,
)
_SEQUELIZE_FIELD = re.compile(
    r"^\s*(\w+)\s*:\s*\{([^}]+)\}", re.MULTILINE | re.DOTALL
)


def _parse_sequelize(content: str, file_path: Path) -> list[TableDef]:
    tables: list[TableDef] = []
    for m in _SEQUELIZE_DEFINE.finditer(content):
        model = m.group(1)
        body = m.group(2)
        line_no = content.count("\n", 0, m.start()) + 1
        cols: list[ColumnDef] = []
        for fm in _SEQUELIZE_FIELD.finditer(body):
            field_name = fm.group(1)
            opts = fm.group(2)
            type_match = re.search(r"type\s*:\s*DataTypes\.(\w+)", opts)
            cols.append(
                ColumnDef(
                    name=_camel_to_snake(field_name),
                    type=(type_match.group(1) if type_match else "STRING").upper(),
                    is_pk="primaryKey: true" in opts,
                    is_unique="unique: true" in opts,
                    nullable="allowNull: true" in opts,
                )
            )
        tables.append(
            TableDef(
                name=_pluralize(_camel_to_snake(model)),
                columns=cols,
                framework="sequelize",
                file=str(file_path),
                line=line_no,
            )
        )
    return tables


# --- Django ---

_DJANGO_MODEL = re.compile(
    r"^class\s+(\w+)\s*\(\s*models\.Model\s*\)\s*:\s*\n((?:\s{4}.*\n)+)",
    re.MULTILINE,
)
_DJANGO_FIELD = re.compile(
    r"^\s+(\w+)\s*=\s*models\.(\w+)\s*\(([^)]*)\)", re.MULTILINE
)


def _parse_django(content: str, file_path: Path) -> list[TableDef]:
    tables: list[TableDef] = []
    for m in _DJANGO_MODEL.finditer(content):
        name = m.group(1)
        body = m.group(2)
        line_no = content.count("\n", 0, m.start()) + 1
        cols: list[ColumnDef] = []
        for fm in _DJANGO_FIELD.finditer(body):
            field_name = fm.group(1)
            field_type = fm.group(2)
            opts = fm.group(3)
            cols.append(
                ColumnDef(
                    name=field_name,
                    type=field_type.upper(),
                    is_pk="primary_key=True" in opts,
                    is_unique="unique=True" in opts,
                    nullable="null=True" in opts,
                )
            )
        tables.append(
            TableDef(
                name=_pluralize(_camel_to_snake(name)),
                columns=cols,
                framework="django",
                file=str(file_path),
                line=line_no,
            )
        )
    return tables


# --- SQLAlchemy ---

_SQLALCHEMY_CLASS = re.compile(
    r"^class\s+(\w+)\s*\(\s*Base\s*\)\s*:\s*\n((?:\s{4}.*\n)+)",
    re.MULTILINE,
)
_SQLALCHEMY_TABLENAME = re.compile(r"^\s+__tablename__\s*=\s*['\"](\w+)['\"]", re.MULTILINE)
_SQLALCHEMY_FIELD = re.compile(
    r"^\s+(\w+)\s*=\s*Column\s*\(\s*(\w+)([^)]*)\)", re.MULTILINE
)


def _parse_sqlalchemy(content: str, file_path: Path) -> list[TableDef]:
    tables: list[TableDef] = []
    for m in _SQLALCHEMY_CLASS.finditer(content):
        class_name = m.group(1)
        body = m.group(2)
        line_no = content.count("\n", 0, m.start()) + 1
        tn_match = _SQLALCHEMY_TABLENAME.search(body)
        table_name = tn_match.group(1) if tn_match else _pluralize(_camel_to_snake(class_name))
        cols: list[ColumnDef] = []
        for fm in _SQLALCHEMY_FIELD.finditer(body):
            field_name = fm.group(1)
            sa_type = fm.group(2)
            opts = fm.group(3)
            cols.append(
                ColumnDef(
                    name=field_name,
                    type=sa_type.upper(),
                    is_pk="primary_key=True" in opts,
                    is_unique="unique=True" in opts,
                    nullable="nullable=False" not in opts,
                )
            )
        tables.append(
            TableDef(
                name=table_name,
                columns=cols,
                framework="sqlalchemy",
                file=str(file_path),
                line=line_no,
            )
        )
    return tables


# --- GORM ---

_GORM_STRUCT = re.compile(r"type\s+(\w+)\s+struct\s*\{([^}]*)\}", re.DOTALL)
_GORM_FIELD = re.compile(
    r"^\s*(\w+)\s+([\w\.\*]+)(?:\s+`([^`]*)`)?", re.MULTILINE
)


def _parse_gorm(content: str, file_path: Path) -> list[TableDef]:
    tables: list[TableDef] = []
    for m in _GORM_STRUCT.finditer(content):
        if "gorm:" not in m.group(2):
            continue  # Not a GORM model
        struct_name = m.group(1)
        body = m.group(2)
        line_no = content.count("\n", 0, m.start()) + 1
        cols: list[ColumnDef] = []
        for fm in _GORM_FIELD.finditer(body):
            go_name = fm.group(1)
            go_type = fm.group(2)
            tag = fm.group(3) or ""
            if "gorm:" not in tag:
                continue
            gorm_tag = re.search(r"gorm:\"([^\"]*)\"", tag).group(1) if "gorm:" in tag else ""
            cols.append(
                ColumnDef(
                    name=_camel_to_snake(go_name),
                    type=go_type.lstrip("*").upper(),
                    is_pk="primaryKey" in gorm_tag or go_name == "ID",
                    is_unique="unique" in gorm_tag,
                    nullable=go_type.startswith("*"),
                )
            )
        tables.append(
            TableDef(
                name=_pluralize(_camel_to_snake(struct_name)),
                columns=cols,
                framework="gorm",
                file=str(file_path),
                line=line_no,
            )
        )
    return tables


# --- Raw SQL ---

_SQL_CREATE_TABLE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`]?(\w+)[\"`]?\s*\(([^;]+?)\)\s*;",
    re.IGNORECASE | re.DOTALL,
)


def _parse_sql(content: str, file_path: Path) -> list[TableDef]:
    tables: list[TableDef] = []
    for m in _SQL_CREATE_TABLE.finditer(content):
        name = m.group(1)
        body = m.group(2)
        line_no = content.count("\n", 0, m.start()) + 1
        cols: list[ColumnDef] = []
        for line in body.splitlines():
            line = line.strip().rstrip(",").strip()
            if not line or line.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CONSTRAINT", "INDEX")):
                continue
            parts = line.split(None, 2)
            if len(parts) < 2:
                continue
            col_name = parts[0].strip("\"`")
            col_type = parts[1].strip()
            rest = parts[2] if len(parts) > 2 else ""
            cols.append(
                ColumnDef(
                    name=col_name.lower(),
                    type=col_type.upper(),
                    is_pk="PRIMARY KEY" in rest.upper(),
                    is_unique="UNIQUE" in rest.upper(),
                    nullable="NOT NULL" not in rest.upper(),
                )
            )
        tables.append(
            TableDef(
                name=name,
                columns=cols,
                framework="sql",
                file=str(file_path),
                line=line_no,
            )
        )
    return tables


def _scan_file(file_path: Path) -> list[TableDef]:
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    suffix = file_path.suffix.lower()

    if suffix == ".prisma":
        return _parse_prisma(content, file_path)
    if suffix in {".ts", ".tsx", ".js", ".jsx"}:
        results: list[TableDef] = []
        if "@Entity" in content:
            results.extend(_parse_typeorm(content, file_path))
        if "sequelize" in content.lower():
            results.extend(_parse_sequelize(content, file_path))
        return results
    if suffix == ".py":
        results = []
        if "models.Model" in content:
            results.extend(_parse_django(content, file_path))
        if "Base" in content and "Column(" in content:
            results.extend(_parse_sqlalchemy(content, file_path))
        return results
    if suffix == ".go":
        return _parse_gorm(content, file_path)
    if suffix == ".sql":
        return _parse_sql(content, file_path)
    return []


def scan_models(paths: list[str | Path], ignore: set[str] | None = None) -> list[TableDef]:
    """Walk paths recursively, return all detected tables (deduped by name)."""
    ignore = (ignore or set()) | _DEFAULT_IGNORES
    tables: list[TableDef] = []
    seen: set[str] = set()

    valid_exts = {".prisma", ".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".sql"}

    for raw in paths:
        root = Path(raw)
        if not root.exists():
            log.warning("path not found: %s", root)
            continue
        if root.is_file():
            files = [root]
        else:
            files = []
            for f in root.rglob("*"):
                if not f.is_file():
                    continue
                if any(part in ignore for part in f.parts):
                    continue
                if f.suffix.lower() in valid_exts:
                    files.append(f)
        for file_path in files:
            for tbl in _scan_file(file_path):
                if tbl.name in seen:
                    continue
                seen.add(tbl.name)
                tables.append(tbl)
    return tables


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--paths", required=True, help="Comma-separated paths")
    p.add_argument("--output", required=True)
    args = p.parse_args()

    paths = [s.strip() for s in args.paths.split(",") if s.strip()]
    tables = scan_models(paths)
    Path(args.output).write_text(
        json.dumps([asdict(t) for t in tables], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        f"Found {len(tables)} tables across {len(paths)} paths -> {args.output}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
