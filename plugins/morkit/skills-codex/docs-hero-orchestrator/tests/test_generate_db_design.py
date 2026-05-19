"""Tests for generate-db-design sub-skill (render_db_design, ERD, sync)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))

_DB = Path(__file__).resolve().parents[2] / "generate-db-design" / "scripts"
sys.path.insert(0, str(_DB))

from db_sync_apply import parse_proposal  # noqa: E402
from db_sync_propose import (  # noqa: E402
    diff_tables,
    parse_existing_tables,
    render_proposal,
)
from generate_mermaid_erd import (  # noqa: E402
    generate_erd,
    mermaid_cardinality,
    mermaid_type,
)
from lib.normalized_schema import (  # noqa: E402
    Column,
    Database,
    Enum_,
    EnumValue,
    Index,
    Language,
    ProjectMeta,
    ProjectModel,
    Relationship,
    Table,
)
from parse_codebase_models import ColumnDef, TableDef  # noqa: E402
from render_db_design import render_db_design  # noqa: E402


def _build_minimal_db_model() -> ProjectModel:
    return ProjectModel(
        meta=ProjectMeta(project_name="TestDB", version="1.0"),
        database=Database(
            engine="PostgreSQL",
            overview="Test database for unit tests.",
            tables=[
                Table(
                    id="TBL-001",
                    name="users",
                    purpose="Application users",
                    related_fr=["FR-001"],
                    columns=[
                        Column(name="id", type="UUID", is_pk=True, nullable=False),
                        Column(name="email", type="VARCHAR(255)", is_unique=True, nullable=False,
                               constraint="UNIQUE"),
                        Column(name="created_at", type="TIMESTAMPTZ", nullable=False,
                               default="NOW()"),
                    ],
                ),
                Table(
                    id="TBL-002",
                    name="orders",
                    purpose="Customer orders",
                    columns=[
                        Column(name="id", type="UUID", is_pk=True, nullable=False),
                        Column(name="user_id", type="UUID", is_fk=True,
                               references="users.id", nullable=False),
                        Column(name="total", type="DECIMAL(10,2)", nullable=False),
                    ],
                ),
            ],
            indexes=[
                Index(id="IDX-001", table="users", columns=["email"], unique=True,
                      purpose="login lookup"),
            ],
            relationships=[
                Relationship(id="REL-001", parent_table="users", child_table="orders",
                             type="1:N", on_delete="CASCADE", label="places"),
            ],
            enums=[
                Enum_(id="ENUM-order_status", name="order_status",
                      values=[
                          EnumValue(value="pending", meaning="Awaiting payment"),
                          EnumValue(value="paid", meaning="Payment received"),
                      ]),
            ],
        ),
    )


# --- mermaid_type ---


def test_mermaid_type_normalizes_varchar():
    assert mermaid_type("VARCHAR(255)") == "varchar"


def test_mermaid_type_normalizes_jsonb():
    assert mermaid_type("JSONB") == "json"


def test_mermaid_type_unknown_falls_back():
    assert mermaid_type("CITEXT") == "citext"


def test_mermaid_type_empty_returns_string():
    assert mermaid_type("") == "string"


# --- mermaid_cardinality ---


def test_cardinality_one_to_many():
    assert mermaid_cardinality("1:N") == "||--o{"


def test_cardinality_many_to_many():
    assert mermaid_cardinality("N:N") == "}o--o{"


def test_cardinality_unknown_falls_back():
    assert mermaid_cardinality("WAT") == "||--o{"


# --- generate_erd ---


def test_erd_includes_mermaid_block_markers():
    model = _build_minimal_db_model()
    erd = generate_erd(model.database.tables, model.database.relationships)
    assert erd.startswith("```mermaid")
    assert erd.endswith("```")
    assert "erDiagram" in erd


def test_erd_includes_relationship_with_cardinality():
    model = _build_minimal_db_model()
    erd = generate_erd(model.database.tables, model.database.relationships)
    assert "USERS ||--o{ ORDERS" in erd


def test_erd_includes_table_columns_with_pk_marker():
    model = _build_minimal_db_model()
    erd = generate_erd(model.database.tables, model.database.relationships)
    assert "USERS {" in erd
    assert "uuid id PK" in erd
    assert "varchar email" in erd
    assert "uuid user_id" in erd  # FK columns get FK marker
    assert "FK" in erd


def test_erd_handles_no_relationships():
    erd = generate_erd([
        Table(id="TBL-1", name="solo", columns=[Column(name="id", type="UUID", is_pk=True)]),
    ], [])
    assert "SOLO {" in erd
    assert "erDiagram" in erd


# --- render_db_design ---


def test_render_includes_main_sections():
    text = render_db_design(_build_minimal_db_model(), Language.EN)
    assert "Database Design" in text
    assert "TestDB" in text
    assert "PostgreSQL" in text


def test_render_emits_h3_anchors_for_diff_engine():
    text = render_db_design(_build_minimal_db_model(), Language.EN)
    assert "### TBL-001" in text
    assert "### TBL-002" in text
    assert "### IDX-001" in text
    assert "### REL-001" in text
    assert "### ENUM-order_status" in text


def test_render_includes_mermaid_erd_block():
    text = render_db_design(_build_minimal_db_model(), Language.EN)
    assert "```mermaid" in text
    assert "erDiagram" in text
    assert "<!-- ERD-START -->" in text


def test_render_jp_uses_japanese_headings():
    text = render_db_design(_build_minimal_db_model(), Language.JP)
    assert "概要" in text  # overview
    assert "テーブル定義" in text  # tables
    assert "ER図" in text  # ERD


def test_render_vn_uses_vietnamese_headings():
    text = render_db_design(_build_minimal_db_model(), Language.VN)
    assert "Tổng quan" in text
    assert "Bảng dữ liệu" in text


def test_render_table_columns_in_summary_table():
    text = render_db_design(_build_minimal_db_model(), Language.EN)
    assert "`email`" in text
    assert "`user_id`" in text
    assert "users.id" in text  # FK reference


def test_render_index_includes_unique_marker():
    text = render_db_design(_build_minimal_db_model(), Language.EN)
    assert "IDX-001" in text
    assert "login lookup" in text


# --- sync: parse_existing_tables ---


def test_parse_existing_tables_extracts_h3_table_names():
    with tempfile.TemporaryDirectory() as td:
        doc = Path(td) / "database-design.md"
        doc.write_text(
            "# DB\n\n"
            "### TBL-001: users\n\nbody\n\n"
            "### TBL-002: orders\n\nbody\n\n"
            "### IDX-001: users(email)\n",
            encoding="utf-8",
        )
        names = parse_existing_tables(doc)
        assert "users" in names
        assert "orders" in names
        assert len(names) == 2  # IDX not counted as table


def test_parse_existing_tables_missing_returns_empty():
    assert parse_existing_tables(Path("/nonexistent/x.md")) == set()


# --- sync: diff_tables ---


def test_diff_tables_finds_adds_and_deprecates():
    code = [
        TableDef(name="users", columns=[ColumnDef(name="id", type="uuid")], framework="prisma"),
        TableDef(name="posts", columns=[ColumnDef(name="id", type="uuid")], framework="prisma"),
    ]
    doc = {"users", "old_table"}
    to_add, to_deprecate = diff_tables(code, doc)
    add_names = {t.name for t in to_add}
    assert "posts" in add_names
    assert "old_table" in to_deprecate


# --- sync: render_proposal ---


def test_proposal_has_checkbox_per_candidate():
    code = [TableDef(name="posts", columns=[ColumnDef(name="id", type="uuid")],
                     framework="prisma", file="schema.prisma", line=10)]
    md = render_proposal(["src/db"], Path("docs/database-design.md"), code, code, ["legacy"])
    assert "[ ] ADD TBL-posts" in md
    assert "[ ] DEPRECATE TBL-legacy" in md


def test_proposal_includes_summary_counts():
    code = [TableDef(name="x", framework="prisma", file="a", line=1)]
    md = render_proposal(["src"], Path("d.md"), code, code, [])
    assert "ADD candidates (1)" in md
    assert "DEPRECATE candidates (0)" in md


# --- sync: parse_proposal (apply step) ---


def test_apply_extracts_only_checked_items():
    proposal = (
        "# Proposal\n\n"
        "### [x] ADD TBL-users\n"
        "- Table: `users`\n"
        "- Columns: id, email\n\n"
        "### [ ] ADD TBL-posts\n"
        "- Table: `posts`\n\n"
        "### [X] DEPRECATE TBL-legacy\n"
        "- gone from code\n\n"
    )
    changes = parse_proposal(proposal)
    ids = [c.entity_id for c in changes]
    assert "TBL-users" in ids
    assert "TBL-legacy" in ids
    assert "TBL-posts" not in ids


def test_apply_extracts_table_name_payload():
    proposal = (
        "### [x] ADD TBL-users\n"
        "- Table: `users`\n"
        "- Columns: id, email\n\n"
    )
    changes = parse_proposal(proposal)
    assert len(changes) == 1
    assert changes[0].entity_type == "TABLE"
    assert (changes[0].payload or {}).get("name") == "users"


def test_apply_handles_no_checked_items():
    assert parse_proposal("### [ ] ADD TBL-x\n- Table: `x`\n\n") == []


def test_apply_dispatches_entity_type_by_id_prefix():
    proposal = (
        "### [x] ADD IDX-001\n- some index\n\n"
        "### [x] ADD REL-001\n- some rel\n\n"
        "### [x] ADD ENUM-status\n- some enum\n\n"
    )
    changes = parse_proposal(proposal)
    types = {c.entity_id: c.entity_type for c in changes}
    assert types["IDX-001"] == "INDEX"
    assert types["REL-001"] == "REL"
    assert types["ENUM-status"] == "ENUM"
