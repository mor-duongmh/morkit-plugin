"""Tests for parse_openspec.py."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from parse_openspec import list_changes, parse_openspec_change  # noqa: E402

# Sample delta spec (OpenSpec convention)
SAMPLE_SPEC = """# Auth Spec Delta

## ADDED Requirements

### Requirement: System SHALL support OAuth2 login

#### Scenario: User logs in with Google
- WHEN user clicks "Login with Google"
- AND user authorizes the app
- THEN user is redirected to dashboard
- AND a session is created

### Requirement: System SHALL validate access tokens

#### Scenario: Token validation
- WHEN API receives request with bearer token
- THEN validate signature
- AND check expiry

## MODIFIED Requirements

### Requirement: User authentication

#### Scenario: Updated login flow
- WHEN credentials submitted
- THEN check rate limit
- AND validate

## REMOVED Requirements

### Requirement: Legacy session cookies

#### Scenario: Cookie-based session
- (deprecated)
"""


def _build_change_folder(tmpdir: Path, change_name: str, spec_content: str) -> Path:
    base = tmpdir / "openspec" / "changes" / change_name
    (base / "specs").mkdir(parents=True)
    (base / "proposal.md").write_text("# Why\n\nAdd OAuth.\n", encoding="utf-8")
    (base / "specs" / "auth.md").write_text(spec_content, encoding="utf-8")
    return tmpdir / "openspec"


def test_list_changes_empty_dir():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "openspec"
        assert list_changes(p) == []


def test_list_changes_finds_folders():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "openspec" / "changes" / "change-001-foo").mkdir(parents=True)
        (tmp / "openspec" / "changes" / "change-002-bar").mkdir(parents=True)
        result = list_changes(tmp / "openspec")
        assert result == ["change-001-foo", "change-002-bar"]


def test_parse_added_requirements():
    with tempfile.TemporaryDirectory() as td:
        openspec_dir = _build_change_folder(Path(td), "change-001-add-oauth", SAMPLE_SPEC)
        delta = parse_openspec_change(openspec_dir, "change-001-add-oauth")

    assert delta.source_type == "openspec"
    add_changes = [c for c in delta.changes if c.op == "ADD"]
    assert len(add_changes) == 2
    assert add_changes[0].entity_type == "FR"
    assert add_changes[0].payload["name"] == "System SHALL support OAuth2 login"


def test_parse_modified_requirements():
    with tempfile.TemporaryDirectory() as td:
        openspec_dir = _build_change_folder(Path(td), "change-001", SAMPLE_SPEC)
        delta = parse_openspec_change(openspec_dir, "change-001")
    update_changes = [c for c in delta.changes if c.op == "UPDATE"]
    assert len(update_changes) == 1
    assert update_changes[0].payload["name"] == "User authentication"


def test_parse_removed_requirements():
    with tempfile.TemporaryDirectory() as td:
        openspec_dir = _build_change_folder(Path(td), "change-001", SAMPLE_SPEC)
        delta = parse_openspec_change(openspec_dir, "change-001")
    deprecate_changes = [c for c in delta.changes if c.op == "DEPRECATE"]
    assert len(deprecate_changes) == 1


def test_scenarios_become_main_flow():
    with tempfile.TemporaryDirectory() as td:
        openspec_dir = _build_change_folder(Path(td), "change-001", SAMPLE_SPEC)
        delta = parse_openspec_change(openspec_dir, "change-001")
    first_add = next(c for c in delta.changes if c.op == "ADD")
    main_flow = first_add.payload.get("main_flow", [])
    assert any("Google" in step for step in main_flow)
    assert any("redirected to dashboard" in step for step in main_flow)


def test_missing_change_raises():
    with tempfile.TemporaryDirectory() as td:
        try:
            parse_openspec_change(Path(td) / "openspec", "nonexistent")
            assert False, "Should raise"
        except FileNotFoundError:
            pass


def test_empty_change_folder_returns_empty_delta():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td) / "openspec" / "changes" / "empty-change"
        base.mkdir(parents=True)
        delta = parse_openspec_change(Path(td) / "openspec", "empty-change")
    assert delta.changes == []
