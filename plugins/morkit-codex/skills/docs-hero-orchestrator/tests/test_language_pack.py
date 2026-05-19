"""Tests for lib/language_pack.py."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib.language_pack import HEADINGS, Language, available_keys, t, vague_terms  # noqa: E402


def test_basic_lookup_jp():
    assert t("overview", Language.JP) == "概要"


def test_basic_lookup_en():
    assert t("overview", Language.EN) == "Overview"


def test_basic_lookup_vn():
    assert t("overview", Language.VN) == "Tổng quan"


def test_string_lang_argument():
    assert t("overview", "JP") == "概要"
    assert t("overview", "en") == "Overview"  # Case-insensitive via .upper()


def test_unknown_key_returns_key():
    assert t("nonexistent_key_xyz", Language.JP) == "nonexistent_key_xyz"


def test_missing_translation_falls_back_en():
    # Inject a key that only has EN
    HEADINGS["__test_only_en"] = {"EN": "Only English"}
    assert t("__test_only_en", Language.JP) == "Only English"
    del HEADINGS["__test_only_en"]


def test_all_keys_have_three_languages():
    """Every registered heading must have JP/EN/VN translations."""
    missing = []
    for key in available_keys():
        bucket = HEADINGS[key]
        for lang in ("JP", "EN", "VN"):
            if lang not in bucket:
                missing.append(f"{key}:{lang}")
    assert not missing, f"Missing translations: {missing}"


def test_available_keys_sorted():
    keys = available_keys()
    assert keys == sorted(keys)


def test_vague_terms_per_language():
    en = vague_terms(Language.EN)
    jp = vague_terms(Language.JP)
    vn = vague_terms(Language.VN)
    assert "fast" in en
    assert "速い" in jp
    assert "nhanh" in vn


def test_vague_terms_unknown_lang_falls_back_en():
    assert vague_terms("XX") == vague_terms(Language.EN)


def test_critical_keys_present():
    """Verify keys required by phase-04..06 templates are all registered."""
    required = [
        "overview", "functional_requirements", "non_functional_requirements",
        "screen_design_index", "data_items", "external_interfaces",
        "constraints_risks", "glossary", "approval", "revision_history",
        "deprecated_items",
        "endpoints", "error_codes", "authentication",
        "tables", "indexes", "relationships", "enums", "erd",
    ]
    for key in required:
        assert key in HEADINGS, f"Missing critical key: {key}"
