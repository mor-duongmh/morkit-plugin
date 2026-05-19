"""End-to-end tests for the diff engine: meta manager + detect + compute + apply."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_patch import apply_patch  # noqa: E402
from compute_diff import compute_diff  # noqa: E402
from detect_manual_edits import detect_manual_edits  # noqa: E402
from lib.diff_schema import (  # noqa: E402
    DocMeta,
    MetaSidecar,
    save_meta,
)
from lib.normalized_schema import Change, Delta  # noqa: E402
from meta_manager import rebuild_meta  # noqa: E402

# Sample SRS doc with FR-001, FR-002, FR-003
SAMPLE_SRS = """# SRS

## Functional Requirements

### FR-001: Login
- **Description:** User logs in with email + password.

### FR-002: Logout
- **Description:** User signs out.

### FR-003: Password Reset
- **Description:** Old password reset flow.

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-05-01 | docs-hero | Initial |
"""


def _setup_docs_dir(td: Path) -> tuple[Path, Path]:
    """Create docs/ with srs.md + .docs-hero-meta.json."""
    docs = td / "docs"
    docs.mkdir()
    srs = docs / "srs.md"
    srs.write_text(SAMPLE_SRS, encoding="utf-8")
    meta_path = docs / ".docs-hero-meta.json"
    rebuild_meta(docs, meta_path)
    return srs, meta_path


# --- meta_manager ---


def test_rebuild_meta_finds_all_sections():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        from lib.diff_schema import load_meta

        meta = load_meta(meta_path)
        doc_meta = meta.docs["srs.md"]
        assert set(doc_meta.section_hashes.keys()) == {"FR-001", "FR-002", "FR-003"}
        assert doc_meta.doc_version == "1.0"


def test_rebuild_meta_empty_dir_raises_or_empty():
    with tempfile.TemporaryDirectory() as td:
        empty = Path(td) / "empty"
        empty.mkdir()
        meta_path = empty / ".meta.json"
        meta = rebuild_meta(empty, meta_path)
        assert meta.docs == {}


# --- detect_manual_edits ---


def test_detect_clean_when_no_changes():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        report = detect_manual_edits(srs, meta_path)
        assert report.summary.clean == 3
        assert report.summary.manual_edit == 0


def test_detect_manual_edit():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        # Tamper with FR-002 description
        text = srs.read_text()
        text = text.replace("User signs out.", "User signs out and clears cache.")
        srs.write_text(text, encoding="utf-8")

        report = detect_manual_edits(srs, meta_path)
        edited = [s for s in report.sections if s.status == "manual_edit"]
        assert len(edited) == 1
        assert edited[0].section_id == "FR-002"


def test_detect_untracked_section():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        text = srs.read_text()
        text += "\n### FR-099: New manual section\n- Custom\n"
        srs.write_text(text, encoding="utf-8")

        report = detect_manual_edits(srs, meta_path)
        untracked = [s for s in report.sections if s.status == "untracked"]
        assert any(s.section_id == "FR-099" for s in untracked)


def test_detect_deleted_section():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        # Remove FR-003 entirely
        text = srs.read_text()
        text = text.replace(
            "### FR-003: Password Reset\n- **Description:** Old password reset flow.\n\n",
            "",
        )
        srs.write_text(text, encoding="utf-8")

        report = detect_manual_edits(srs, meta_path)
        deleted = [s for s in report.sections if s.status == "deleted_by_user"]
        assert any(s.section_id == "FR-003" for s in deleted)


# --- compute_diff ---


def test_compute_diff_add_new_fr():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        report = detect_manual_edits(srs, meta_path)
        delta = Delta(
            source_type="plan",
            source_path="x",
            changes=[
                Change(
                    op="ADD",
                    entity_type="FR",
                    entity_id="FR-008",
                    payload={"name": "OAuth Login", "description": "OAuth flow"},
                )
            ],
        )
        plan = compute_diff(delta, report, current_version="1.0")
        insert_ops = [op for op in plan.ops if op.op == "INSERT"]
        assert len(insert_ops) == 1
        assert insert_ops[0].section_id == "FR-008"
        assert plan.next_version == "1.1.0"


def test_compute_diff_update_skips_manual_edit():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        # Edit FR-001 manually
        text = srs.read_text().replace("User logs in", "User signs in")
        srs.write_text(text, encoding="utf-8")
        report = detect_manual_edits(srs, meta_path)

        delta = Delta(
            source_type="openspec",
            source_path="x",
            changes=[
                Change(
                    op="UPDATE",
                    entity_type="FR",
                    entity_id="FR-001",
                    payload={"description": "New description"},
                )
            ],
        )
        plan = compute_diff(delta, report, current_version="1.0")
        skip_ops = [op for op in plan.ops if op.op == "SKIP"]
        assert len(skip_ops) == 1
        assert skip_ops[0].section_id == "FR-001"
        assert len(plan.conflicts) == 1


def test_compute_diff_deprecate_breaking_bumps_major():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        report = detect_manual_edits(srs, meta_path)
        delta = Delta(
            source_type="plan",
            source_path="x",
            changes=[
                Change(op="DEPRECATE", entity_type="FR", entity_id="FR-003", reason="Replaced")
            ],
        )
        plan = compute_diff(delta, report, current_version="1.0")
        assert plan.next_version == "2.0.0"
        move_ops = [op for op in plan.ops if op.op == "MOVE_TO_APPENDIX"]
        assert len(move_ops) == 1


# --- apply_patch ---


def test_apply_insert_fr_appears_in_doc():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        report = detect_manual_edits(srs, meta_path)
        delta = Delta(
            source_type="plan",
            source_path="x",
            changes=[
                Change(
                    op="ADD",
                    entity_type="FR",
                    entity_id="FR-008",
                    payload={"name": "OAuth", "description": "OAuth flow"},
                )
            ],
        )
        plan = compute_diff(delta, report, current_version="1.0")
        apply_patch(plan, srs, meta_path)

        final_text = srs.read_text()
        assert "FR-008" in final_text
        assert "OAuth" in final_text
        # Original FRs intact
        assert "FR-001" in final_text
        assert "FR-002" in final_text


def test_apply_replace_keeps_id_changes_body():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        report = detect_manual_edits(srs, meta_path)
        delta = Delta(
            source_type="plan",
            source_path="x",
            changes=[
                Change(
                    op="UPDATE",
                    entity_type="FR",
                    entity_id="FR-001",
                    payload={"name": "Login", "description": "Updated login description"},
                )
            ],
        )
        plan = compute_diff(delta, report, current_version="1.0")
        apply_patch(plan, srs, meta_path)
        final_text = srs.read_text()
        assert "FR-001" in final_text
        assert "Updated login description" in final_text


def test_apply_deprecate_moves_to_appendix_z():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        report = detect_manual_edits(srs, meta_path)
        delta = Delta(
            source_type="plan",
            source_path="x",
            changes=[
                Change(op="DEPRECATE", entity_type="FR", entity_id="FR-003", reason="Replaced")
            ],
        )
        plan = compute_diff(delta, report, current_version="1.0")
        apply_patch(plan, srs, meta_path)
        final_text = srs.read_text()
        assert "Appendix Z" in final_text or "DEPRECATED" in final_text
        assert "[DEPRECATED v1.0]" in final_text


def test_apply_skip_preserves_user_edits():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        # User edits FR-002
        original = srs.read_text()
        edited = original.replace("User signs out.", "User signs out and clears tokens.")
        srs.write_text(edited, encoding="utf-8")

        report = detect_manual_edits(srs, meta_path)
        delta = Delta(
            source_type="plan",
            source_path="x",
            changes=[
                Change(
                    op="UPDATE",
                    entity_type="FR",
                    entity_id="FR-002",
                    payload={"description": "Different description from upstream"},
                )
            ],
        )
        plan = compute_diff(delta, report, current_version="1.0")
        apply_patch(plan, srs, meta_path)

        final_text = srs.read_text()
        # User's edit preserved
        assert "clears tokens" in final_text
        # Upstream description NOT applied
        assert "Different description from upstream" not in final_text


def test_apply_idempotent_replay():
    """Applying same plan twice → second apply is no-op (sections already match)."""
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        report = detect_manual_edits(srs, meta_path)
        delta = Delta(
            source_type="plan",
            source_path="x",
            changes=[
                Change(
                    op="ADD",
                    entity_type="FR",
                    entity_id="FR-099",
                    payload={"name": "Test"},
                )
            ],
        )
        plan = compute_diff(delta, report, current_version="1.0")
        apply_patch(plan, srs, meta_path)
        first = srs.read_text()

        # Re-detect after first apply, then run same delta
        report2 = detect_manual_edits(srs, meta_path)
        plan2 = compute_diff(delta, report2, current_version=plan.next_version)
        apply_patch(plan2, srs, meta_path)
        second = srs.read_text()

        # FR-099 still present, no duplicate
        assert second.count("FR-099") == first.count("FR-099")


def test_apply_atomic_writes_backup():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        report = detect_manual_edits(srs, meta_path)
        delta = Delta(
            source_type="plan",
            source_path="x",
            changes=[Change(op="ADD", entity_type="FR", entity_id="FR-050", payload={"name": "X"})],
        )
        plan = compute_diff(delta, report, current_version="1.0")
        apply_patch(plan, srs, meta_path)

        backup = srs.with_suffix(srs.suffix + ".bak")
        assert backup.exists()


def test_apply_dry_run_does_not_write():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        original = srs.read_text()
        report = detect_manual_edits(srs, meta_path)
        delta = Delta(
            source_type="plan",
            source_path="x",
            changes=[Change(op="ADD", entity_type="FR", entity_id="FR-077", payload={"name": "X"})],
        )
        plan = compute_diff(delta, report, current_version="1.0")
        result = apply_patch(plan, srs, meta_path, dry_run=True)
        # Dry run returns text containing FR-077, but file unchanged
        assert "FR-077" in result
        assert srs.read_text() == original


def test_apply_updates_meta_hashes():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        report = detect_manual_edits(srs, meta_path)
        delta = Delta(
            source_type="plan",
            source_path="x",
            changes=[Change(op="ADD", entity_type="FR", entity_id="FR-088", payload={"name": "X"})],
        )
        plan = compute_diff(delta, report, current_version="1.0")
        apply_patch(plan, srs, meta_path)

        from lib.diff_schema import load_meta

        meta = load_meta(meta_path)
        assert "FR-088" in meta.docs["srs.md"].section_hashes
        assert meta.docs["srs.md"].doc_version == plan.next_version


def test_apply_appends_revision_history_row():
    with tempfile.TemporaryDirectory() as td:
        srs, meta_path = _setup_docs_dir(Path(td))
        report = detect_manual_edits(srs, meta_path)
        delta = Delta(
            source_type="plan",
            source_path="x",
            changes=[Change(op="ADD", entity_type="FR", entity_id="FR-066", payload={"name": "X"})],
        )
        plan = compute_diff(delta, report, current_version="1.0")
        apply_patch(plan, srs, meta_path)

        final = srs.read_text()
        # Plan version 1.1.0 should be in revision history
        assert "1.1.0" in final
