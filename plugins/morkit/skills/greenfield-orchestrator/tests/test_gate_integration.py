"""Integration: real checklist `required` (loader) drives the state guard.

Proves the wire P3 asks the orchestrator to run: load required ids from the
canonical checklist, record them on the gate with the reviewer's confirmed set,
and let `advance` enforce — missing one blocks, all confirmed passes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import checklist_loader as cl  # noqa: E402
import gate_review as gr  # noqa: E402
import state_manager as sm  # noqa: E402

CANONICAL_DIR = Path(__file__).resolve().parents[1] / "references" / "gate-checklists"


def _drive_to(state, target):
    """Advance to `target`, clearing earlier gates with a full proceed."""
    while state["stage"] != target:
        cur = state["stage"]
        if cur in sm.GATED_STAGES:
            req = cl.load(cl.find_gate(cur, CANONICAL_DIR))["required"]
            sm.set_gate(state, cur, "proceed", "ok", required=req, confirmed=req)
        sm.advance(state)


def test_g2_missing_required_blocks_then_full_confirm_passes():
    required = cl.load(cl.find_gate("G2", CANONICAL_DIR))["required"]
    assert required, "G2 must declare a required subset"

    state = sm.init_state("demo", "brse", "JP")
    _drive_to(state, "G2")

    # Reviewer confirms all but the last required item → blocked.
    partial = required[:-1]
    sm.set_gate(state, "G2", "proceed", "partial", required=required, confirmed=partial)
    with pytest.raises(sm.GateNotPassed, match=required[-1]):
        sm.advance(state)
    assert state["stage"] == "G2"  # stayed put

    # Confirm the full required subset → advances.
    sm.set_gate(state, "G2", "proceed", "all met", required=required, confirmed=required)
    sm.advance(state)
    assert state["stage"] == "G3"


def test_g6_required_subset_enforced_end_to_end():
    required = cl.load(cl.find_gate("G6", CANONICAL_DIR))["required"]
    state = sm.init_state("demo", "brse", "JP")
    _drive_to(state, "G6")
    sm.set_gate(state, "G6", "proceed", "missing one",
                required=required, confirmed=required[1:])
    with pytest.raises(sm.GateNotPassed):
        sm.advance(state)
    sm.set_gate(state, "G6", "proceed", "all met", required=required, confirmed=required)
    sm.advance(state)
    assert state["stage"] == "G7"


def _tick(path: Path, ids) -> None:
    """Tick the given item ids in a workspace checklist copy."""
    text = path.read_text(encoding="utf-8")
    for i in ids:
        text = text.replace(f"- [ ] [{i}]", f"- [x] [{i}]")
    path.write_text(text, encoding="utf-8")


def test_filebased_approve_blocks_then_passes(tmp_path):
    """File-based flow: workspace copy → tick required → confirmed feeds the guard.

    Proves the file-based gate (write copy + read_confirmed) drives the SAME
    unchanged `set_gate`/`advance` guard: missing a required tick blocks, ticking
    all required advances. No multiSelect involved.
    """
    canonical = cl.find_gate("G2", CANONICAL_DIR)
    required = cl.load(canonical)["required"]
    dest = tmp_path / "ws" / "gate-G2-checklist.md"
    gr.write_workspace_copy(canonical, dest)

    state = sm.init_state("demo", "brse", "JP")
    _drive_to(state, "G2")

    # Reviewer ticks all required but the last → blocked.
    _tick(dest, required[:-1])
    confirmed = gr.read_confirmed(dest)
    assert confirmed == required[:-1]
    sm.set_gate(state, "G2", "proceed", "partial", required=required, confirmed=confirmed)
    with pytest.raises(sm.GateNotPassed, match=required[-1]):
        sm.advance(state)
    assert state["stage"] == "G2"

    # Tick the last required → read_confirmed now complete → advances.
    _tick(dest, [required[-1]])
    confirmed = gr.read_confirmed(dest)
    assert set(confirmed) == set(required)
    sm.set_gate(state, "G2", "proceed", "all met", required=required, confirmed=confirmed)
    sm.advance(state)
    assert state["stage"] == "G3"


def test_update_docs_adjust_persists_note_and_holds_gate():
    """`Update docs` → set_gate adjust + note: gate does NOT advance, note persists.

    The Update path hands off to /morkit:brainstorm via state.json (not a nested
    call). It must (a) leave the stage put so the run is resumable, and (b) keep
    the note so brainstorm/resume can read what to change.
    """
    state = sm.init_state("demo", "brse", "JP")
    _drive_to(state, "G3")
    sm.set_gate(state, "G3", "adjust", note="cần thêm ngưỡng NFR cho mục X")
    with pytest.raises(sm.GateNotPassed):
        sm.advance(state)
    assert state["stage"] == "G3"  # stayed put → resumable
    assert state["stages"]["G3"]["gate"]["note"] == "cần thêm ngưỡng NFR cho mục X"
    assert state["stages"]["G3"]["gate"]["decision"] == "adjust"
