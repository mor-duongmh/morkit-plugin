"""Tests for review-state accessors used by the brownfield init resume loop."""
from __future__ import annotations

import sys
from pathlib import Path

_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))

from meta_manager import (  # noqa: E402
    get_review_state,
    list_pending,
    set_review_state,
)

CODE_DERIVED = [
    "system-architecture.md",
    "database-design.md",
    "codebase-summary.md",
    "code-standards.md",
    "api-docs.md",
]


def test_get_review_state_missing_is_none(tmp_path):
    meta = tmp_path / ".docs-hero-meta.json"
    assert get_review_state(meta, "api-docs.md") is None


def test_set_then_get_review_state(tmp_path):
    meta = tmp_path / ".docs-hero-meta.json"
    set_review_state(meta, "api-docs.md", "approved")
    assert get_review_state(meta, "api-docs.md") == "approved"


def test_set_review_state_preserves_existing_baseline(tmp_path):
    """Flipping status must not wipe the snapshot baseline."""
    from lib.diff_schema import load_meta
    import review_gate

    meta = tmp_path / ".docs-hero-meta.json"
    staged = tmp_path / "api-docs.md"
    staged.write_text(
        "# API\n\n### GET /users\nReturns users.\n", encoding="utf-8"
    )
    review_gate.snapshot(staged, "api-docs.md", meta)
    set_review_state(meta, "api-docs.md", "approved")

    rs = load_meta(meta).review["api-docs.md"]
    assert rs.status == "approved"
    assert "ENDPOINT-GET-users" in rs.baseline_hashes


def test_list_pending_filters_approved(tmp_path):
    meta = tmp_path / ".docs-hero-meta.json"
    set_review_state(meta, "api-docs.md", "approved")
    set_review_state(meta, "code-standards.md", "pending")

    pending = list_pending(meta, CODE_DERIVED)
    assert "api-docs.md" not in pending          # approved → skipped on resume
    assert "code-standards.md" in pending          # explicitly pending
    assert "database-design.md" in pending          # never reviewed → pending


def test_list_pending_all_when_no_meta(tmp_path):
    meta = tmp_path / ".docs-hero-meta.json"
    pending = list_pending(meta, CODE_DERIVED)
    assert pending == CODE_DERIVED


def test_set_review_state_rejects_invalid_status(tmp_path):
    """Bad status must fail fast on write, not corrupt the meta for the next load."""
    import pytest

    meta = tmp_path / ".docs-hero-meta.json"
    with pytest.raises(ValueError):
        set_review_state(meta, "api-docs.md", "done")
    assert not meta.exists()  # nothing written
