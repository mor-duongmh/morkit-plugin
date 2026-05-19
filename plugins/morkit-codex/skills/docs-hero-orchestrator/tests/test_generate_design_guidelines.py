"""Tests for generate-design-guidelines sub-skill + parse_codebase_adrs scanner."""
from __future__ import annotations

import sys
from pathlib import Path

_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))

_GUI = Path(__file__).resolve().parents[2] / "generate-design-guidelines" / "scripts"
sys.path.insert(0, str(_GUI))

from lib.normalized_schema import (  # noqa: E402
    ADR,
    DesignPrinciple,
    Language,
    PatternGuideline,
    ProjectMeta,
    ProjectModel,
)
from parse_codebase_adrs import scan_adrs  # noqa: E402
from render_design_guidelines import render_adr_stub, render_design_guidelines  # noqa: E402


def _build_minimal_guidelines_model() -> ProjectModel:
    return ProjectModel(
        meta=ProjectMeta(project_name="TestGui", version="1.0"),
        design_principles=[
            DesignPrinciple(
                id="DPR-001",
                name="Fail fast",
                statement="Surface invalid state at the boundary.",
                rationale="Prevents silent corruption.",
                examples=["validate at API edge"],
            ),
        ],
        pattern_guidelines=[
            PatternGuideline(id="PTN-001", name="Repository", category="domain",
                             when_to_use="aggregate root persistence",
                             when_to_avoid="trivial CRUD"),
        ],
        adrs=[
            ADR(id="ADR-002", title="Use Postgres for OLTP", status="accepted",
                date="2026-05-01", context="multi-tenant", decision="Postgres 15",
                consequences="ops burden"),
            ADR(id="ADR-001", title="Adopt Conventional Commits", status="accepted",
                date="2026-04-15", context="messy log", decision="cc enforced",
                consequences="cleaner log"),
        ],
    )


# --- Renderer ---


def test_render_guidelines_top_sections():
    model = _build_minimal_guidelines_model()
    text = render_design_guidelines(model, Language.EN, "adr")
    assert text.startswith("# Design Guidelines — TestGui")
    for heading in (
        "## 1. Design Principles",
        "## 2. Patterns We Use / Avoid",
        "## 3. Architecture Decision Records (ADRs)",
        "## 4. Anti-patterns",
        "## 5. Review Checklist",
    ):
        assert heading in text, f"missing {heading!r}"
    # Manual-only disclaimer
    assert "manual" in text.lower()
    # Per-principle detail with rationale appears
    assert "Rationale" in text
    # Pattern table
    assert "PTN-001" in text and "Repository" in text


def test_render_guidelines_adrs_sorted_by_id():
    """ADRs should render in ID order (ADR-001 before ADR-002), regardless of input order."""
    model = _build_minimal_guidelines_model()
    text = render_design_guidelines(model, Language.EN, "adr")
    pos_001 = text.find("ADR-001:")
    pos_002 = text.find("ADR-002:")
    assert pos_001 != -1 and pos_002 != -1
    assert pos_001 < pos_002


def test_render_guidelines_empty_model_uses_placeholders():
    pm = ProjectModel(meta=ProjectMeta(project_name="Empty"))
    text = render_design_guidelines(pm, Language.EN, "adr")
    assert "DPR-001" in text  # placeholder row
    assert "PTN-001" in text
    assert "ADR-001" in text


def test_render_guidelines_jp_title():
    model = _build_minimal_guidelines_model()
    text = render_design_guidelines(model, Language.JP, "adr")
    assert text.startswith("# 設計ガイドライン")


def test_render_adr_stub_madr_fields():
    adr = ADR(id="ADR-007", title="Pick A Database",
              status="accepted", date="2026-05-10",
              context="C", decision="D", consequences="X")
    text = render_adr_stub(adr, Language.EN)
    assert text.startswith("# ADR-007: Pick A Database")
    assert "## Context\nC" in text
    assert "## Decision\nD" in text
    assert "## Consequences\nX" in text
    # Sync-warning footer
    assert "design-guidelines.md §3" in text


# --- Scanner ---


def test_scan_adrs_parses_madr_sections(tmp_path):
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0003-pick-postgres.md").write_text(
        "# ADR-003: Pick Postgres\n\n"
        "## Status\naccepted\n\n"
        "## Date\n2026-04-01\n\n"
        "## Context\nmulti-tenant SaaS\n\n"
        "## Decision\nUse Postgres 15\n\n"
        "## Consequences\nMore ops burden\n",
        encoding="utf-8",
    )
    adrs = scan_adrs([str(tmp_path)])
    assert len(adrs) == 1
    a = adrs[0]
    assert a.id == "ADR-003"
    assert a.title == "Pick Postgres"
    assert a.status == "accepted"
    assert a.date == "2026-04-01"
    assert "multi-tenant" in a.context
    assert "Postgres 15" in a.decision
    assert "ops burden" in a.consequences


def test_scan_adrs_parses_inline_status(tmp_path):
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-use-something.md").write_text(
        "# ADR-001: Use Something\n\n"
        "Status: proposed\n\n"
        "Some prose.\n",
        encoding="utf-8",
    )
    adrs = scan_adrs([str(tmp_path)])
    assert len(adrs) == 1
    assert adrs[0].status == "proposed"


def test_scan_adrs_skips_readme_and_template(tmp_path):
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "README.md").write_text("# Index", encoding="utf-8")
    (adr_dir / "template.md").write_text("# Template", encoding="utf-8")
    (adr_dir / "0001-real.md").write_text("# ADR-001: Real\n\n## Status\naccepted\n", encoding="utf-8")
    adrs = scan_adrs([str(tmp_path)])
    assert [a.id for a in adrs] == ["ADR-001"]


def test_scan_adrs_supports_alt_dirs(tmp_path):
    """`docs/decisions/`, `architecture/decisions/`, `adr/` should also work."""
    for sub in ("docs/decisions", "architecture/decisions", "adr"):
        d = tmp_path / sub
        d.mkdir(parents=True)
        (d / "0001-x.md").write_text(
            f"# ADR-001: {sub}\n\n## Status\naccepted\n", encoding="utf-8"
        )
    # Each dir hits the singleton ID — first wins (sorted dir order)
    adrs = scan_adrs([str(tmp_path)])
    assert len(adrs) == 1
    assert adrs[0].id == "ADR-001"


def test_scan_adrs_normalizes_status_synonyms(tmp_path):
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001.md").write_text(
        "# ADR-001: x\n\nStatus: Approved (2026-01-01)\n", encoding="utf-8"
    )
    adrs = scan_adrs([str(tmp_path)])
    assert adrs[0].status == "accepted"
