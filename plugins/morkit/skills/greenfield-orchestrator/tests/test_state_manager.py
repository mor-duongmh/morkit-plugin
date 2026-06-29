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
        # Gated stages now block advance until proceeded (see guard tests below).
        if state["stage"] in sm.GATED_STAGES:
            sm.set_gate(state, state["stage"], "proceed", "ok")
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
    sm.set_gate(state, "G2", "proceed", "confirmed")  # gate must pass to leave G2
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


# --- Gate guard (hard-block): advance refuses unless proceed + required confirmed ---

def _to_g2(state):
    sm.advance(state)  # G0 -> G1 (non-gated)
    sm.advance(state)  # G1 -> G2
    assert state["stage"] == "G2"


def test_advance_blocked_when_gate_pending():
    state = sm.init_state("acme")
    _to_g2(state)
    with pytest.raises(sm.GateNotPassed):
        sm.advance(state)  # gate still pending


def test_advance_blocked_on_adjust():
    state = sm.init_state("acme")
    _to_g2(state)
    sm.set_gate(state, "G2", "adjust", "redo")
    with pytest.raises(sm.GateNotPassed):
        sm.advance(state)


def test_advance_blocked_when_required_not_fully_confirmed():
    state = sm.init_state("acme")
    _to_g2(state)
    sm.set_gate(state, "G2", "proceed", "ok",
                required=["G2-A1", "G2-A2", "G2-C1"], confirmed=["G2-A1", "G2-C1"])
    with pytest.raises(sm.GateNotPassed, match="G2-A2"):
        sm.advance(state)


def test_advance_ok_when_required_subset_confirmed():
    state = sm.init_state("acme")
    _to_g2(state)
    sm.set_gate(state, "G2", "proceed", "ok",
                required=["G2-A1", "G2-C1"], confirmed=["G2-A1", "G2-C1", "G2-A2"])
    sm.advance(state)
    assert state["stage"] == "G3"


def test_advance_nonbreaking_proceed_without_checklist():
    # Legacy/old state: proceed gate, no checklist key → required is empty → advances.
    state = sm.init_state("acme")
    _to_g2(state)
    sm.set_gate(state, "G2", "proceed", "legacy")
    assert "checklist" not in state["stages"]["G2"]["gate"]
    sm.advance(state)
    assert state["stage"] == "G3"


def _to_g4(state):
    sm.advance(state)  # G1
    sm.advance(state)  # G2
    sm.set_gate(state, "G2", "proceed")
    sm.advance(state)  # G3
    sm.set_gate(state, "G3", "proceed")
    sm.advance(state)  # G4
    assert state["stage"] == "G4"


def test_g4_force_close_advances_with_note():
    state = sm.init_state("acme")
    _to_g4(state)
    sm.set_gate(state, "G4", "force-close", "khách không phản hồi đúng hạn")
    sm.advance(state)
    assert state["stage"] == "G5"


def test_g4_force_close_without_note_blocked():
    state = sm.init_state("acme")
    _to_g4(state)
    sm.set_gate(state, "G4", "force-close", "")
    with pytest.raises(sm.GateNotPassed, match="note"):
        sm.advance(state)


def test_force_close_only_valid_at_g4():
    # force-close is not a valid pass at G3 (only G4 may close-despite-open).
    state = sm.init_state("acme")
    sm.advance(state)  # G1
    sm.advance(state)  # G2
    sm.set_gate(state, "G2", "proceed")
    sm.advance(state)  # G3
    sm.set_gate(state, "G3", "force-close", "reason")
    with pytest.raises(sm.GateNotPassed):
        sm.advance(state)


def test_set_gate_records_checklist_and_stays_valid():
    state = sm.init_state("acme")
    sm.set_gate(state, "G6", "proceed", "ok",
                required=["G6-A3", "G6-A4"], confirmed=["G6-A3", "G6-A4"])
    cl = state["stages"]["G6"]["gate"]["checklist"]
    assert cl == {"required": ["G6-A3", "G6-A4"], "confirmed": ["G6-A3", "G6-A4"]}
    assert validate_state(state) == []


def test_gate_checklist_roundtrips_through_save_load(tmp_path):
    state = sm.init_state("acme")
    _to_g2(state)
    sm.set_gate(state, "G2", "proceed", "ok",
                required=["G2-A1"], confirmed=["G2-A1"])
    path = tmp_path / "state.json"
    sm.save(state, path)
    resumed = sm.load(path)
    assert resumed["stages"]["G2"]["gate"]["checklist"]["required"] == ["G2-A1"]
