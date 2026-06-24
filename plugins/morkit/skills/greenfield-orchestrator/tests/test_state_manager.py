"""Tests for state_manager.py (Phase 6 orchestrator)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import state_manager as sm  # noqa: E402
from validate_state import validate_state  # noqa: E402


def test_init_state_is_valid_and_at_g0():
    state = sm.init_state("acme", "brse", "JP")
    assert validate_state(state) == []
    assert state["stage"] == "G0"
    assert state["stages"]["G0"]["status"] == "in_progress"
    assert all(state["stages"][s]["status"] == "pending" for s in ["G1", "G7"])
    # Gated stages get a pending gate up front (G2 included — foundational doc).
    for g in ("G2", "G3", "G4", "G6"):
        assert state["stages"][g]["gate"]["decision"] == "pending"


def test_advance_marks_done_and_next_in_progress():
    state = sm.init_state("acme")
    sm.advance(state)
    assert state["stage"] == "G1"
    assert state["stages"]["G0"]["status"] == "done"
    assert state["stages"]["G1"]["status"] == "in_progress"
    assert validate_state(state) == []


def test_advance_through_full_pipeline_to_g7():
    state = sm.init_state("acme")
    for _ in range(len(sm.STAGES) - 1):
        sm.advance(state)
    assert state["stage"] == "G7"
    assert state["stages"]["G7"]["status"] == "in_progress"
    # Advancing at the last stage marks G7 done, stays at G7.
    sm.advance(state)
    assert state["stage"] == "G7"
    assert state["stages"]["G7"]["status"] == "done"


def test_set_gate_only_on_gated_stages():
    state = sm.init_state("acme")
    sm.set_gate(state, "G3", "proceed", "looks good")
    assert state["stages"]["G3"]["gate"] == {"decision": "proceed", "note": "looks good"}
    # G2 is now gated (function-list confirm gate).
    sm.set_gate(state, "G2", "proceed", "BrSE confirmed list")
    assert state["stages"]["G2"]["gate"] == {"decision": "proceed", "note": "BrSE confirmed list"}
    with pytest.raises(ValueError):
        sm.set_gate(state, "G1", "proceed")  # G1 is not gated


def test_g2_gate_confirm_then_advance_to_g3():
    state = sm.init_state("acme", "brse", "JP")
    sm.advance(state)  # → G1
    sm.advance(state)  # → G2
    assert state["stage"] == "G2"
    # "Another round" (adjust) then "Proceed" (confirm).
    sm.set_gate(state, "G2", "adjust", "needs another Q&A round")
    sm.set_gate(state, "G2", "proceed", "confirmed")
    assert state["stages"]["G2"]["gate"]["decision"] == "proceed"
    sm.advance(state)  # → G3
    assert state["stage"] == "G3"
    assert validate_state(state) == []


def test_set_stage_rejects_unknown_stage():
    state = sm.init_state("acme")
    with pytest.raises(ValueError):
        sm.set_stage(state, "G9", "done")


def test_save_load_roundtrip_atomic(tmp_path):
    state = sm.init_state("acme", "agile", "EN")
    path = tmp_path / "sub" / "state.json"   # parent dir created by save()
    sm.save(state, path)
    assert path.exists()
    # No temp file left behind (unique pid-tagged temp, cleaned up on success).
    assert list((path.parent).glob("*.tmp")) == []
    loaded = sm.load(path)
    assert loaded == state


def test_kill_and_resume_restores_mid_pipeline(tmp_path):
    # Drive to G3, record a gate decision + artifact, persist — then "resume".
    state = sm.init_state("acme", "brse", "JP")
    path = tmp_path / "state.json"
    sm.advance(state)  # G1
    sm.set_stage(state, "G1", "done", "brainstorm-report.md")
    sm.advance(state)  # G2
    sm.advance(state)  # G3
    sm.set_gate(state, "G3", "proceed", "BA approved")
    sm.save(state, path)

    # Fresh process would just load:
    resumed = sm.load(path)
    assert resumed["stage"] == "G3"
    assert resumed["stages"]["G1"]["artifact"] == "brainstorm-report.md"
    assert resumed["stages"]["G3"]["gate"]["decision"] == "proceed"


def test_load_rejects_corrupt_state(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"stage": "G9", "stages": {}}', encoding="utf-8")
    with pytest.raises(ValueError):
        sm.load(path)
