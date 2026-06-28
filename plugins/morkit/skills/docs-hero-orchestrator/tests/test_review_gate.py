"""Tests for review_gate.py: render-to-staging, snapshot, surface, promote.

Keystone invariant: promote writes the PRE-edit render baseline into meta so
review-time edits register as `manual_edit` (locked end-to-end in Phase 3).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))
_TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TESTS))

import review_gate  # noqa: E402
from detect_manual_edits import detect_manual_edits  # noqa: E402
from lib.canonicalize import compute_hash  # noqa: E402
from lib.diff_schema import load_meta  # noqa: E402
from lib.markdown_ast import parse_doc  # noqa: E402
from lib.normalized_schema import save_project_model  # noqa: E402
from test_e2e import _build_full_model  # noqa: E402

PYTHON = sys.executable
DISPATCH = _ORCH / "dispatch_coordinator.py"

# Staged render with two endpoints; "## Endpoints" is an un-anchored heading.
SAMPLE_API_STAGED = """# API Docs

## Endpoints

### GET /users
Returns a paginated list of users.

### POST /users
Creates a user.
"""

# Existing doc on disk: GET has a different body, DELETE present, POST absent.
SAMPLE_API_EXISTING = """# API Docs

## Endpoints

### GET /users
Returns users.

### DELETE /users
Deletes a user.
"""


def _staged(td: Path, name: str, text: str) -> Path:
    staging = td / ".tmp" / "staged"
    staging.mkdir(parents=True, exist_ok=True)
    p = staging / name
    p.write_text(text, encoding="utf-8")
    return p


# --- render-to-staging ---


def test_render_to_staging_leaves_docs_untouched(tmp_path):
    """dispatch init --docs-dir <staging> must not touch docs/."""
    model = tmp_path / "pm.json"
    save_project_model(_build_full_model(), model)
    docs = tmp_path / "docs"
    docs.mkdir()
    staging = tmp_path / ".tmp" / "staged"
    res = subprocess.run(
        [PYTHON, str(DISPATCH), "init", "--project-model", str(model),
         "--outputs", "api", "--docs-dir", str(staging)],
        capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    assert (staging / "api-docs.md").exists(), "staged render missing"
    assert not any(docs.iterdir()), "docs/ must stay untouched during staged render"


# --- snapshot ---


def test_snapshot_records_preedit_baseline(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    meta_path = docs / ".docs-hero-meta.json"
    staged = _staged(tmp_path, "api-docs.md", SAMPLE_API_STAGED)

    review_gate.snapshot(staged, "api-docs.md", meta_path)

    meta = load_meta(meta_path)
    rs = meta.review["api-docs.md"]
    assert rs.status == "pending"
    blocks = parse_doc(SAMPLE_API_STAGED)
    assert set(rs.baseline_order) == set(blocks.keys())
    for sid, blk in blocks.items():
        assert rs.baseline_hashes[sid] == compute_hash(blk.body_md)


# --- surface ---


def test_surface_lists_sections_and_diff(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "api-docs.md").write_text(SAMPLE_API_EXISTING, encoding="utf-8")
    staged = _staged(tmp_path, "api-docs.md", SAMPLE_API_STAGED)

    out = review_gate.surface(staged, "api-docs.md", docs)

    titles = [s["title"] for s in out["sections"]]
    assert "Endpoints" in titles       # un-anchored heading still listed
    assert "GET /users" in titles
    assert out["exists"] is True
    assert "ENDPOINT-POST-users" in out["diff"]["added"]
    assert "ENDPOINT-DELETE-users" in out["diff"]["removed"]
    assert "ENDPOINT-GET-users" in out["diff"]["modified"]


def test_surface_no_existing_doc_all_added(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    staged = _staged(tmp_path, "api-docs.md", SAMPLE_API_STAGED)

    out = review_gate.surface(staged, "api-docs.md", docs)
    assert out["exists"] is False
    assert "ENDPOINT-GET-users" in out["diff"]["added"]
    assert out["diff"]["removed"] == []


# --- promote ---


def test_promote_copies_edited_doc_but_keeps_preedit_baseline(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    meta_path = docs / ".docs-hero-meta.json"
    staged = _staged(tmp_path, "api-docs.md", SAMPLE_API_STAGED)

    # snapshot BEFORE the reviewer edits
    review_gate.snapshot(staged, "api-docs.md", meta_path)

    edited = SAMPLE_API_STAGED.replace(
        "Returns a paginated list of users.", "Returns a paginated list of ACTIVE users."
    )
    staged.write_text(edited, encoding="utf-8")

    review_gate.promote(staged, "api-docs.md", docs, meta_path)

    # promoted content = the reviewer-edited staging file
    assert (docs / "api-docs.md").read_text(encoding="utf-8") == edited

    meta = load_meta(meta_path)
    # meta stores PRE-edit hash, not the edited one
    pre_blocks = parse_doc(SAMPLE_API_STAGED)
    assert (
        meta.docs["api-docs.md"].section_hashes["ENDPOINT-GET-users"]
        == compute_hash(pre_blocks["ENDPOINT-GET-users"].body_md)
    )
    assert meta.review["api-docs.md"].status == "approved"


def test_promote_baseline_flags_review_edit_as_manual(tmp_path):
    """Integration: detect_manual_edits sees the review-time edit as manual_edit."""
    docs = tmp_path / "docs"
    docs.mkdir()
    meta_path = docs / ".docs-hero-meta.json"
    staged = _staged(tmp_path, "api-docs.md", SAMPLE_API_STAGED)

    review_gate.snapshot(staged, "api-docs.md", meta_path)
    edited = SAMPLE_API_STAGED.replace(
        "Returns a paginated list of users.", "Returns a paginated list of ACTIVE users."
    )
    staged.write_text(edited, encoding="utf-8")
    review_gate.promote(staged, "api-docs.md", docs, meta_path)

    report = detect_manual_edits(docs / "api-docs.md", meta_path)
    statuses = {s.section_id: s.status for s in report.sections}
    assert statuses["ENDPOINT-GET-users"] == "manual_edit"
    assert statuses["ENDPOINT-POST-users"] == "clean"
