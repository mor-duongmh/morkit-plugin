"""Tests for orchestrator infrastructure: lock_manager, dispatch_coordinator, aggregate_report."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))

from aggregate_report import collect_screen_specs, collect_stats, render_report  # noqa: E402
from dispatch_coordinator import SCOPES, filter_delta  # noqa: E402
from lib.normalized_schema import (  # noqa: E402
    ApiSpec,
    Change,
    Database,
    Delta,
    Endpoint,
    FunctionalRequirement,
    Priority,
    ProjectMeta,
    ProjectModel,
    SourceRef,
    Table,
    Column,
)
from lock_manager import acquire, is_locked, release  # noqa: E402


# --- lock_manager ---


def test_lock_acquire_and_release_cycle():
    with tempfile.TemporaryDirectory() as td:
        lock = Path(td) / ".docs-hero.lock"

        assert not lock.exists()
        assert acquire(lock) is True
        assert lock.exists()

        # Already held by current PID — peers should see locked=True
        locked, _ = is_locked(lock)
        assert locked is True

        release(lock)
        assert not lock.exists()


def test_lock_acquire_when_no_existing_lock():
    with tempfile.TemporaryDirectory() as td:
        lock = Path(td) / ".docs-hero.lock"
        # First acquire
        assert acquire(lock) is True
        # Lock payload is JSON with our pid
        data = json.loads(lock.read_text())
        assert data["pid"] == os.getpid()
        release(lock)


def test_is_locked_treats_dead_pid_as_stale():
    with tempfile.TemporaryDirectory() as td:
        lock = Path(td) / ".docs-hero.lock"
        # Write a lock file with a guaranteed-dead PID (PID 1 is the init process,
        # which is alive — use very high PID instead)
        lock.write_text(json.dumps({
            "pid": 999999999,
            "acquired_at": "2026-05-04T00:00:00+00:00",
            "host": "test",
        }))
        locked, reason = is_locked(lock)
        assert locked is False
        assert "stale" in reason


def test_is_locked_treats_old_timestamp_as_stale():
    with tempfile.TemporaryDirectory() as td:
        lock = Path(td) / ".docs-hero.lock"
        lock.write_text(json.dumps({
            "pid": os.getpid(),  # alive
            "acquired_at": "2020-01-01T00:00:00+00:00",  # ancient
            "host": "test",
        }))
        locked, reason = is_locked(lock)
        assert locked is False
        assert "stale" in reason


def test_is_locked_no_file_returns_false():
    locked, reason = is_locked(Path("/nonexistent/lock"))
    assert locked is False
    assert reason == "no lock"


def test_release_no_op_when_held_by_other_pid():
    with tempfile.TemporaryDirectory() as td:
        lock = Path(td) / ".docs-hero.lock"
        # Foreign PID
        lock.write_text(json.dumps({
            "pid": 999999998,
            "acquired_at": "2026-05-04T00:00:00+00:00",
            "host": "test",
        }))
        release(lock)  # should not delete (different PID)
        assert lock.exists()


# --- dispatch_coordinator: filter_delta ---


def _make_delta(types: list[str]) -> Delta:
    return Delta(
        source_type="plan",
        source_path="x.md",
        changes=[
            Change(op="ADD", entity_type=t, entity_id=f"{t}-001", payload=None,
                   reason=None)
            for t in types
        ],
    )


def test_filter_srs_scope_keeps_fr_nfr_screen_data_int():
    delta = _make_delta(["FR", "NFR", "SCREEN", "DATA", "INT", "ENDPOINT", "TABLE"])
    out = filter_delta(delta, SCOPES["srs"])
    types = [c.entity_type for c in out.changes]
    assert set(types) == {"FR", "NFR", "SCREEN", "DATA", "INT"}


def test_filter_api_scope_keeps_only_api_types():
    delta = _make_delta(["FR", "ENDPOINT", "ERROR_CODE", "WEBHOOK", "TABLE"])
    out = filter_delta(delta, SCOPES["api"])
    types = [c.entity_type for c in out.changes]
    assert set(types) == {"ENDPOINT", "ERROR_CODE", "WEBHOOK"}


def test_filter_db_scope_keeps_only_db_types():
    delta = _make_delta(["FR", "TABLE", "INDEX", "REL", "ENUM", "ENDPOINT"])
    out = filter_delta(delta, SCOPES["db"])
    types = [c.entity_type for c in out.changes]
    assert set(types) == {"TABLE", "INDEX", "REL", "ENUM"}


def test_filter_preserves_source_metadata():
    delta = _make_delta(["FR"])
    out = filter_delta(delta, SCOPES["srs"])
    assert out.source_type == delta.source_type
    assert out.source_path == delta.source_path


def test_filter_empty_when_no_match():
    delta = _make_delta(["TABLE", "INDEX"])
    out = filter_delta(delta, SCOPES["api"])
    assert out.changes == []


def test_scopes_are_disjoint():
    """SRS / API / DB scopes must not overlap — otherwise filter_delta would dispatch
    the same change to two skills, double-applying it."""
    srs, api, db = SCOPES["srs"], SCOPES["api"], SCOPES["db"]
    assert srs.isdisjoint(api)
    assert srs.isdisjoint(db)
    assert api.isdisjoint(db)


# --- aggregate_report ---


def test_collect_stats_handles_missing_docs():
    with tempfile.TemporaryDirectory() as td:
        stats = collect_stats(Path(td))
        for ds in stats:
            assert ds.exists is False
            assert ds.line_count == 0


def test_collect_stats_counts_h3_anchors():
    with tempfile.TemporaryDirectory() as td:
        docs = Path(td)
        (docs / "srs.md").write_text(
            "# SRS\n\n"
            "### FR-001: Login\nbody\n\n"
            "### FR-002: Logout\nbody\n\n"
            "### NFR-001\nbody\n\n",
            encoding="utf-8",
        )
        (docs / "api-docs.md").write_text(
            "# API\n\n"
            "### ENDPOINT-GET-users: get\n\n"
            "### ENDPOINT-POST-users: create\n\n",
            encoding="utf-8",
        )
        stats = collect_stats(docs)
        srs = next(s for s in stats if s.name == "srs.md")
        assert srs.exists
        assert srs.counts["FR"] == 2
        assert srs.counts["NFR"] == 1

        api = next(s for s in stats if s.name == "api-docs.md")
        assert api.counts["ENDPOINT"] == 2


def test_collect_screen_specs_globs_correctly():
    with tempfile.TemporaryDirectory() as td:
        docs = Path(td)
        spec_dir = docs / "screen-specs"
        spec_dir.mkdir()
        (spec_dir / "SCREEN-001-login.md").write_text("# Login")
        (spec_dir / "SCREEN-002-dashboard.md").write_text("# Dash")
        (spec_dir / "README.md").write_text("# misc")  # should be ignored
        specs = collect_screen_specs(docs)
        assert len(specs) == 2
        assert all("SCREEN-" in s.name for s in specs)


def test_render_report_marks_missing_docs():
    with tempfile.TemporaryDirectory() as td:
        text = render_report(Path(td))
        assert "missing" in text
        assert "srs.md" in text
        assert "api-docs.md" in text
        assert "database-design.md" in text


def test_render_report_includes_health_section():
    with tempfile.TemporaryDirectory() as td:
        text = render_report(Path(td))
        assert "Health Check" in text


def test_render_report_passes_when_all_docs_have_anchors():
    """Health check passes when each doc has ≥ 30 lines and a primary anchor."""
    body = "lorem ipsum body line\n" * 40  # plenty of lines
    with tempfile.TemporaryDirectory() as td:
        docs = Path(td)
        (docs / "srs.md").write_text(
            "# SRS\n\n" + ("### FR-001\n" * 3) + body, encoding="utf-8"
        )
        (docs / "api-docs.md").write_text(
            "# API\n\n" + ("### ENDPOINT-GET-x\n" * 3) + body, encoding="utf-8"
        )
        (docs / "database-design.md").write_text(
            "# DB\n\n" + ("### TBL-001\n" * 2) + body, encoding="utf-8"
        )
        text = render_report(docs)
        assert "All checks passed" in text
