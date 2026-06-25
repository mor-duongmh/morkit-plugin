"""Tests for render_html.py — Markdown (srs.md) -> branded srs.html."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))

from render_html import render_html  # noqa: E402

_SCRIPT = _ORCH / "render_html.py"
_PYTHON = sys.executable

_SAMPLE_MD = """# PropCity SRS

## 1. Tổng quan

Đoạn mô tả.

## 3. Yêu cầu chức năng

| ID | Tên | Ưu tiên | Trạng thái |
|----|-----|---------|------------|
| FR-001 | Đăng nhập | MUST | 🟢 Done |
| FR-002 | Báo cáo | SHOULD | 🔴 Blocked |
"""


# --- pure function ---


def test_render_html_builds_self_contained_doc():
    out = render_html(_SAMPLE_MD, title="PropCity SRS", lang="vi")
    assert "<!DOCTYPE html>" in out
    assert "--mor-blue:#016DD0" in out
    assert "PropCity SRS" in out


def test_headings_get_ids_and_nav_links_match():
    out = render_html(_SAMPLE_MD, title="PropCity SRS")
    # every H2 becomes a nav link AND a body heading with matching id
    for slug in ("1-tong-quan", "3-yeu-cau-chuc-nang"):
        assert f'href="#{slug}"' in out
        assert f'id="{slug}"' in out


def test_badges_colorized_in_table_cells():
    out = render_html(_SAMPLE_MD)
    assert 'class="badge must"' in out
    assert 'class="badge should"' in out
    assert 'class="badge ok"' in out       # 🟢 Done
    assert 'class="badge danger"' in out   # 🔴 Blocked


def test_title_defaults_to_first_h1():
    out = render_html("# My Doc Title\n\n## A\n", title=None)
    assert "My Doc Title" in out


# --- CLI ---


def test_cli_writes_file(tmp_path):
    src = tmp_path / "srs.md"
    src.write_text(_SAMPLE_MD, encoding="utf-8")
    dst = tmp_path / "srs.html"
    r = subprocess.run(
        [_PYTHON, str(_SCRIPT), "--input", str(src), "--output", str(dst)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    assert dst.exists()
    html = dst.read_text(encoding="utf-8")
    assert "--mor-navy:#0E1A4B" in html
    assert 'href="#1-tong-quan"' in html


def test_cli_missing_input_fails(tmp_path):
    dst = tmp_path / "out.html"
    r = subprocess.run(
        [_PYTHON, str(_SCRIPT), "--input", str(tmp_path / "nope.md"), "--output", str(dst)],
        capture_output=True, text=True,
    )
    assert r.returncode != 0
    assert not dst.exists()
