"""Validate a greenfield ``state.json`` against the locked conventions.

Dependency-free (stdlib only) so it runs anywhere the plugin venv can. The
constants + ``validate_state`` here are the single source of truth for stage
order and enums; ``state_manager.py`` (Phase 6) imports them rather than
re-declaring (DRY). See ``references/greenfield-conventions.md`` §2-§3.

Public API:
    STAGES, STAGE_STATUS, FORMATS, LANGS, GATE_DECISIONS, GATED_STAGES
    validate_state(data) -> list[str]   # [] == valid
    load_state(path) -> dict
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Stage order (G0..G7) — the only place this list is declared.
STAGES = ["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7"]
STAGE_STATUS = {"pending", "in_progress", "done", "blocked"}
FORMATS = {"brse", "agile"}
LANGS = {"JP", "EN", "VN"}
GATE_DECISIONS = {"pending", "proceed", "adjust", "force-close"}
# Stages that carry a human-review gate (see conventions §2).
# G2 (function list / user story) is gated too — it is the foundational artifact
# everything downstream is built on, so it gets its own confirm gate.
GATED_STAGES = {"G2", "G3", "G4", "G6"}

_REQUIRED_TOP = ("project", "stage", "stages")


def validate_state(data: Any) -> list[str]:
    """Return a list of human-readable validation errors ([] == valid)."""
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["state must be a JSON object"]

    for key in _REQUIRED_TOP:
        if key not in data:
            errors.append(f"missing required key: {key}")

    project = data.get("project")
    if "project" in data and (not isinstance(project, str) or not project.strip()):
        errors.append("project must be a non-empty string")

    stage = data.get("stage")
    if "stage" in data and stage not in STAGES:
        errors.append(f"stage must be one of {STAGES}, got {stage!r}")

    if "format" in data and data["format"] not in FORMATS:
        errors.append(f"format must be one of {sorted(FORMATS)}, got {data['format']!r}")

    if "lang" in data and data["lang"] not in LANGS:
        errors.append(f"lang must be one of {sorted(LANGS)}, got {data['lang']!r}")

    stages = data.get("stages")
    if "stages" in data:
        if not isinstance(stages, dict):
            errors.append("stages must be an object keyed by stage id")
        else:
            errors.extend(_validate_stages(stages))

    return errors


def _validate_stages(stages: dict) -> list[str]:
    errors: list[str] = []
    for sid, rec in stages.items():
        if sid not in STAGES:
            errors.append(f"unknown stage id: {sid!r}")
            continue
        if not isinstance(rec, dict):
            errors.append(f"stages.{sid} must be an object")
            continue
        status = rec.get("status")
        if status is None:
            errors.append(f"stages.{sid} missing required key: status")
        elif status not in STAGE_STATUS:
            errors.append(
                f"stages.{sid}.status must be one of {sorted(STAGE_STATUS)}, got {status!r}"
            )
        gate = rec.get("gate")
        if gate is not None:
            errors.extend(_validate_gate(sid, gate))
    return errors


def _validate_gate(sid: str, gate: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(gate, dict):
        errors.append(f"stages.{sid}.gate must be an object or null")
        return errors
    decision = gate.get("decision")
    if decision is None:
        errors.append(f"stages.{sid}.gate missing required key: decision")
    elif decision not in GATE_DECISIONS:
        errors.append(
            f"stages.{sid}.gate.decision must be one of {sorted(GATE_DECISIONS)}, got {decision!r}"
        )
    # Optional checklist record: {required:[str], confirmed:[str]} — drives the
    # advance hard-block. Absent on legacy/no-checklist gates (allowed).
    if gate.get("checklist") is not None:
        errors.extend(_validate_checklist(sid, gate["checklist"]))
    return errors


def _validate_checklist(sid: str, checklist: Any) -> list[str]:
    if not isinstance(checklist, dict):
        return [f"stages.{sid}.gate.checklist must be an object"]
    errors: list[str] = []
    for field in ("required", "confirmed"):
        val = checklist.get(field, [])
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            errors.append(f"stages.{sid}.gate.checklist.{field} must be a list of strings")
    return errors


def load_state(path: str | Path) -> dict:
    """Load + parse a state.json file (no validation)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--state", required=True, help="Path to state.json")
    args = p.parse_args()

    try:
        data = load_state(args.state)
    except FileNotFoundError:
        print(f"ERROR: state file not found: {args.state}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {args.state}: {exc}", file=sys.stderr)
        return 2

    errors = validate_state(data)
    if errors:
        print(f"INVALID state.json ({len(errors)} error(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"OK: state.json valid (stage={data.get('stage')})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
