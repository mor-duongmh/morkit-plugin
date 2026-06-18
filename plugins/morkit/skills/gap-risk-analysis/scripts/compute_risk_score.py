"""Risk scoring helper for the gap-risk-analysis skill.

Locked rule (plan §Locked Decision 5): map ``H/M/L → 3/2/1``,
``Score = Probability × Impact`` (1..9), ``High = Score >= 6``, and **every High
risk MUST carry a non-empty mitigation** — enforced as validation, not just
convention. The ``risk-register.md`` is the canonical source; the ProjectModel
``Risk[]`` and SRS §13.3 render *derived* from it (single source of truth).

Stdlib only, Python 3.9 compatible.

Public API:
    LEVELS                                  # {"H":3,"M":2,"L":1}
    normalize_level(s) -> "H"|"M"|"L"
    score(prob, impact) -> tuple[int, bool]  # (1..9, is_high)
    is_high(score_value) -> bool
    validate_risk_rows(rows) -> list[str]    # [] == valid
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Canonical numeric weights.
LEVELS = {"H": 3, "M": 2, "L": 1}
HIGH_THRESHOLD = 6

# Accept the schema's High/Mid/Low spelling (and a few common variants) and fold
# them onto the canonical H/M/L so register rows and ProjectModel.Risk agree.
_ALIASES = {
    "H": "H", "HIGH": "H",
    "M": "M", "MID": "M", "MEDIUM": "M", "MED": "M",
    "L": "L", "LOW": "L",
}


def normalize_level(value: str) -> str:
    """Fold High/Mid/Low (any case) onto canonical H/M/L. Raises on unknown."""
    key = str(value).strip().upper()
    if key not in _ALIASES:
        raise ValueError(f"unknown level {value!r}; expected one of H/M/L (or High/Mid/Low)")
    return _ALIASES[key]


def score(prob: str, impact: str) -> "tuple[int, bool]":
    """Return ``(score 1..9, is_high)`` for a probability/impact pair."""
    s = LEVELS[normalize_level(prob)] * LEVELS[normalize_level(impact)]
    return s, is_high(s)


def is_high(score_value: int) -> bool:
    return score_value >= HIGH_THRESHOLD


def validate_risk_rows(rows: Any) -> list[str]:
    """Validate a list of risk rows. Each row: ``{id, probability, impact, mitigation}``.

    Checks level enums and enforces "High ⇒ non-empty mitigation".
    Returns ``[]`` when valid.
    """
    if not isinstance(rows, list):
        return ["risk rows must be a list"]
    errors: list[str] = []
    for i, row in enumerate(rows):
        errors.extend(_validate_one_row(row, i))
    return errors


def _validate_one_row(row: Any, i: int) -> list[str]:
    rid = row.get("id", f"row[{i}]") if isinstance(row, dict) else f"row[{i}]"
    if not isinstance(row, dict):
        return [f"{rid}: must be an object"]
    try:
        s, high = score(row.get("probability", ""), row.get("impact", ""))
    except ValueError as exc:
        return [f"{rid}: {exc}"]
    errors: list[str] = []
    if high and not str(row.get("mitigation", "")).strip():
        errors.append(f"{rid}: High risk (score {s}) requires a non-empty mitigation")
    errors.extend(_check_declared_score(row, rid, s))
    return errors


def _check_declared_score(row: dict, rid: str, computed: int) -> list[str]:
    """A row may carry a precomputed ``score``; if so it must be an int and match."""
    if "score" not in row or row["score"] in (None, ""):
        return []
    try:
        declared = int(row["score"])
    except (TypeError, ValueError):
        return [f"{rid}: score {row['score']!r} is not an integer"]
    return [] if declared == computed else [f"{rid}: score {declared} != computed {computed}"]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--prob", help="Probability H/M/L (or High/Mid/Low)")
    p.add_argument("--impact", help="Impact H/M/L (or High/Mid/Low)")
    p.add_argument("--rows", help="Path to a JSON array of risk rows to validate")
    args = p.parse_args()

    if args.rows:
        try:
            rows = json.loads(Path(args.rows).read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(f"ERROR: rows file not found: {args.rows}", file=sys.stderr)
            return 2
        except json.JSONDecodeError as exc:
            print(f"ERROR: invalid JSON in {args.rows}: {exc}", file=sys.stderr)
            return 2
        errors = validate_risk_rows(rows)
        if errors:
            print(f"INVALID risk rows ({len(errors)}):", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            return 1
        print(f"OK: {len(rows)} risk row(s) valid", file=sys.stderr)
        return 0

    if args.prob and args.impact:
        s, high = score(args.prob, args.impact)
        print(f"score={s} high={high}")
        return 0

    p.error("provide --rows PATH, or both --prob and --impact")
    return 2  # unreachable (argparse exits)


if __name__ == "__main__":
    raise SystemExit(main())
