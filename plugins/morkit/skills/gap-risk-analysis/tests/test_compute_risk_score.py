"""Tests for compute_risk_score.py (Phase 3)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from compute_risk_score import (  # noqa: E402
    normalize_level,
    score,
    validate_risk_rows,
)

# (prob, impact) -> (score, is_high). Full 3x3 truth table; High = score >= 6.
TRUTH = {
    ("H", "H"): (9, True),
    ("H", "M"): (6, True),
    ("H", "L"): (3, False),
    ("M", "H"): (6, True),
    ("M", "M"): (4, False),
    ("M", "L"): (2, False),
    ("L", "H"): (3, False),
    ("L", "M"): (2, False),
    ("L", "L"): (1, False),
}


@pytest.mark.parametrize("pair,expected", list(TRUTH.items()))
def test_score_truth_table(pair, expected):
    assert score(*pair) == expected


def test_high_threshold_is_six():
    # Exactly 6 is High; 4 is not. (Boundary lock.)
    assert score("H", "M") == (6, True)
    assert score("M", "M") == (4, False)


def test_normalize_accepts_high_mid_low_spelling():
    assert normalize_level("High") == "H"
    assert normalize_level("mid") == "M"
    assert normalize_level("LOW") == "L"
    assert score("High", "Mid") == (6, True)


def test_normalize_rejects_unknown():
    with pytest.raises(ValueError):
        normalize_level("Critical")


def test_high_without_mitigation_fails():
    rows = [{"id": "RISK-001", "probability": "H", "impact": "H", "mitigation": ""}]
    errors = validate_risk_rows(rows)
    assert errors
    assert "RISK-001" in errors[0]
    assert "mitigation" in errors[0]


def test_high_with_mitigation_passes():
    rows = [{"id": "RISK-001", "probability": "H", "impact": "H", "mitigation": "Phased rollout"}]
    assert validate_risk_rows(rows) == []


def test_low_risk_needs_no_mitigation():
    rows = [{"id": "RISK-002", "probability": "L", "impact": "L", "mitigation": ""}]
    assert validate_risk_rows(rows) == []


def test_precomputed_score_must_match():
    rows = [{"id": "RISK-003", "probability": "M", "impact": "M", "score": 9, "mitigation": ""}]
    errors = validate_risk_rows(rows)
    assert any("!= computed 4" in e for e in errors)


def test_bad_level_reported_with_id():
    rows = [{"id": "RISK-004", "probability": "X", "impact": "H", "mitigation": "x"}]
    errors = validate_risk_rows(rows)
    assert any("RISK-004" in e and "unknown level" in e for e in errors)


def test_non_integer_score_reported_not_crash():
    # M-1 guard: a non-integer precomputed score must yield a clean error,
    # not a ValueError crash of the whole register validation.
    rows = [{"id": "RISK-005", "probability": "M", "impact": "M", "score": "abc", "mitigation": ""}]
    errors = validate_risk_rows(rows)
    assert any("RISK-005" in e and "not an integer" in e for e in errors)


def test_rows_not_a_list_reported():
    assert validate_risk_rows({"not": "a list"}) == ["risk rows must be a list"]


def test_non_dict_row_reported():
    errors = validate_risk_rows(["oops"])
    assert any("must be an object" in e for e in errors)
