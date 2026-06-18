"""Validate a bridge-authored ``project-model.json`` against ``normalized_schema``.

The bridge (``build-project-model`` skill) authors JSON; this script is the
hard gate that confirms it is loadable by the SAME Pydantic models ``init``
uses, so a passing file is guaranteed to render. On failure it prints the exact
field path + message so the skill can re-author precisely (validation loop).

Reuses ``docs-hero-orchestrator/scripts/lib/normalized_schema.py`` — no schema
is duplicated here. ``extra="allow"`` means provenance extras
(``external_sources``, etc.) are preserved, not rejected.

Public API:
    validate_project_model(data) -> list[str]   # [] == valid
    parse_project_model(data) -> ProjectModel    # raises ValidationError
    load_json(path) -> dict
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def _normalized_schema_dir() -> Path:
    """Locate the docs-hero ``scripts/lib`` dir holding normalized_schema.py.

    Order: ``MORKIT_NORMALIZED_SCHEMA_DIR`` env override, then the in-repo
    sibling skill (the only layout that ships on ``main``).
    """
    env = os.environ.get("MORKIT_NORMALIZED_SCHEMA_DIR")
    if env:
        return Path(env)
    # this file lives in skills/build-project-model/scripts/ → up two to skills/
    skills = Path(__file__).resolve().parents[2]
    return skills / "docs-hero-orchestrator" / "scripts" / "lib"


_LIB = _normalized_schema_dir()
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import normalized_schema as ns  # noqa: E402
from pydantic import ValidationError  # noqa: E402

ProjectModel = ns.ProjectModel


def parse_project_model(data: Any) -> "ns.ProjectModel":
    """Validate + return a ProjectModel instance (raises ValidationError)."""
    return ProjectModel.model_validate(data)


def validate_project_model(data: Any) -> list[str]:
    """Return formatted ``loc: message`` errors ([] == valid)."""
    # Raw-dict lint FIRST: Pydantic's extra="allow" silently keeps a
    # `status:"Draft"` placed on a block without a typed status field (e.g.
    # `meta`), so a pure model_validate would report a misleading OK. Catch the
    # locked provenance pitfall (draft belongs in `doc_status`, not `status`).
    errors = _lint_status_misuse(data) if isinstance(data, dict) else []
    try:
        parse_project_model(data)
    except ValidationError as exc:
        errors.extend(_format_error(e) for e in exc.errors())
    return errors


def _lint_status_misuse(data: dict) -> list[str]:
    """Flag any DocStatus value (Draft/In Review/...) mistakenly put in a
    lifecycle ``status`` field anywhere in the tree (status only accepts
    active/deprecated; review state belongs in ``doc_status``)."""
    # docstatus-only labels: a `status` value matching one of these is the pitfall.
    misused = {d.value.lower() for d in ns.DocStatus} - {s.value.lower() for s in ns.Status}
    errors: list[str] = []
    _walk_status(data, "", misused, errors)
    return errors


def _walk_status(node: Any, path: str, misused: set, errors: list) -> None:
    """Recursively collect status-misuse errors (flat to keep complexity low)."""
    if isinstance(node, dict):
        for key, val in node.items():
            child = f"{path}.{key}" if path else str(key)
            if key == "status" and isinstance(val, str) and val.strip().lower() in misused:
                errors.append(
                    f"{child}: {val!r} is a doc_status value, not a lifecycle "
                    f"status — use 'doc_status'"
                )
            _walk_status(val, child, misused, errors)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            _walk_status(item, f"{path}[{i}]", misused, errors)


def _format_error(err: dict) -> str:
    loc = ".".join(str(p) for p in err.get("loc", ())) or "<root>"
    msg = err.get("msg", "invalid")
    return f"{loc}: {msg}"


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--project-model", required=True, help="Path to project-model.json")
    args = p.parse_args()

    try:
        data = load_json(args.project_model)
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.project_model}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {args.project_model}: {exc}", file=sys.stderr)
        return 2

    errors = validate_project_model(data)
    if errors:
        print(f"INVALID project-model.json ({len(errors)} error(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    model = parse_project_model(data)
    fr = len(model.functional_requirements)
    uc = len(model.business_flow.use_cases)
    print(
        f"OK: project-model.json valid "
        f"(project={model.meta.project_name!r}, FR={fr}, UseCase={uc})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
