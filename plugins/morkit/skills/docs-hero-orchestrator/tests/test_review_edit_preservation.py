"""Lock the keystone invariant: a doc edited DURING review is not overwritten by
a later update/sync. Reuses the existing diff engine — no new merge logic.

Scenario: render v1 → snapshot → reviewer edits FR-001 in staging → promote →
update delta touches FR-001 + FR-002 → FR-001 keeps the reviewer edit (manual_edit
→ SKIP), FR-002 takes the new render (clean → REPLACE).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))

import review_gate  # noqa: E402
from apply_patch import apply_patch  # noqa: E402
from compute_diff import compute_diff  # noqa: E402
from detect_manual_edits import detect_manual_edits  # noqa: E402
from dispatch_coordinator import run_update  # noqa: E402
from lib.diff_schema import load_meta, save_meta  # noqa: E402
from lib.normalized_schema import Change, Delta, save_delta  # noqa: E402

SRS_V1 = """# SRS

## Functional Requirements

### FR-001: Login
- **Description:** User logs in with email + password.

### FR-002: Logout
- **Description:** User signs out.

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-06-01 | docs-hero | Initial |
"""

REVIEWER_MARK = "REVIEWER-NOTE: must keep 2FA caveat."
UPDATE_MARK = "UPDATED-BY-PIPELINE"


def _stage(td: Path, name: str, text: str) -> Path:
    staging = td / ".tmp" / "staged"
    staging.mkdir(parents=True, exist_ok=True)
    p = staging / name
    p.write_text(text, encoding="utf-8")
    return p


def _promote_with_review_edit(td: Path) -> tuple[Path, Path]:
    """Render v1 → snapshot → edit FR-001 → promote. Returns (doc, meta)."""
    docs = td / "docs"
    docs.mkdir()
    meta = docs / ".docs-hero-meta.json"
    staged = _stage(td, "srs.md", SRS_V1)

    review_gate.snapshot(staged, "srs.md", meta)

    # Reviewer edits FR-001 in staging BEFORE approving.
    edited = SRS_V1.replace(
        "- **Description:** User logs in with email + password.",
        "- **Description:** User logs in with email + password.\n- " + REVIEWER_MARK,
    )
    staged.write_text(edited, encoding="utf-8")

    review_gate.promote(staged, "srs.md", docs, meta)
    return docs / "srs.md", meta


def test_promote_marks_review_edit_as_manual():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        doc, meta = _promote_with_review_edit(Path(td))
        report = detect_manual_edits(doc, meta)
        st = {s.section_id: s.status for s in report.sections}
        assert st["FR-001"] == "manual_edit"   # reviewer edit registered
        assert st["FR-002"] == "clean"


def test_update_keeps_review_edit_updates_clean_section():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        doc, meta = _promote_with_review_edit(Path(td))

        # An upstream delta wants to rewrite BOTH FR-001 and FR-002.
        delta = Delta(
            source_type="plan",
            source_path="x",
            changes=[
                Change(op="UPDATE", entity_type="FR", entity_id="FR-001",
                       payload={"name": "Login", "description": UPDATE_MARK}),
                Change(op="UPDATE", entity_type="FR", entity_id="FR-002",
                       payload={"name": "Logout", "description": UPDATE_MARK}),
            ],
        )
        report = detect_manual_edits(doc, meta)
        plan = compute_diff(delta, report, current_version="1.0")
        ops = {op.section_id: op.op for op in plan.ops}
        assert ops["FR-001"] == "SKIP"        # manual edit preserved
        assert ops["FR-002"] == "REPLACE"     # clean section updated

        apply_patch(plan, doc, meta)
        final = doc.read_text(encoding="utf-8")

        # FR-001 still carries the reviewer's note; the pipeline rewrite skipped.
        assert REVIEWER_MARK in final
        fr001 = final.split("### FR-001")[1].split("### FR-002")[0]
        assert UPDATE_MARK not in fr001
        # FR-002 took the new render.
        fr002 = final.split("### FR-002")[1]
        assert UPDATE_MARK in fr002


def test_skip_review_no_promote_leaves_update_flow_unaffected():
    """Skipping review = no promote: doc absent from docs/ + meta.docs; update is a clean no-op."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        docs = tdp / "docs"
        docs.mkdir()
        meta = docs / ".docs-hero-meta.json"
        staged = _stage(tdp, "api-docs.md", "# API\n\n### GET /users\nReturns users.\n")

        review_gate.snapshot(staged, "api-docs.md", meta)
        # NOTE: no promote() — reviewer skipped it.

        m = load_meta(meta)
        assert "api-docs.md" not in m.docs            # never promoted
        assert m.review["api-docs.md"].status == "pending"
        assert not (docs / "api-docs.md").exists()    # docs/ untouched

        # An update targeting the un-promoted doc is a clean skip (existing behavior),
        # not a crash or a fabricated doc.
        delta = Delta(
            source_type="plan", source_path="x",
            changes=[Change(op="UPDATE", entity_type="ENDPOINT", entity_id="ENDPOINT-GET-users",
                            payload={"description": "x"})],
        )
        delta_path = tdp / ".tmp" / "delta.json"
        save_delta(delta, delta_path)
        results = run_update(delta_path, docs, meta, tdp / ".tmp")
        api_results = [r for r in results if r.name == "api"]
        assert api_results and not api_results[0].ok
        assert "doc missing" in api_results[0].message
        assert not (docs / "api-docs.md").exists()    # still not fabricated
