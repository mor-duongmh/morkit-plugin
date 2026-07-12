"""Render a validated ProjectModel into `tasks.json` — the input to diff + gate.

Deterministic: same (model, lang, skip_nfr) always produces byte-identical output.
Nothing here talks to Jira; nothing here invents content. A field the SRS does not
carry simply does not become a section.

CLI:
    build_tasks.py --model project-model.json --out tasks.json \
        [--lang JP|EN|VN] [--skip-nfr]

Emits a JSON result on stdout for SKILL.md to read. On failure, prints a
plain-language message (no traceback) and exits non-zero.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_ORCH_SCRIPTS = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import jira_map  # noqa: E402
from lib.language_pack import Language  # noqa: E402
from lib.normalized_schema import ProjectModel, Status  # noqa: E402
from task_mapper import MappingError, fr_to_task, nfr_to_task  # noqa: E402


def _is_active(entity) -> bool:
    """`status: deprecated` is how this pipeline retires a requirement.

    A deprecated FR still sits in the model (see deprecation_mover.py) — it must
    not become a ticket, and phase 2 must be able to tell it apart from an FR that
    was simply deleted, so its id is reported separately rather than dropped.
    """
    return getattr(entity, "status", Status.ACTIVE) != Status.DEPRECATED


def build(model: ProjectModel, lang: Language, skip_nfr: bool) -> tuple[list[dict], list[dict], list[str]]:
    tasks: list[dict] = []
    warnings: list[dict] = []
    deprecated: list[str] = []

    entities = list(model.functional_requirements)
    if not skip_nfr:
        entities += list(model.non_functional_requirements)

    for entity in entities:
        if not _is_active(entity):
            deprecated.append(entity.id)
            continue
        to_task = fr_to_task if entity.id.startswith("FR-") else nfr_to_task
        task, entity_warnings = to_task(entity, lang)
        tasks.append(task)
        warnings.extend(entity_warnings)

    return tasks, warnings, deprecated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProjectModel -> Jira tasks.json")
    parser.add_argument("--model", required=True, help="path to project-model.json")
    parser.add_argument("--out", required=True, help="path to write tasks.json")
    parser.add_argument("--lang", default="EN", choices=[lang.value for lang in Language])
    parser.add_argument(
        "--skip-nfr",
        action="store_true",
        help="omit NFRs. Recorded in tasks.json so phase 2 does not report them as orphaned.",
    )
    args = parser.parse_args(argv)

    model_path = Path(args.model)
    try:
        raw = model_path.read_bytes()
        model = ProjectModel.model_validate_json(raw)
    except FileNotFoundError:
        print(f"ERROR: project model not found: {model_path}", file=sys.stderr)
        return 1
    except Exception as exc:  # pydantic ValidationError / bad JSON
        print(f"ERROR: {model_path} is not a valid ProjectModel.\n{exc}", file=sys.stderr)
        return 1

    lang = Language(args.lang)
    try:
        tasks, warnings, deprecated = build(model, lang, args.skip_nfr)
    except MappingError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = {
        "meta": {
            "lang": lang.value,
            "skip_nfr": args.skip_nfr,
            "model_path": str(model_path),
            "model_sha256": hashlib.sha256(raw).hexdigest(),
            "deprecated_ids": deprecated,
        },
        "warnings": warnings,
        "tasks": tasks,
    }

    # First step of the pipeline, so it owns creating the workspace — and making sure
    # git ignores it. tasks.json holds the whole SRS.
    out_path = Path(args.out)
    jira_map.ensure_private_workspace(out_path.parent)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "out": str(out_path),
                "tasks": len(tasks),
                "stories": sum(1 for t in tasks if t["issue_type"] == "Story"),
                "issue_tasks": sum(1 for t in tasks if t["issue_type"] == "Task"),
                "warnings": len(warnings),
                "deprecated_skipped": len(deprecated),
                "lang": lang.value,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
