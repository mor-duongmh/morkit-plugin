"""Tests for validate_project_model.py (Phase 2 bridge keystone)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_project_model import (  # noqa: E402
    parse_project_model,
    validate_project_model,
)

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _minimal() -> dict:
    # Mirrors parse_inputs' empty path: meta only, everything else defaults.
    return {"meta": {"project_name": "Acme Portal"}}


def _seeded_fr() -> dict:
    """A greenfield-seeded model: FR traced to a source doc, doc_status Draft."""
    return {
        "meta": {"project_name": "Acme Portal", "language": "JP"},
        "overview": {"in_scope": ["password reset"]},
        "functional_requirements": [
            {
                "id": "FR-001",
                "name": "Password reset",
                "description": "User resets password via emailed link.",
                "doc_status": "Draft",
                "source": {"origin": "pdf", "file_path": "inputs/prd.pdf"},
                "external_sources": ["inputs/prd.pdf"],
            }
        ],
    }


def test_minimal_model_valid():
    assert validate_project_model(_minimal()) == []


def test_empty_inputs_minimal_but_valid():
    # No FRs at all (mirrors parse_inputs empty path) still validates.
    model = parse_project_model(_minimal())
    assert model.meta.project_name == "Acme Portal"
    assert model.functional_requirements == []


def test_missing_required_meta_fails_with_path():
    errors = validate_project_model({"overview": {}})
    assert errors
    assert any(e.startswith("meta") for e in errors)


def test_seeded_fr_valid():
    assert validate_project_model(_seeded_fr()) == []


def test_provenance_extras_preserved():
    model = parse_project_model(_seeded_fr())
    fr = model.functional_requirements[0]
    # doc_status is a real field; external_sources rides on extra="allow".
    assert fr.doc_status.value == "Draft"
    assert fr.external_sources == ["inputs/prd.pdf"]
    # Round-trips through model_dump (not silently dropped).
    dumped = model.model_dump(exclude_none=True)
    assert dumped["functional_requirements"][0]["external_sources"] == ["inputs/prd.pdf"]


def test_bad_fr_id_pattern_fails():
    data = _seeded_fr()
    data["functional_requirements"][0]["id"] = "feature-1"  # not FR-*
    errors = validate_project_model(data)
    assert errors
    assert any("functional_requirements" in e for e in errors)


def test_status_draft_on_status_field_rejected():
    # Guard the locked pitfall: provenance "draft" must go to doc_status,
    # NOT status (which only accepts active/deprecated).
    data = _seeded_fr()
    data["functional_requirements"][0]["status"] = "draft"
    errors = validate_project_model(data)
    assert errors
    assert any("functional_requirements" in e and "status" in e for e in errors)


def test_status_draft_on_meta_rejected_via_lint():
    # H-1 guard: extra="allow" would silently KEEP status:"draft" on meta
    # (no typed status field there), so the raw-dict lint must catch it.
    data = _minimal()
    data["meta"]["status"] = "draft"
    errors = validate_project_model(data)
    assert any("meta.status" in e and "doc_status" in e for e in errors)


def test_valid_status_active_on_entity_not_flagged():
    # Lifecycle status values stay valid — lint must not false-positive.
    data = _seeded_fr()
    data["functional_requirements"][0]["status"] = "active"
    assert validate_project_model(data) == []


def test_end_to_end_fixture_stays_valid():
    # The committed fixture is the known-good bridge output the SKILL renders
    # via init in the Phase-2 smoke test — guard it against schema drift.
    data = json.loads((_FIXTURES / "seeded-greenfield.json").read_text(encoding="utf-8"))
    assert validate_project_model(data) == []
