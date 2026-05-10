"""Tests for generate-system-architecture sub-skill."""
from __future__ import annotations

import sys
from pathlib import Path

_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))

_ARCH = Path(__file__).resolve().parents[2] / "generate-system-architecture" / "scripts"
sys.path.insert(0, str(_ARCH))

from generate_mermaid_arch import generate_arch_diagram  # noqa: E402
from lib.normalized_schema import (  # noqa: E402
    Component,
    Interaction,
    Language,
    Layer,
    ProjectMeta,
    ProjectModel,
    QualityGoal,
)
from render_system_architecture import render_system_architecture  # noqa: E402
from system_architecture_sync_apply import parse_proposal  # noqa: E402
from system_architecture_sync_propose import (  # noqa: E402
    diff_components,
    parse_existing_components,
    render_proposal,
)
from parse_codebase_arch import ComponentDef, scan_components  # noqa: E402


def _build_minimal_arch_model() -> ProjectModel:
    return ProjectModel(
        meta=ProjectMeta(project_name="TestArch", version="1.0"),
        components=[
            Component(id="CMP-001", name="auth-svc", kind="service",
                      tech=["NestJS"], depends_on=["CMP-002"]),
            Component(id="CMP-002", name="user-db", kind="datastore",
                      tech=["Postgres"]),
        ],
        layers=[
            Layer(id="LAY-001", name="Application", component_ids=["CMP-001"]),
            Layer(id="LAY-002", name="Persistence", component_ids=["CMP-002"]),
        ],
        interactions=[
            Interaction(id="INX-001", from_id="CMP-001", to_id="CMP-002",
                        protocol="db", description="Read users"),
        ],
        quality_goals=[
            QualityGoal(id="QG-001", name="p95 <200ms"),
        ],
    )


# --- Mermaid diagram ---


def test_arch_mermaid_includes_components_and_edges():
    model = _build_minimal_arch_model()
    out = generate_arch_diagram(model.components, model.layers, model.interactions)
    assert out.startswith("```mermaid")
    assert out.endswith("```")
    assert "flowchart LR" in out
    assert "CMP-001" in out
    assert "CMP-002" in out
    assert "auth-svc" in out
    assert "Read users" in out  # interaction label
    assert 'subgraph LAY_001["Application"]' in out
    assert "class CMP-001 service" in out
    assert "class CMP-002 datastore" in out


def test_arch_mermaid_falls_back_to_depends_on_when_no_interactions():
    model = _build_minimal_arch_model()
    model.interactions = []
    out = generate_arch_diagram(model.components, model.layers, model.interactions)
    # depends_on edge should appear instead
    assert "CMP-001 --> CMP-002" in out


def test_arch_mermaid_unassigned_subgraph():
    cmps = [Component(id="CMP-X", name="orphan", kind="service")]
    out = generate_arch_diagram(cmps, [], [])
    assert "Unassigned" in out


# --- Renderer ---


def test_render_arch_top_sections_and_diagram():
    model = _build_minimal_arch_model()
    text = render_system_architecture(model, Language.EN)
    assert text.startswith("# System Architecture — TestArch")
    for heading in (
        "## 1. Introduction & Goals",
        "## 2. Architecture Constraints",
        "## 3. Context & Scope",
        "## 4. Solution Strategy",
        "## 5. Building Block View",
        "## 6. Runtime View",
        "## 7. Deployment View",
        "## 8. Crosscutting Concepts",
    ):
        assert heading in text, f"missing {heading!r}"
    assert "<!-- ARCH-DIAGRAM-START -->" in text
    assert "<!-- ARCH-DIAGRAM-END -->" in text
    # Per-component H3 anchor
    assert "### CMP-001: auth-svc" in text
    # Quality goal embedded
    assert "QG-001" in text


def test_render_arch_handles_empty_components_with_placeholder():
    pm = ProjectModel(meta=ProjectMeta(project_name="Empty"))
    text = render_system_architecture(pm, Language.EN)
    assert "Placeholder[No components yet]" in text


