"""Tests for gate_review — workspace tickable copy + confirmed-required reader.

The orchestrator gate writes a tickable copy of the canonical checklist into the
run workspace, the reviewer ticks `- [x]`, and Approve reads back which *required*
items are ticked to feed `state_manager.set_gate(confirmed=...)`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import gate_review as gr  # noqa: E402

# Canonical-shaped fixture: G6-A1 (required, pre-ticked), G6-A2 (not required),
# G6-C1 (required, unticked). Mirrors a real checklist's structure.
CANONICAL = """---
gate: G6
role: "BrSE/BA"
decisions: { proceed: proceed, revise: adjust, abort: null }
required: [G6-A1, G6-C1]
---

# [G6] Checklist

## A
- [x] [G6-A1] **First** — desc. Tiêu chí: phải có X.
- [ ] [G6-A2] **Second** — desc.

## C
- [ ] [G6-C1] **Closing** — desc.
"""


def _canonical(tmp_path: Path) -> Path:
    p = tmp_path / "g6-canonical.md"
    p.write_text(CANONICAL, encoding="utf-8")
    return p


def test_write_copy_resets_checkboxes_and_keeps_content(tmp_path):
    dest = tmp_path / "ws" / "gate-G6-checklist.md"
    out = gr.write_workspace_copy(_canonical(tmp_path), dest)
    assert out == dest and dest.exists()
    text = dest.read_text(encoding="utf-8")
    # every item reset to unchecked
    assert "- [x]" not in text and "- [X]" not in text
    assert "- [ ] [G6-A1]" in text
    # body content (criteria) preserved verbatim
    assert "Tiêu chí: phải có X." in text
    assert "required: [G6-A1, G6-C1]" in text


def test_write_copy_no_overwrite_keeps_user_ticks(tmp_path):
    dest = tmp_path / "ws" / "gate-G6-checklist.md"
    gr.write_workspace_copy(_canonical(tmp_path), dest)
    # reviewer ticks a box
    dest.write_text(dest.read_text().replace("- [ ] [G6-C1]", "- [x] [G6-C1]"), encoding="utf-8")
    # second call must NOT clobber the tick
    gr.write_workspace_copy(_canonical(tmp_path), dest)
    assert "- [x] [G6-C1]" in dest.read_text(encoding="utf-8")


def test_read_confirmed_returns_only_ticked_required(tmp_path):
    dest = tmp_path / "ws" / "gate-G6-checklist.md"
    gr.write_workspace_copy(_canonical(tmp_path), dest)  # all reset
    # tick one required (G6-A1) and one NON-required (G6-A2); leave required G6-C1 off
    t = dest.read_text()
    t = t.replace("- [ ] [G6-A1]", "- [x] [G6-A1]").replace("- [ ] [G6-A2]", "- [x] [G6-A2]")
    dest.write_text(t, encoding="utf-8")
    confirmed = gr.read_confirmed(dest)
    assert confirmed == ["G6-A1"]  # only required AND ticked; G6-A2 excluded, G6-C1 unticked


def test_cli_write_then_confirmed(tmp_path, capsys):
    canonical = _canonical(tmp_path)
    dest = tmp_path / "ws" / "gate-G6-checklist.md"
    assert gr.main(["write", "--canonical", str(canonical), "--dest", str(dest)]) == 0
    dest.write_text(dest.read_text().replace("- [ ] [G6-A1]", "- [x] [G6-A1]"), encoding="utf-8")
    capsys.readouterr()  # clear
    assert gr.main(["confirmed", "--path", str(dest)]) == 0
    out = capsys.readouterr().out.strip()
    assert json.loads(out) == ["G6-A1"]


def test_cli_write_by_gate_resolves_canonical(tmp_path):
    """`write --gate G2` resolves the real canonical checklist (no path needed)."""
    dest = tmp_path / "ws" / "gate-G2-checklist.md"
    assert gr.main(["write", "--gate", "G2", "--dest", str(dest)]) == 0
    assert dest.exists()
    text = dest.read_text(encoding="utf-8")
    # No ticked G2 *item box* remains; a real G2 item is present and unticked.
    # (Substring "- [x]" can legitimately appear in header prose, so match item lines.)
    assert "- [x] [G2-" not in text
    assert "- [ ] [G2-A1]" in text
