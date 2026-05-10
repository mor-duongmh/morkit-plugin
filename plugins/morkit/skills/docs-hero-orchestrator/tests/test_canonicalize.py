"""Tests for lib/canonicalize.py."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib.canonicalize import canonicalize, compute_hash  # noqa: E402


def test_strips_bom():
    assert canonicalize("﻿hello") == "hello"


def test_normalizes_crlf_and_cr():
    assert canonicalize("a\r\nb\rc") == "a\nb\nc"


def test_strips_trailing_whitespace():
    assert canonicalize("foo   \nbar\t\n") == "foo\nbar"


def test_collapses_multiple_blank_lines():
    assert canonicalize("a\n\n\n\nb") == "a\n\nb"


def test_strips_html_comments():
    assert canonicalize("foo <!-- hidden --> bar") == "foo  bar"


def test_strips_outer_whitespace():
    assert canonicalize("\n\n  hello  \n\n") == "hello"


def test_preserves_indented_code_block():
    md = "```\n    indented\n    code\n```"
    assert "    indented" in canonicalize(md)


def test_hash_stable_across_whitespace_only_changes():
    a = "## FR-001\n\nDescription text."
    b = "## FR-001\n\nDescription text.\n   "  # Trailing whitespace
    c = "## FR-001\r\n\r\nDescription text."  # CRLF
    assert compute_hash(a) == compute_hash(b) == compute_hash(c)


def test_hash_changes_on_content():
    a = "## FR-001\n\nOld description."
    b = "## FR-001\n\nNew description."
    assert compute_hash(a) != compute_hash(b)


def test_hash_is_hex_string():
    h = compute_hash("anything")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)