def test_render_arch_jp_title():
    model = _build_minimal_arch_model()
    text = render_system_architecture(model, Language.JP)
    assert text.startswith("# システムアーキテクチャ")


# --- Scanner ---


def test_scan_components_dir_convention(tmp_path):
    (tmp_path / "services" / "alpha").mkdir(parents=True)
    (tmp_path / "services" / "beta").mkdir(parents=True)
    (tmp_path / "packages" / "shared").mkdir(parents=True)
    (tmp_path / "apps" / "web").mkdir(parents=True)

    cmps = scan_components([str(tmp_path)])
    ids = {c.id for c in cmps}
    assert "CMP-alpha" in ids
    assert "CMP-beta" in ids
    assert "CMP-shared" in ids
    assert "CMP-web" in ids
    by_id = {c.id: c for c in cmps}
    assert by_id["CMP-alpha"].kind == "service"
    assert by_id["CMP-shared"].kind == "library"
    assert by_id["CMP-web"].kind == "frontend"


def test_scan_components_docker_compose(tmp_path):
    (tmp_path / "docker-compose.yml").write_text(
        "version: '3'\n"
        "services:\n"
        "  api:\n"
        "    image: node:18\n"
        "  cache:\n"
        "    image: redis:7\n",
        encoding="utf-8",
    )
    cmps = scan_components([str(tmp_path)])
    ids = {c.id for c in cmps}
    assert "CMP-api" in ids
    assert "CMP-cache" in ids


def test_scan_components_dependency_edges(tmp_path):
    """Files in services/A importing services/B should produce CMP-A → CMP-B edge."""
    (tmp_path / "services" / "alpha").mkdir(parents=True)
    (tmp_path / "services" / "beta").mkdir(parents=True)
    (tmp_path / "services" / "alpha" / "main.py").write_text(
        "from services.beta import core\n", encoding="utf-8"
    )
    (tmp_path / "services" / "beta" / "core.py").write_text("X = 1\n", encoding="utf-8")

    cmps = scan_components([str(tmp_path)])
    by_id = {c.id: c for c in cmps}
    assert "CMP-beta" in by_id["CMP-alpha"].depends_on


# --- Sync propose / apply ---


def test_diff_components_add_and_deprecate():
    code = [
        ComponentDef(id="CMP-new", name="new", kind="service"),
        ComponentDef(id="CMP-keep", name="keep", kind="service"),
    ]
    doc_ids = {"CMP-keep", "CMP-old"}
    to_add, to_dep = diff_components(code, doc_ids)
    assert [c.id for c in to_add] == ["CMP-new"]
    assert to_dep == ["CMP-old"]


def test_render_proposal_has_checkboxes(tmp_path):
    code = [ComponentDef(id="CMP-new", name="new", kind="service", tech=["Go"])]
    text = render_proposal([str(tmp_path)], tmp_path / "fake.md", code, code, ["CMP-old"])
    assert "[ ] ADD CMP-new" in text
    assert "[ ] DEPRECATE CMP-old" in text


def test_parse_proposal_picks_only_checked():
    proposal = (
        "### [x] ADD CMP-new\n"
        "- Name: `new`\n"
        "- Kind: service\n\n"
        "### [ ] ADD CMP-skipped\n"
        "- Name: `skipped`\n\n"
        "### [X] DEPRECATE CMP-old\n"
    )
    changes = parse_proposal(proposal)
    assert len(changes) == 2
    by_id = {c.entity_id: c for c in changes}
    assert by_id["CMP-new"].op == "ADD"
    assert by_id["CMP-new"].payload == {"name": "new", "kind": "service"}
    assert by_id["CMP-old"].op == "DEPRECATE"


def test_parse_existing_components(tmp_path):
    doc = tmp_path / "system-architecture.md"
    doc.write_text(
        "## 5. Building Block View\n\n"
        "### CMP-001: auth-svc\n- Kind: service\n\n"
        "### CMP-002: user-db\n- Kind: datastore\n",
        encoding="utf-8",
    )
    ids = parse_existing_components(doc)
    assert ids == {"CMP-001", "CMP-002"}
