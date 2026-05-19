"""Tests for lib/id_allocator.py."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib.id_allocator import IdAllocator, parse_id  # noqa: E402


def test_parse_id_basic():
    assert parse_id("FR-007") == ("FR", 7)
    assert parse_id("SCREEN-099") == ("SCREEN", 99)


def test_parse_id_invalid_returns_none():
    assert parse_id("invalid") is None
    assert parse_id("FR-abc") is None
    assert parse_id("") is None


def test_allocator_empty_starts_at_1():
    a = IdAllocator()
    assert a.next("FR") == "FR-001"
    assert a.next("FR") == "FR-002"


def test_allocator_continues_from_existing():
    a = IdAllocator(existing_ids=["FR-001", "FR-005", "FR-002"])
    assert a.next("FR") == "FR-006"


def test_allocator_per_prefix_independent():
    a = IdAllocator(existing_ids=["FR-001", "SCREEN-005"])
    assert a.next("FR") == "FR-002"
    assert a.next("SCREEN") == "SCREEN-006"
    assert a.next("FR") == "FR-003"


def test_allocator_ignores_invalid_existing():
    a = IdAllocator(existing_ids=["not-an-id", "FR-001"])
    assert a.next("FR") == "FR-002"


def test_allocator_peek_does_not_bump():
    a = IdAllocator()
    assert a.peek("FR") == "FR-001"
    assert a.peek("FR") == "FR-001"  # Still 1
    assert a.next("FR") == "FR-001"  # Now committed


def test_allocator_reserve():
    a = IdAllocator()
    a.reserve("FR-010")
    assert a.next("FR") == "FR-011"


def test_allocator_custom_padding():
    a = IdAllocator()
    assert a.next("FR", pad=4) == "FR-0001"
    assert a.next("FR", pad=4) == "FR-0002"
