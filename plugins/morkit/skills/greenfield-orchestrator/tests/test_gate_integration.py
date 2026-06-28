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
