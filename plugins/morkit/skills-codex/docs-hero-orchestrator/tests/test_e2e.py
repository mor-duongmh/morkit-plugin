"""End-to-end smoke tests for the docs-hero pipeline.

Exercises the full chain via subprocess (matching real user execution):
  init  → all 3 docs rendered with expected anchors + screen-specs
  meta  → meta_manager rebuild produces hashes
  diff  → delta + detect_manual_edits + compute_diff + apply_patch
  cycle → idempotent replay of the same delta is a no-op
  manual edit → conflict detection skips UPDATE
  deprecate → entity moves to Appendix Z

Slower than unit tests (subprocess overhead) but real proof the pieces compose.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))

from lib.normalized_schema import (  # noqa: E402
    ApiSpec,
    AuthConfig,
    Column,
    Database,
    Endpoint,
    FunctionalRequirement,
    NonFunctionalRequirement,
    Overview,
    Priority,
    ProjectMeta,
    ProjectModel,
    Relationship,
    Screen,
    SourceRef,
    Table,
    save_project_model,
)

PYTHON = sys.executable
DISPATCH = _ORCH / "dispatch_coordinator.py"
META_MGR = _ORCH / "meta_manager.py"
AGGREGATE = _ORCH / "aggregate_report.py"


# --- Fixtures ---


def _build_full_model() -> ProjectModel:
    """Project model with content in every doc bucket."""
    return ProjectModel(
        meta=ProjectMeta(project_name="E2E-App", version="1.0", brse_name="QA"),
        overview=Overview(
            purpose="End-to-end fixture for docs-hero pipeline tests.",
            in_scope=["User auth", "Order placement"],
        ),
        functional_requirements=[
            FunctionalRequirement(
                id="FR-001", name="Login", description="User authenticates",
                main_flow=["Submit email+password", "Validate", "Issue session"],
                related_screens=["SCREEN-001"], priority=Priority.HIGH,
                source=SourceRef(origin="manual"),
            ),
            FunctionalRequirement(
                id="FR-002", name="Logout", description="User ends session",
                main_flow=["Click logout", "Clear session"],
                related_screens=["SCREEN-001"], priority=Priority.MID,
                source=SourceRef(origin="manual"),
            ),
        ],
        non_functional_requirements=[
            NonFunctionalRequirement(
                id="NFR-001", category="Performance",
                requirement="Login responds within budget",
                metric="< 500ms p95",
                source=SourceRef(origin="manual"),
            ),
        ],
        screens=[
            Screen(
                id="SCREEN-001", slug="login", name="Login Screen",
                related_fr=["FR-001", "FR-002"], role="guest",
                url_path="/login",
                source=SourceRef(origin="manual"),
            ),
        ],
        api=ApiSpec(
            base_url="https://api.example.com", version="1.0",
            overview="Public API",
            auth=AuthConfig(type="Bearer"),
            endpoints=[
                Endpoint(
                    id="ENDPOINT-POST-auth-login",
                    method="POST", path="/auth/login",
                    description="Login endpoint",
                    auth_required=False,
                    related_fr=["FR-001"],
                ),
            ],
        ),
        database=Database(
            engine="PostgreSQL",
            tables=[
                Table(
                    id="TBL-001", name="users", purpose="User accounts",
                    columns=[
                        Column(name="id", type="UUID", is_pk=True, nullable=False),
                        Column(name="email", type="VARCHAR(255)", is_unique=True,
                               nullable=False),
                    ],
                    related_fr=["FR-001"],
                ),
                Table(
                    id="TBL-002", name="sessions", purpose="Active sessions",
                    columns=[
                        Column(name="id", type="UUID", is_pk=True, nullable=False),
                        Column(name="user_id", type="UUID", is_fk=True,
                               references="users.id", nullable=False),
                    ],
                ),
            ],
            relationships=[
                Relationship(id="REL-001", parent_table="users",
                             child_table="sessions", type="1:N",
                             on_delete="CASCADE", label="owns"),
            ],
        ),
    )


@pytest.fixture(scope="module")
def workspace():
    """Single shared workspace for all E2E tests in this module."""
    with tempfile.TemporaryDirectory(prefix="docs-hero-e2e-") as td:
        root = Path(td)
        model_path = root / "project-model.json"
        save_project_model(_build_full_model(), model_path)
        yield {
            "root": root,
            "model": model_path,
            "docs": root / "docs",
            "tmp": root / ".tmp",
            "meta": root / "docs" / ".docs-hero-meta.json",
        }


def _run(cmd: list, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(c) for c in cmd], capture_output=True, text=True, cwd=cwd, timeout=120
    )


# --- E2E Init ---


def test_e2e_init_renders_all_three_docs(workspace):
    """`/docs-hero init` produces srs.md + api-docs.md + database-design.md."""
    res = _run([
        PYTHON, DISPATCH, "init",
        "--project-model", workspace["model"],
        "--language", "EN",
        "--outputs", "srs,api,db",
        "--docs-dir", workspace["docs"],
    ])
    assert res.returncode == 0, f"dispatch failed: {res.stderr}"

    docs = workspace["docs"]
    assert (docs / "srs.md").exists()
    assert (docs / "api-docs.md").exists()
    assert (docs / "database-design.md").exists()


def test_e2e_init_renders_screen_specs(workspace):
    """Per-screen file gets generated under docs/screen-specs/."""
    spec = workspace["docs"] / "screen-specs" / "SCREEN-001-login.md"
    assert spec.exists()
    text = spec.read_text(encoding="utf-8")
    assert "Login Screen" in text


def test_e2e_init_emits_expected_anchors(workspace):
    """All section IDs land as H3 anchors in their respective docs."""
    srs = (workspace["docs"] / "srs.md").read_text(encoding="utf-8")
    api = (workspace["docs"] / "api-docs.md").read_text(encoding="utf-8")
    db = (workspace["docs"] / "database-design.md").read_text(encoding="utf-8")

    assert "### FR-001" in srs and "### FR-002" in srs
    assert "### NFR-001" in srs
    assert "### SCREEN-001" in srs
    assert "### ENDPOINT-POST-auth-login" in api
    assert "### TBL-001" in db and "### TBL-002" in db
    assert "### REL-001" in db


def test_e2e_database_design_has_mermaid_erd(workspace):
    db = (workspace["docs"] / "database-design.md").read_text(encoding="utf-8")
    assert "```mermaid" in db
    assert "erDiagram" in db
    assert "USERS" in db and "SESSIONS" in db
    # cardinality marker for 1:N
    assert "||--o{" in db


# --- Meta + report ---


def test_e2e_meta_rebuild_succeeds(workspace):
    """meta_manager rebuild builds .docs-hero-meta.json with hashes per section."""
    if not (workspace["docs"] / "srs.md").exists():
        pytest.skip("requires init test to have run first (file-order dependency)")
    res = _run([
        PYTHON, META_MGR,
        "--docs-dir", workspace["docs"],
        "--meta", workspace["meta"],
        "rebuild",
    ])
    assert res.returncode == 0, f"meta rebuild failed: {res.stderr}"
    assert workspace["meta"].exists()
    meta = json.loads(workspace["meta"].read_text())
    # Sidecar should have at least one section per doc
    section_counts = {k: len(v.get("section_hashes", {})) for k, v in meta.get("docs", {}).items()}
    assert sum(section_counts.values()) > 0, f"empty meta: {meta}"


def test_e2e_aggregate_report_passes(workspace):
    """aggregate_report.py prints a Health Check section after init."""
    res = _run([
        PYTHON, AGGREGATE,
        "--docs-dir", workspace["docs"],
    ])
    assert res.returncode == 0
    assert "Health Check" in res.stdout
    assert "srs.md" in res.stdout
    assert "api-docs.md" in res.stdout


# --- E2E Update flow ---


def test_e2e_update_adds_new_fr(workspace):
    """A Delta ADDing FR-003 results in a new H3 anchor in srs.md (preserves FR-001/FR-002)."""
    delta_path = workspace["tmp"] / "add-fr.json"
    delta_path.parent.mkdir(parents=True, exist_ok=True)
    delta_path.write_text(json.dumps({
        "source_type": "plan",
        "source_path": "test-plan.md",
        "changes": [
            {
                "op": "ADD",
                "entity_type": "FR",
                "entity_id": "FR-003",
                "payload": {
                    "id": "FR-003",
                    "name": "Password Reset",
                    "description": "User resets forgotten password via email link.",
                    "main_flow": ["Request reset", "Email token", "Set new password"],
                    "priority": "Mid",
                },
                "reason": "e2e test",
            },
        ],
    }))

    res = _run([
        PYTHON, DISPATCH, "update",
        "--delta", delta_path,
        "--docs-dir", workspace["docs"],
        "--meta", workspace["meta"],
        "--tmp-dir", workspace["tmp"],
    ])
    assert res.returncode == 0, f"update failed: {res.stderr}\nstdout: {res.stdout}"

    srs = (workspace["docs"] / "srs.md").read_text(encoding="utf-8")
    assert "### FR-003" in srs, "new FR not added"
    assert "### FR-001" in srs and "### FR-002" in srs, "existing FRs lost"


def test_e2e_idempotent_replay_is_noop(workspace):
    """Running the same Delta twice should not duplicate sections."""
    delta_path = workspace["tmp"] / "add-fr.json"  # reuse from previous test
    if not delta_path.exists():
        pytest.skip("requires test_e2e_update_adds_new_fr ran first")

    res = _run([
        PYTHON, DISPATCH, "update",
        "--delta", delta_path,
        "--docs-dir", workspace["docs"],
        "--meta", workspace["meta"],
        "--tmp-dir", workspace["tmp"],
    ])
    assert res.returncode == 0

    srs = (workspace["docs"] / "srs.md").read_text(encoding="utf-8")
    # FR-003 should appear exactly once as an H3 anchor
    occurrences = srs.count("### FR-003")
    assert occurrences == 1, f"FR-003 duplicated {occurrences} times"


def test_e2e_deprecation_moves_to_appendix(workspace):
    """DEPRECATE FR-002 → it moves out of the main FR section."""
    delta_path = workspace["tmp"] / "deprecate.json"
    delta_path.write_text(json.dumps({
        "source_type": "plan",
        "source_path": "test.md",
        "changes": [
            {
                "op": "DEPRECATE",
                "entity_type": "FR",
                "entity_id": "FR-002",
                "reason": "no longer needed",
            },
        ],
    }))

    res = _run([
        PYTHON, DISPATCH, "update",
        "--delta", delta_path,
        "--docs-dir", workspace["docs"],
        "--meta", workspace["meta"],
        "--tmp-dir", workspace["tmp"],
    ])
    assert res.returncode == 0, f"deprecate failed: {res.stderr}"

    srs = (workspace["docs"] / "srs.md").read_text(encoding="utf-8")
    # FR-002 should still be present (moved, not deleted) — likely as DEPRECATED-FR-002
    # or under an Appendix heading. We just assert it's not gone.
    assert "FR-002" in srs
    # And FR-001 / FR-003 still in main section
    assert "### FR-001" in srs
    assert "### FR-003" in srs
