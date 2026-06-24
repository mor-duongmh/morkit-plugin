"""Tests for the shared Mor HTML theme library (lib/html_theme)."""
from __future__ import annotations

import sys
from pathlib import Path

_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))

from lib.html_theme import (  # noqa: E402
    Heading,
    build_nav,
    colorize_badges,
    slugify,
    wrap_document,
)


# --- slugify ---


def test_slugify_basic_and_vietnamese():
    assert slugify("1. Tổng quan") == slugify("1. Tổng quan")  # deterministic
    s = slugify("3. Yêu cầu chức năng")
    assert s and " " not in s and s == s.lower()


def test_slugify_unique_stable():
    # same input → same slug (anchors and nav must agree)
    assert slugify("Appendix A: Danh sách") == slugify("Appendix A: Danh sách")


# --- build_nav ---


def test_build_nav_includes_only_h2_in_order():
    heads = [
        Heading(1, "PropCity SRS", "propcity-srs"),
        Heading(2, "1. Tổng quan", "s1"),
        Heading(3, "FR-001 Login", "fr-001"),
        Heading(2, "2. Hiện trạng", "s2"),
    ]
    nav = build_nav(heads)
    assert 'href="#s1"' in nav
    assert 'href="#s2"' in nav
    # H1 and H3 are not nav entries
    assert 'href="#propcity-srs"' not in nav
    assert 'href="#fr-001"' not in nav
    # order preserved: s1 before s2
    assert nav.index('href="#s1"') < nav.index('href="#s2"')


def test_build_nav_extracts_leading_number():
    nav = build_nav([Heading(2, "7. Định nghĩa dữ liệu", "s7")])
    assert ">7<" in nav  # section number chip


# --- colorize_badges ---


def test_colorize_impl_status_emoji():
    html = "<table><tr><td>🟢 Done</td><td>🔴 Blocked</td></tr></table>"
    out = colorize_badges(html)
    assert 'class="badge ok"' in out
    assert 'class="badge danger"' in out


def test_colorize_priority_words_cell_scoped():
    html = "<td>MUST</td><td>SHOULD</td><td>LOW</td>"
    out = colorize_badges(html)
    assert 'class="badge must"' in out
    assert 'class="badge should"' in out
    assert 'class="badge low"' in out


def test_colorize_does_not_touch_prose():
    # "must" inside prose (not a whole-cell token) stays untouched
    html = "<p>The system must handle errors.</p>"
    assert colorize_badges(html) == html


# --- wrap_document ---


def test_wrap_document_is_self_contained_with_mor_tokens():
    doc = wrap_document("PropCity SRS", "<h2 id='s1'>1. Tổng quan</h2>", "<nav></nav>", lang="vi")
    assert "<!DOCTYPE html>" in doc
    assert "--mor-blue:#016DD0" in doc
    assert "--mor-navy:#0E1A4B" in doc
    assert "--mor-gold:#F5AE18" in doc
    assert "PropCity SRS" in doc          # title used
    assert "1. Tổng quan" in doc          # body embedded
    assert "@media print" in doc          # print-safe rules present
    assert 'lang="vi"' in doc


def test_wrap_document_embeds_nav_and_scripts():
    doc = wrap_document("T", "<p>body</p>", '<nav class="nav"><a href="#x">X</a></nav>')
    assert 'href="#x"' in doc            # nav embedded
    assert "<script" in doc              # scrollspy/progress JS present
    assert 'id="progress"' in doc        # progress bar element
