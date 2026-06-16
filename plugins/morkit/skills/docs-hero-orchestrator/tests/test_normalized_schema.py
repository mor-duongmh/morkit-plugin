"""Tests for lib/normalized_schema.py."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib.normalized_schema import (  # noqa: E402
    Change,
    Column,
    Database,
    Delta,
    Endpoint,
    FunctionalRequirement,
    Language,
    NonFunctionalRequirement,
    Priority,
    ProjectMeta,
    ProjectModel,
    Screen,
    SourceRef,
    Status,
    Table,
    load_delta,
    load_project_model,
    save_delta,
    save_project_model,
)


# --- Basic instantiation ---


def test_minimal_project_model():
    pm = ProjectModel(meta=ProjectMeta(project_name="Test"))
    assert pm.meta.project_name == "Test"
    assert pm.meta.language == Language.EN  # default
    assert pm.functional_requirements == []


def test_fr_id_pattern_validates():
    fr = FunctionalRequirement(
        id="FR-001",
        name="Login",
        source=SourceRef(origin="manual"),
    )
    assert fr.id == "FR-001"
    assert fr.priority == Priority.MID
    assert fr.status == Status.ACTIVE


def test_fr_id_pattern_rejects_invalid():
    with pytest.raises(Exception):
        FunctionalRequirement(id="X-001", name="Bad", source=SourceRef(origin="manual"))


def test_screen_id_pattern():
    s = Screen(id="SCREEN-001", slug="login", name="Login")
    assert s.id == "SCREEN-001"


def test_table_with_columns():
    t = Table(
        id="TBL-001",
        name="users",
        columns=[
            Column(name="id", type="UUID", is_pk=True),
            Column(name="email", type="VARCHAR(255)", is_unique=True),
        ],
    )
    assert len(t.columns) == 2
    assert t.columns[0].is_pk is True


def test_endpoint_method_literal():
    ep = Endpoint(id="ENDPOINT-GET-users", method="GET", path="/users")
    assert ep.method == "GET"


def test_endpoint_invalid_method_rejects():
    with pytest.raises(Exception):
        Endpoint(id="ENDPOINT-XYZ-users", method="INVALID", path="/users")


# --- Extra fields preserved ---


def test_extra_fields_preserved_via_config():
    fr = FunctionalRequirement.model_validate(
        {
            "id": "FR-001",
            "name": "X",
            "source": {"origin": "openspec"},
            "custom_field": "preserved",
            "openspec_metadata": {"x": 1},
        }
    )
    dumped = fr.model_dump()
    assert dumped.get("custom_field") == "preserved"
    assert dumped.get("openspec_metadata") == {"x": 1}


# --- Database section ---


def test_database_default_engine():
    db = Database()
    assert db.engine == "PostgreSQL"
    assert db.tables == []


# --- Delta ---


def test_delta_change_validates():
    d = Delta(
        source_type="openspec",
        source_path="openspec/changes/c1",
        changes=[
            Change(op="ADD", entity_type="FR", entity_id="FR-008"),
            Change(op="DEPRECATE", entity_type="FR", entity_id="FR-003", reason="Replaced"),
        ],
    )
    assert len(d.changes) == 2
    assert d.changes[0].op == "ADD"


def test_delta_invalid_op_rejects():
    with pytest.raises(Exception):
        Change(op="REMOVE", entity_type="FR", entity_id="FR-001")


# --- IO round-trip ---


def test_save_load_project_model_roundtrip():
    pm = ProjectModel(
        meta=ProjectMeta(project_name="Test", version="1.0", language=Language.JP),
        functional_requirements=[
            FunctionalRequirement(
                id="FR-001",
                name="Login",
                description="User login flow.",
                main_flow=["Step 1", "Step 2"],
                source=SourceRef(origin="openspec", openspec_change_id="c1"),
            ),
        ],
        non_functional_requirements=[
            NonFunctionalRequirement(
                id="NFR-001",
                category="Performance",
                requirement="Response < 500ms",
            ),
        ],
    )

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "model.json"
        save_project_model(pm, path)
        loaded = load_project_model(path)

    assert loaded.meta.project_name == "Test"
    assert loaded.meta.language == Language.JP
    assert len(loaded.functional_requirements) == 1
    assert loaded.functional_requirements[0].main_flow == ["Step 1", "Step 2"]


def test_save_load_delta_roundtrip():
    delta = Delta(
        source_type="plan",
        source_path="plans/x.md",
        changes=[
            Change(op="ADD", entity_type="FR", entity_id="FR-009", payload={"name": "Test"}),
        ],
    )

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "delta.json"
        save_delta(delta, path)
        loaded = load_delta(path)

    assert loaded.source_type == "plan"
    assert len(loaded.changes) == 1
    assert loaded.changes[0].payload == {"name": "Test"}


def test_serialized_json_excludes_none():
    """save_project_model uses exclude_none → cleaner JSON."""
    pm = ProjectModel(meta=ProjectMeta(project_name="T"))
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "m.json"
        save_project_model(pm, path)
        data = json.loads(path.read_text())

    # `date` is None on default → should NOT appear in JSON
    assert "date" not in data["meta"]
    # `project_name` IS set → should appear
    assert data["meta"]["project_name"] == "T"


def test_load_invalid_json_raises():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "bad.json"
        path.write_text("not valid json")
        with pytest.raises(json.JSONDecodeError):
            load_project_model(path)


def test_new_template_updated_entities_instantiate():
    """Template-updated entities (BR/ROLE/RPT/AC/Q/CONS/ASM/ENT/REF/UC) all validate."""
    from lib.normalized_schema import (
        AcceptanceCriterion,
        Assumption,
        BusinessRule,
        Constraint,
        DocStatus,
        EntityDef,
        Issue,
        OpenQuestion,
        Reference,
        Report,
        Role,
        UseCase,
    )

    BusinessRule(id="BR-001", rule="x", related_fr=["FR-001"])
    Role(id="ROLE-001", name="Admin")
    Report(id="RPT-001", name="r")
    AcceptanceCriterion(id="AC-001", criterion="Given X")
    OpenQuestion(id="Q-001", question="?")
    Constraint(id="CONS-001", constraint="x")
    Assumption(id="ASM-001", assumption="x")
    EntityDef(id="ENT-001", entity="users")
    Reference(id="REF-001", document="Spec")
    Issue(id="ISSUE-001", issue="slow")
    UseCase(id="UC-001", name="Login", actor="User",
            main_success_scenario=["s1", "s2"])
    assert DocStatus.DRAFT.value == "Draft"


def test_priority_moscow_values_accepted():
    fr = FunctionalRequirement(id="FR-X", name="t", source=SourceRef(origin="manual"),
                               priority=Priority.MUST)
    assert fr.priority == Priority.MUST


def test_delta_change_accepts_new_entity_types():
    """Delta supports BR/ROLE/RPT/AC/Q/UC/CONS/ASM/ENT/REF/RISK/ISSUE."""
    for et in ("BR", "ROLE", "RPT", "AC", "Q", "UC", "CONS", "ASM", "ENT", "REF", "RISK", "ISSUE"):
        Change(op="ADD", entity_type=et, entity_id=f"{et}-001")


def test_arch_entities_instantiate():
    """System Architecture entities (CMP/LAY/INX/QG)."""
    from lib.normalized_schema import Component, Interaction, Layer, QualityGoal

    cmp = Component(
        id="CMP-001",
        name="auth-svc",
        kind="service",
        responsibility="JWT issuance",
        tech=["NestJS", "Postgres"],
        depends_on=["CMP-002"],
    )
    assert cmp.kind == "service"
    assert "CMP-002" in cmp.depends_on

    lay = Layer(id="LAY-001", name="Domain", component_ids=["CMP-001"])
    assert lay.component_ids == ["CMP-001"]

    inx = Interaction(id="INX-001", from_id="CMP-001", to_id="CMP-002", protocol="http")
    assert inx.protocol == "http"

    qg = QualityGoal(id="QG-001", name="Low latency", priority=Priority.HIGH)
    assert qg.priority == Priority.HIGH


def test_standards_entities_instantiate():
    """Code Standards entities (LNT/NAM/CMT/FMT)."""
    from lib.normalized_schema import (
        CommitPolicy,
        FormattingRule,
        LintConfig,
        NamingConvention,
    )

    lc = LintConfig(
        id="LNT-001",
        tool="eslint",
        config_path=".eslintrc.json",
        extends=["eslint:recommended", "plugin:@typescript-eslint/recommended"],
        rules_summary={"no-unused-vars": "error"},
    )
    assert lc.tool == "eslint"
    assert len(lc.extends) == 2

    nc = NamingConvention(id="NAM-001", scope="function", pattern="camelCase", example="getUser")
    assert nc.scope == "function"

    cp = CommitPolicy(
        id="CMT-001",
        style="conventional",
        allowed_types=["feat", "fix", "docs"],
        scope_required=False,
    )
    assert cp.style == "conventional"

    fr_ = FormattingRule(id="FMT-001", tool="ruff", option="line-length", value="100")
    assert fr_.value == "100"


def test_summary_entities_instantiate():
    """Codebase Summary entities (RPO/TCH/PKG/MOD). RPO is a singleton."""
    from lib.normalized_schema import ModuleEntry, PackageInfo, RepoOverview, TechStackItem

    ro = RepoOverview(name="morkit", primary_language="Python", loc_total=12345)
    assert ro.id == "RPO-001"  # default singleton ID

    # Reject any non-RPO-001 ID
    with pytest.raises(Exception):
        RepoOverview(id="RPO-002", name="x")

    ts = TechStackItem(id="TCH-001", category="framework", name="NestJS", confidence="declared")
    assert ts.confidence == "declared"

    pkg = PackageInfo(id="PKG-001", name="@morkit/api", path="apps/api", manager="npm", dep_count=42)
    assert pkg.dep_count == 42

    me = ModuleEntry(id="MOD-001", path="src/main.ts", loc=120, language="TypeScript", is_entry_point=True)
    assert me.is_entry_point is True


def test_guidelines_entities_instantiate():
    """Design Guidelines entities (DPR/PTN/ADR)."""
    from lib.normalized_schema import ADR, DesignPrinciple, PatternGuideline

    dp = DesignPrinciple(
        id="DPR-001",
        name="Fail fast",
        statement="Surface invalid state at the boundary.",
        rationale="Avoids silent corruption downstream.",
        examples=["validate inputs at API edge"],
    )
    assert dp.name == "Fail fast"

    pg = PatternGuideline(
        id="PTN-001",
        name="Repository",
        category="domain",
        when_to_use="Persistence aggregate root",
        when_to_avoid="Trivial CRUD without invariants",
    )
    assert pg.category == "domain"

    adr = ADR(
        id="ADR-001",
        title="Use Postgres for OLTP",
        status="accepted",
        context="…",
        decision="Postgres 15",
        consequences="Adds ops burden",
    )
    assert adr.status == "accepted"


def test_project_model_holds_new_entities():
    """ProjectModel exposes list fields for all new entity groups."""
    from lib.normalized_schema import (
        ADR,
        Component,
        DesignPrinciple,
        LintConfig,
        NamingConvention,
        RepoOverview,
        TechStackItem,
    )

    pm = ProjectModel(
        meta=ProjectMeta(project_name="T"),
        components=[Component(id="CMP-001", name="api", kind="service")],
        lint_configs=[LintConfig(id="LNT-001", tool="ruff", config_path="pyproject.toml")],
        naming_conventions=[NamingConvention(id="NAM-001", scope="class", pattern="PascalCase")],
        repo_overview=RepoOverview(name="t", loc_total=1),
        tech_stack=[TechStackItem(id="TCH-001", category="language", name="Python")],
        design_principles=[DesignPrinciple(id="DPR-001", name="KISS")],
        adrs=[ADR(id="ADR-001", title="x", decision="y")],
    )
    assert pm.components[0].id == "CMP-001"
    assert pm.lint_configs[0].tool == "ruff"
    assert pm.repo_overview.id == "RPO-001"
    assert pm.adrs[0].title == "x"


def test_delta_change_accepts_arch_standards_summary_guidelines_types():
    """Delta supports CMP/LAY/INX/QG/LNT/NAM/CMT/FMT/RPO/TCH/PKG/MOD/DPR/PTN/ADR."""
    new_types = (
        "CMP", "LAY", "INX", "QG",
        "LNT", "NAM", "CMT", "FMT",
        "RPO", "TCH", "PKG", "MOD",
        "DPR", "PTN", "ADR",
    )
    for et in new_types:
        Change(op="ADD", entity_type=et, entity_id=f"{et}-001")


def test_load_missing_required_field_raises():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "m.json"
        # meta.project_name is required
        path.write_text(json.dumps({"meta": {"version": "1.0"}}))
        with pytest.raises(Exception):
            load_project_model(path)
