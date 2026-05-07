"""Parse a brainstorm plan markdown into a normalized Delta.

Plan markdown convention (lenient default):
    ### ADD FR-007: User logout
    - description: User can sign out
    - priority: Mid
    - related_screens: [SCREEN-001]

    ### UPDATE FR-005
    - field: description
    - new_value: "Updated description"

    ### DEPRECATE FR-003
    - reason: Replaced by FR-008

Lenient mode auto-fixes:
    - Heading level off-by-one (## vs ###)
    - ID zero-padding (FR-7 -> FR-007)
    - Extra colons (### ADD: FR-007)

Strict mode (--strict) requires exact format.

CLI:
    parse-plan.py --plan plan.md [--strict] --output delta.json

Public API:
    parse_plan(path, strict=False) -> Delta
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.normalized_schema import Change, Delta, save_delta  # noqa: E402

# Lenient: matches "### ADD FR-7", "## ADD: FR-007", "#### UPDATE FR-007: name"
_LENIENT_OP_HEADER = re.compile(
    r"^#{2,4}\s+(ADD|UPDATE|DEPRECATE)\s*[:\s]\s*"
    r"(FR|NFR|SCREEN|DATA|INT|TBL|TABLE|INDEX|REL|ENDPOINT|ERROR_CODE|ERR|WEBHOOK|ENUM)"
    r"-?(\d+)\s*[:\-]?\s*(.*?)\s*$",
    re.IGNORECASE,
)
_STRICT_OP_HEADER = re.compile(
    r"^###\s+(ADD|UPDATE|DEPRECATE)\s+"
    r"(FR|NFR|SCREEN|DATA|INT|TBL|TABLE|INDEX|REL|ENDPOINT|ERROR_CODE|ERR|WEBHOOK|ENUM)"
    r"-(\d{3,})\s*(?::\s*(.*?))?\s*$"
)
_BULLET = re.compile(r"^\s*[-*]\s+(.+?)\s*$")
_KV = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*[:=]\s*(.+?)\s*$")

# Map short type → schema entity_type
_TYPE_MAP = {
    "FR": "FR", "NFR": "NFR", "SCREEN": "SCREEN", "DATA": "DATA", "INT": "INT",
    "TBL": "TABLE", "TABLE": "TABLE", "INDEX": "INDEX", "REL": "REL",
    "ENDPOINT": "ENDPOINT", "ERROR_CODE": "ERROR_CODE", "ERR": "ERROR_CODE",
    "WEBHOOK": "WEBHOOK", "ENUM": "ENUM",
}


def parse_plan(path: str | Path, strict: bool = False) -> Delta:
    """Parse plan.md → Delta. Lenient by default."""
    plan_path = Path(path)
    text = plan_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    pattern = _STRICT_OP_HEADER if strict else _LENIENT_OP_HEADER
    changes: list[Change] = []

    current_op: str | None = None
    current_type: str | None = None
    current_id: str | None = None
    current_name: str = ""
    current_payload: dict[str, object] = {}

    def flush() -> None:
        nonlocal current_op, current_type, current_id, current_name, current_payload
        if current_op is None or current_type is None or current_id is None:
            return
        payload = dict(current_payload)
        if current_name and "name" not in payload:
            payload["name"] = current_name
        changes.append(
            Change(
                op=current_op,
                entity_type=current_type,
                entity_id=current_id,
                payload=payload if payload else None,
                reason=f"From plan {plan_path.name}",
            )
        )
        current_op = None
        current_type = None
        current_id = None
        current_name = ""
        current_payload = {}

    for raw_line in lines:
        line = raw_line.rstrip()
        m = pattern.match(line)
        if m:
            flush()
            op = m.group(1).upper()
            entity_type = _TYPE_MAP.get(m.group(2).upper())
            num_str = m.group(3)
            num = int(num_str)
            current_op = op
            current_type = entity_type
            current_id = f"{m.group(2).upper().replace('TBL', 'TBL')}-{num:03d}"
            # Normalize TABLE/TBL aliases for ID prefix
            prefix_for_id = m.group(2).upper()
            if prefix_for_id == "TABLE":
                prefix_for_id = "TBL"
            elif prefix_for_id == "ERROR_CODE":
                prefix_for_id = "ERR"
            current_id = f"{prefix_for_id}-{num:03d}"
            current_name = (m.group(4) or "").strip(": -").strip()
            current_payload = {}
            continue

        if current_op is None:
            continue

        # Parse bullet payload entries
        bullet = _BULLET.match(line)
        if bullet:
            inner = bullet.group(1)
            kv = _KV.match(inner)
            if kv:
                key = kv.group(1).lower()
                value = kv.group(2).strip()
                current_payload[key] = _coerce_value(value)
            else:
                # Plain bullet - append to "notes" list
                current_payload.setdefault("notes", []).append(inner)  # type: ignore[union-attr]

    flush()
    return Delta(
        source_type="plan",
        source_path=str(plan_path),
        changes=changes,
    )


def _coerce_value(value: str) -> object:
    """Coerce simple list / quoted string / bare value."""
    s = value.strip()
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"') for item in inner.split(",")]
    return s


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--plan", required=True)
    p.add_argument("--strict", action="store_true", help="Strict format only")
    p.add_argument("--output", required=True)
    args = p.parse_args()

    delta = parse_plan(args.plan, strict=args.strict)
    save_delta(delta, args.output)
    print(
        f"Parsed {args.plan}: {len(delta.changes)} changes -> {args.output}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
