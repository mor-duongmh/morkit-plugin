"""Tests for validate_state.py (Phase 1 foundation)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_state import (  # noqa: E402
    GATED_STAGES,
    STAGES,
    validate_state,
)


def _valid_state() -> dict:
    return {
        "project": "acme-portal",
        "stage": "G3",
        "format": "brse",
        "lang": "JP",
        "stages": {
            "G0": {"status": "done", "artifact": "inputs/"},
            "G3": {
                "status": "in_progress",
                "artifact": None,
                "gate": {"decision": "pending", "note": ""},
            },
        },
    }


def test_valid_state_passes():
    assert validate_state(_valid_state()) == []


def test_missing_required_keys():
    errors = validate_state({"format": "brse"})
    assert any("project" in e for e in errors)
    assert any("stage" in e for e in errors)
    assert any("stages" in e for e in errors)


def test_bad_stage_enum():
    s = _valid_state()
    s["stage"] = "G9"
    errors = validate_state(s)
    assert any("stage must be one of" in e for e in errors)


def test_bad_format_and_lang():
    s = _valid_state()
    s["format"] = "scrum"
    s["lang"] = "FR"
    errors = validate_state(s)
    assert any("format must be one of" in e for e in errors)
    assert any("lang must be one of" in e for e in errors)


def test_unknown_stage_id_in_stages():
    s = _valid_state()
    s["stages"]["G42"] = {"status": "pending"}
    errors = validate_state(s)
    assert any("unknown stage id" in e for e in errors)


def test_bad_stage_status():
    s = _valid_state()
    s["stages"]["G0"]["status"] = "finished"
    errors = validate_state(s)
    assert any("status must be one of" in e for e in errors)


def test_stage_missing_status():
    s = _valid_state()
    s["stages"]["G0"] = {"artifact": "inputs/"}
    errors = validate_state(s)
    assert any("missing required key: status" in e for e in errors)


def test_bad_gate_decision():
    s = _valid_state()
    s["stages"]["G3"]["gate"]["decision"] = "maybe"
    errors = validate_state(s)
    assert any("gate.decision must be one of" in e for e in errors)


def test_non_dict_input():
    assert validate_state(["not", "a", "dict"]) == ["state must be a JSON object"]


def test_stage_constants_are_g0_through_g7():
    assert STAGES == ["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7"]
    # G2 is gated too — the foundational function-list confirm gate.
    assert GATED_STAGES == {"G2", "G3", "G4", "G6"}


def test_g2_gate_is_valid_and_decision_checked():
    s = _valid_state()
    s["stages"]["G2"] = {
        "status": "in_progress",
        "artifact": None,
        "gate": {"decision": "proceed", "note": "BrSE confirmed list"},
    }
    assert validate_state(s) == []
    # An invalid G2 gate decision is still rejected by the shared gate validator.
    s["stages"]["G2"]["gate"]["decision"] = "nope"
    errors = validate_state(s)
    assert any("gate.decision must be one of" in e for e in errors)
