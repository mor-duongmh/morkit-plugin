"""Coordinate sub-skill execution for docs-hero init / update flows.

Init: invoke each sub-skill's renderer in turn (subprocess) so each renderer
runs in isolation with its own argparse. Per-screen rendering also handled here.

Update: filter Delta by entity_type per doc, then run the diff engine
(detect_manual_edits → compute_diff → apply_patch) for each affected doc.

CLI:
    dispatch_coordinator.py init   --project-model PATH --language EN \
                                   --outputs srs,api,db --docs-dir docs/
    dispatch_coordinator.py update --delta PATH --docs-dir docs/ \
                                   --meta PATH [--language EN]
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from lib.normalized_schema import (  # noqa: E402
    Change,
    Delta,
    load_delta,
    load_project_model,
    save_delta,
)

log = logging.getLogger(__name__)

# Resolve sibling sub-skill folders.
# Plugin layout: $MORKIT_PLUGIN_ROOT (or $CLAUDE_PLUGIN_ROOT)/skills/<sub-skill>/scripts/
# Bundle layout (legacy): <bundle>/.claude/skills/<sub-skill>/scripts/ via parents[1]
_PLUGIN_ROOT_ENV = os.environ.get("MORKIT_PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")
if _PLUGIN_ROOT_ENV:
    _SKILLS_ROOT = Path(_PLUGIN_ROOT_ENV) / "skills"
else:
    _SKILLS_ROOT = _THIS_DIR.parents[1]  # legacy bundle layout
_SRS_SCRIPTS = _SKILLS_ROOT / "generate-srs" / "scripts"
_API_SCRIPTS = _SKILLS_ROOT / "generate-api-docs" / "scripts"
_DB_SCRIPTS = _SKILLS_ROOT / "generate-db-design" / "scripts"
_ARCH_SCRIPTS = _SKILLS_ROOT / "generate-system-architecture" / "scripts"
_STD_SCRIPTS = _SKILLS_ROOT / "generate-code-standards" / "scripts"
_SUM_SCRIPTS = _SKILLS_ROOT / "generate-codebase-summary" / "scripts"
_GUI_SCRIPTS = _SKILLS_ROOT / "generate-design-guidelines" / "scripts"

PYTHON = sys.executable

# Filter rules — entity_types each sub-skill cares about.
# Adding a key here lets `update` mode route changes to the right doc, but
# does NOT wire up `init` rendering — each sub-skill needs its own block in
# run_init() and an entry in _DOC_FILES (init is added in PR-B/PR-C; SCOPES
# is reserved here so the schema/Change.entity_type stay consistent).
SCOPES: dict[str, set[str]] = {
    "srs": {"FR", "NFR", "SCREEN", "DATA", "INT"},
    "api": {"ENDPOINT", "ERROR_CODE", "WEBHOOK", "AUTH_CONFIG", "RATE_LIMIT"},
    "db": {"TABLE", "INDEX", "REL", "ENUM"},
    "arch": {"CMP", "LAY", "INX", "QG"},
    "standards": {"LNT", "NAM", "CMT", "FMT"},
    "summary": {"RPO", "TCH", "PKG", "MOD"},
    "guidelines": {"DPR", "PTN", "ADR"},
}


@dataclass
class StepResult:
    name: str
    ok: bool
    output_path: str = ""
    message: str = ""


def _run(cmd: list[str]) -> tuple[bool, str]:
    """Run a subprocess; return (ok, combined_output)."""
    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True, check=False, timeout=300
        )
    except subprocess.TimeoutExpired:
        return False, f"timeout: {' '.join(cmd)}"
    out = (res.stdout or "") + (res.stderr or "")
    return res.returncode == 0, out.strip()


def filter_delta(delta: Delta, scope: set[str]) -> Delta:
    """Return new Delta containing only changes whose entity_type ∈ scope."""
    return Delta(
        source_type=delta.source_type,
        source_path=delta.source_path,
        changes=[c for c in delta.changes if c.entity_type in scope],
    )


# --- Init flow ---


def run_init(
    project_model: Path,
    language: str,
    outputs: list[str],
    docs_dir: Path,
) -> list[StepResult]:
    docs_dir.mkdir(parents=True, exist_ok=True)
    results: list[StepResult] = []

    if "srs" in outputs:
        srs_out = docs_dir / "srs.md"
        ok, msg = _run([
            PYTHON, str(_SRS_SCRIPTS / "render_srs.py"),
            "--project-model", str(project_model),
            "--language", language,
            "--output", str(srs_out),
        ])
        results.append(StepResult("srs", ok, str(srs_out), msg))

        # Per-screen specs
        if ok:
            model = load_project_model(project_model)
            screens_dir = docs_dir / "screen-specs"
            screens_dir.mkdir(exist_ok=True)
            for screen in model.screens:
                spec_out = screens_dir / f"{screen.id}-{screen.slug}.md"
                ok2, msg2 = _run([
                    PYTHON, str(_SRS_SCRIPTS / "render_screen_spec.py"),
                    "--project-model", str(project_model),
                    "--screen-id", screen.id,
                    "--language", language,
                    "--output", str(spec_out),
                ])
                results.append(StepResult(f"screen-{screen.id}", ok2, str(spec_out), msg2))

    if "api" in outputs:
        api_out = docs_dir / "api-docs.md"
        ok, msg = _run([
            PYTHON, str(_API_SCRIPTS / "render_api_docs.py"),
            "--project-model", str(project_model),
            "--language", language,
            "--output", str(api_out),
        ])
        results.append(StepResult("api", ok, str(api_out), msg))

    if "db" in outputs:
        db_out = docs_dir / "database-design.md"
        ok, msg = _run([
            PYTHON, str(_DB_SCRIPTS / "render_db_design.py"),
            "--project-model", str(project_model),
            "--language", language,
            "--output", str(db_out),
        ])
        results.append(StepResult("db", ok, str(db_out), msg))

    if "arch" in outputs:
        arch_out = docs_dir / "system-architecture.md"
        ok, msg = _run([
            PYTHON, str(_ARCH_SCRIPTS / "render_system_architecture.py"),
            "--project-model", str(project_model),
            "--language", language,
            "--output", str(arch_out),
        ])
        results.append(StepResult("arch", ok, str(arch_out), msg))

    if "standards" in outputs:
        std_out = docs_dir / "code-standards.md"
        ok, msg = _run([
            PYTHON, str(_STD_SCRIPTS / "render_code_standards.py"),
            "--project-model", str(project_model),
            "--language", language,
            "--output", str(std_out),
        ])
        results.append(StepResult("standards", ok, str(std_out), msg))

    if "summary" in outputs:
        sum_out = docs_dir / "codebase-summary.md"
        ok, msg = _run([
            PYTHON, str(_SUM_SCRIPTS / "render_codebase_summary.py"),
            "--project-model", str(project_model),
            "--language", language,
            "--output", str(sum_out),
        ])
        results.append(StepResult("summary", ok, str(sum_out), msg))

    if "guidelines" in outputs:
        gui_out = docs_dir / "design-guidelines.md"
        adr_dir = docs_dir / "adr"
        ok, msg = _run([
            PYTHON, str(_GUI_SCRIPTS / "render_design_guidelines.py"),
            "--project-model", str(project_model),
            "--language", language,
            "--output", str(gui_out),
            "--adr-dir", str(adr_dir),
        ])
        results.append(StepResult("guidelines", ok, str(gui_out), msg))

    return results


# --- Update flow ---


_DOC_FILES = {
    "srs": "srs.md",
    "api": "api-docs.md",
    "db": "database-design.md",
    "arch": "system-architecture.md",
    "standards": "code-standards.md",
    "summary": "codebase-summary.md",
    # "guidelines" intentionally omitted — design-guidelines.md is manual
    # only (no sync mode), so update flow does not iterate it.
}


def run_update(
    delta_path: Path,
    docs_dir: Path,
    meta_path: Path,
    tmp_dir: Path,
) -> list[StepResult]:
    """For each doc, filter delta → detect edits → compute diff → apply patch."""
    delta = load_delta(delta_path)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    results: list[StepResult] = []

    for skill_name, filename in _DOC_FILES.items():
        scoped = filter_delta(delta, SCOPES[skill_name])
        if not scoped.changes:
            continue

        doc_path = docs_dir / filename
        if not doc_path.exists():
            results.append(StepResult(skill_name, False, str(doc_path),
                                       "doc missing — run init first"))
            continue

        scoped_delta_path = tmp_dir / f"{skill_name}-delta.json"
        save_delta(scoped, scoped_delta_path)

        edits_path = tmp_dir / f"{skill_name}-edits.json"
        plan_path = tmp_dir / f"{skill_name}-plan.json"

        ok, msg = _run([
            PYTHON, str(_THIS_DIR / "detect_manual_edits.py"),
            "--doc", str(doc_path),
            "--meta", str(meta_path),
            "--output", str(edits_path),
        ])
        if not ok:
            results.append(StepResult(skill_name, False, str(doc_path), msg))
            continue

        ok, msg = _run([
            PYTHON, str(_THIS_DIR / "compute_diff.py"),
            "--delta", str(scoped_delta_path),
            "--doc", str(doc_path),
            "--manual-edits", str(edits_path),
            "--output", str(plan_path),
        ])
        if not ok:
            results.append(StepResult(skill_name, False, str(doc_path), msg))
            continue

        ok, msg = _run([
            PYTHON, str(_THIS_DIR / "apply_patch.py"),
            "--plan", str(plan_path),
            "--doc", str(doc_path),
            "--meta", str(meta_path),
        ])
        results.append(StepResult(skill_name, ok, str(doc_path), msg))

    return results


# --- CLI ---


def _print_results(results: list[StepResult]) -> int:
    fail = 0
    for r in results:
        flag = "✓" if r.ok else "✗"
        print(f"{flag} {r.name:<20} {r.output_path}", file=sys.stderr)
        if not r.ok and r.message:
            print(f"    {r.message[:300]}", file=sys.stderr)
            fail += 1
    return 0 if fail == 0 else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init")
    init_p.add_argument("--project-model", required=True)
    init_p.add_argument("--language", default="EN", choices=["JP", "EN", "VN"])
    init_p.add_argument("--outputs", default="srs,api,db",
                        help="Comma-separated subset of srs,api,db")
    init_p.add_argument("--docs-dir", default="docs")

    upd_p = sub.add_parser("update")
    upd_p.add_argument("--delta", required=True)
    upd_p.add_argument("--docs-dir", default="docs")
    upd_p.add_argument("--meta", required=True)
    upd_p.add_argument("--tmp-dir", default=".tmp")

    args = p.parse_args()

    if args.command == "init":
        outputs = [s.strip() for s in args.outputs.split(",") if s.strip()]
        results = run_init(Path(args.project_model), args.language, outputs, Path(args.docs_dir))
    else:
        results = run_update(Path(args.delta), Path(args.docs_dir),
                              Path(args.meta), Path(args.tmp_dir))

    # JSON line for the orchestrator to ingest
    payload = [
        {"name": r.name, "ok": r.ok, "output_path": r.output_path}
        for r in results
    ]
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")

    return _print_results(results)


if __name__ == "__main__":
    raise SystemExit(main())
