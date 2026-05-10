"""Tests for parse_plan.py."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from parse_plan import parse_plan  # noqa: E402

STRICT_PLAN = """# Plan: Add OAuth

## Changes for SRS

### ADD FR-008: OAuth Login
- description: User can sign in via Google OAuth
- priority: High
- related_screens: [SCREEN-005]

### UPDATE FR-005
- field: description
- new_value: "Updated authentication flow"

### DEPRECATE FR-003
- reason: Replaced by FR-008

## Changes for Database

### ADD TABLE-002: oauth_tokens
- columns: [id, user_id, token, expires_at]

## Changes for API

### ADD ENDPOINT-001: POST /auth/oauth/callback
- description: OAuth callback endpoint
"""

LENIENT_PLAN = """# Plan with typos

## ADD FR-7: Logout
- description: User can sign out

### UPDATE: FR-005
- field: name
"""


def test_parse_strict_plan():
    with tempfile.TemporaryDirectory() as td:
        plan_path = Path(td) / "plan.md"
        plan_path.write_text(STRICT_PLAN)
        delta = parse_plan(plan_path)

    assert delta.source_type == "plan"
    assert len(delta.changes) >= 4

    add_fr = next(c for c in delta.changes if c.op == "ADD" and c.entity_type == "FR")
    assert add_fr.entity_id == "FR-008"
    assert add_fr.payload.get("name") == "OAuth Login"
    assert add_fr.payload.get("priority") == "High"
    assert add_fr.payload.get("related_screens") == ["SCREEN-005"]

    update_fr = next(c for c in delta.changes if c.op == "UPDATE" and c.entity_type == "FR")
    assert update_fr.entity_id == "FR-005"

    deprecate = next(c for c in delta.changes if c.op == "DEPRECATE")
    assert deprecate.entity_id == "FR-003"


def test_parse_table_change():
    with tempfile.TemporaryDirectory() as td:
        plan_path = Path(td) / "plan.md"
        plan_path.write_text(STRICT_PLAN)
        delta = parse_plan(plan_path)
    table_change = next(c for c in delta.changes if c.entity_type == "TABLE")
    assert table_change.entity_id == "TBL-002"
    assert table_change.op == "ADD"


def test_lenient_mode_handles_typos():
    """Heading level off-by-one + ID padding (FR-7 -> FR-007) auto-fixed."""
    with tempfile.TemporaryDirectory() as td:
        plan_path = Path(td) / "plan.md"
        plan_path.write_text(LENIENT_PLAN)
        delta = parse_plan(plan_path, strict=False)

    add = next(c for c in delta.changes if c.op == "ADD")
    assert add.entity_id == "FR-007"  # zero-padded


def test_strict_mode_rejects_typos():
    """Strict mode should not parse heading with wrong level."""
    with tempfile.TemporaryDirectory() as td:
        plan_path = Path(td) / "plan.md"
        plan_path.write_text(LENIENT_PLAN)
        delta = parse_plan(plan_path, strict=True)
    # Strict pattern requires exactly ### + 3-digit ID; LENIENT_PLAN has neither
    assert all(c.entity_id != "FR-007" for c in delta.changes)


def test_empty_plan_returns_empty_delta():
    with tempfile.TemporaryDirectory() as td:
        plan_path = Path(td) / "plan.md"
        plan_path.write_text("# Just a title\n\nNo changes.")
        delta = parse_plan(plan_path)
    assert delta.changes == []


def test_quoted_string_value():
    with tempfile.TemporaryDirectory() as td:
        plan_path = Path(td) / "plan.md"
        plan_path.write_text(STRICT_PLAN)
        delta = parse_plan(plan_path)
    update = next(c for c in delta.changes if c.op == "UPDATE")
    assert update.payload.get("new_value") == "Updated authentication flow"
