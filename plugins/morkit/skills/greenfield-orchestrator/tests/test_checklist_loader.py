"""Tests for checklist_loader — front-matter parsing + required-subset contract."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import checklist_loader as cl  # noqa: E402

CANONICAL_DIR = Path(__file__).resolve().parent.parent / "references" / "gate-checklists"

FIXTURE = """---
gate: G6
role: "BrSE/BA"
artifact: ["docs/srs.md", "docs/srs.html"]
decisions: { proceed: proceed, revise: adjust, abort: null }
required: [G6-A1, G6-C1]
---

# [G6] Checklist

## A
- [ ] [G6-A1] **First item** — desc. Tiêu chí: x.
- [ ] [G6-A2] **Second item** — desc.

## C
- [ ] [G6-C1] **Closing** — desc.
"""


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_parse_fixture(tmp_path):
    data = cl.load(_write(tmp_path, "g6-x.md", FIXTURE))
    assert data["gate"] == "G6"
    assert data["role"] == "BrSE/BA"
    assert data["artifact"] == ["docs/srs.md", "docs/srs.html"]
    assert data["decisions"] == {"proceed": "proceed", "revise": "adjust", "abort": None}
    assert data["required"] == ["G6-A1", "G6-C1"]
    assert [it["id"] for it in data["items"]] == ["G6-A1", "G6-A2", "G6-C1"]
    by_id = {it["id"]: it for it in data["items"]}
    assert by_id["G6-A1"]["required"] is True
    assert by_id["G6-A2"]["required"] is False
    assert by_id["G6-A1"]["title"] == "First item"


def test_dangling_required_raises(tmp_path):
    bad = FIXTURE.replace("required: [G6-A1, G6-C1]", "required: [G6-A1, G6-ZZ]")
    with pytest.raises(ValueError, match="not found"):
        cl.load(_write(tmp_path, "g6-x.md", bad))


def test_duplicate_id_raises(tmp_path):
    dup = FIXTURE.replace("[G6-A2] **Second item**", "[G6-A1] **Second item**")
    with pytest.raises(ValueError, match="duplicate"):
        cl.load(_write(tmp_path, "g6-x.md", dup))


def test_gate_filename_mismatch_raises(tmp_path):
    with pytest.raises(ValueError, match="filename gate"):
        cl.load(_write(tmp_path, "g2-x.md", FIXTURE))  # body says G6


def test_missing_front_matter_raises(tmp_path):
    with pytest.raises(ValueError, match="front-matter"):
        cl.load(_write(tmp_path, "g6-x.md", "# no front matter\n- [ ] [G6-A1] **x**"))


def test_invalid_decision_enum_raises(tmp_path):
    bad = FIXTURE.replace("abort: null", "abort: bogus")
    with pytest.raises(ValueError, match="decision"):
        cl.load(_write(tmp_path, "g6-x.md", bad))


# --- Contract over the 4 real canonical checklists ---

@pytest.mark.parametrize("gate", ["G2", "G3", "G4", "G6"])
def test_real_checklist_required_subset(gate):
    path = cl.find_gate(gate, CANONICAL_DIR)
    data = cl.load(path)
    assert data["gate"] == gate
    assert 1 <= len(data["required"]) <= 5, f"{gate}: required must be a small subset"
    ids = {it["id"] for it in data["items"]}
    assert set(data["required"]) <= ids, f"{gate}: dangling required ids"
    assert data["decisions"], f"{gate}: must declare decision->enum map"
