"""Render codebase-summary.md from a ProjectModel JSON.

Generates `docs/codebase-summary.md` with sections: what is this repo, tech
stack (grouped by category), repo layout, packages, entry points, LOC by
language, build & run quickstart.

CLI:
    render_codebase_summary.py --project-model {path}.json --language EN \
        --output docs/codebase-summary.md
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))

from lib.normalized_schema import (  # noqa: E402
    Language,
    ModuleEntry,
    PackageInfo,
    ProjectModel,
    RepoOverview,
    TechStackItem,
    load_project_model,
)


def _h(level: int, text: str) -> str:
    return f"{'#' * level} {text}\n\n"


def _safe(v, default: str = "_TBD_") -> str:
    return str(v) if v not in (None, "", []) else default


def _title(lang: Language) -> str:
    if lang == Language.JP:
        return "コードベース概要"
    if lang == Language.VN:
        return "Tổng quan mã nguồn"
    return "Codebase Summary"


def _render_meta(model: ProjectModel, lang: Language) -> str:
    today = date.today().isoformat()
    return (
        f"# {_title(lang)} — {model.meta.project_name}\n\n"
        f"| Field | Value |\n|---|---|\n"
        f"| Project | {model.meta.project_name} |\n"
        f"| Version | {model.meta.version} |\n"
        f"| Date | {today} |\n"
        f"| Language | {lang.value} |\n\n"
        "> LOC counts are **approximate** (pure-Python line counter, no `cloc` dependency).\n\n"
    )


def _render_overview(ro: RepoOverview | None) -> str:
    out = _h(2, "1. What is this repo")
    if ro is None:
        out += "_TBD_\n\n"
        out += (
            "| Field | Value |\n|---|---|\n"
            "| Primary language | _TBD_ |\n"
            "| Total LOC (approx) | _TBD_ |\n"
            "| VCS | git |\n"
            "| License | _TBD_ |\n\n"
        )
        return out
    out += f"{_safe(ro.description, ro.name or '_TBD_')}\n\n"
    out += (
        "| Field | Value |\n|---|---|\n"
        f"| Primary language | {_safe(ro.primary_language)} |\n"
        f"| Total LOC (approx) | {ro.loc_total:,} |\n"
        f"| VCS | {ro.vcs} |\n"
        f"| License | {_safe(ro.license)} |\n\n"
    )
    return out


def _render_tech_stack(items: list[TechStackItem]) -> str:
    out = _h(2, "2. Tech Stack")
    out += (
        "Grouped by category. `confidence: detected` = inferred from "
        "manifest; `declared` = present in user-provided ProjectModel.\n\n"
    )
    if not items:
        out += "_No tech-stack items recorded._\n\n"
        return out

    grouped: dict[str, list[TechStackItem]] = defaultdict(list)
    for ts in items:
        grouped[ts.category].append(ts)

    label = {
        "language": "Languages",
        "framework": "Frameworks",
        "db": "Databases",
        "infra": "Infrastructure",
        "ci": "CI",
        "test": "Test",
        "build": "Build",
    }
    order = ("language", "framework", "db", "infra", "ci", "test", "build")
    for cat in order:
        rows = grouped.get(cat)
        if not rows:
            continue
        out += _h(3, label[cat])
        out += "| ID | Name | Version | Confidence |\n|---|---|---|---|\n"
        for ts in rows:
            out += (
                f"| {ts.id} | {ts.name} | {_safe(ts.version, '-')} | "
                f"{ts.confidence} |\n"
            )
        out += "\n"
    return out


def _render_layout(modules: list[ModuleEntry]) -> str:
    """Depth-3 tree from ModuleEntry paths (best-effort)."""
    out = _h(2, "3. Repository Layout")
    out += (
        "Depth-3 tree (auto-generated; `node_modules` / `.venv` / `dist` / "
        "`build` / `.git` excluded).\n\n"
    )
    if not modules:
        out += "```\n.\n└── _TBD_\n```\n\n"
        return out

    # Build a path tree from module paths, capped at depth 3
    tree: dict = {}
    for m in modules:
        parts = Path(m.path).parts[:3]
        cur = tree
        for p in parts:
            cur = cur.setdefault(p, {})

    out += "```\n.\n"
    out += _format_tree(tree, prefix="")
    out += "```\n\n"
    return out


def _format_tree(tree: dict, prefix: str) -> str:
    """Render nested dict as ASCII tree."""
    lines: list[str] = []
    keys = sorted(tree.keys())
    for i, key in enumerate(keys):
        is_last = i == len(keys) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{key}")
        if tree[key]:
            extension = "    " if is_last else "│   "
            lines.append(_format_tree(tree[key], prefix + extension).rstrip("\n"))
    return "\n".join(lines) + "\n"


def _render_packages(packages: list[PackageInfo]) -> str:
    out = _h(2, "4. Packages / Workspaces")
    out += "| ID | Name | Path | Manager | Version | Deps |\n"
    out += "|---|---|---|---|---|---|\n"
    if not packages:
        out += "| PKG-001 | _TBD_ | _TBD_ | npm | - | 0 |\n\n"
        return out
    for p in packages:
        out += (
            f"| {p.id} | {_safe(p.name)} | `{_safe(p.path)}` | "
            f"{_safe(p.manager)} | {_safe(p.version, '-')} | {p.dep_count} |\n"
        )
    out += "\n"
    return out


def _render_entry_points(modules: list[ModuleEntry]) -> str:
    out = _h(2, "5. Entry Points")
    out += (
        "Files marked as program entry points (e.g. `main.py`, `index.ts`, "
        "`cmd/*`, `bin/*`, `pyproject [project.scripts]`).\n\n"
    )
    out += "| ID | Path | Language | LOC | Purpose |\n|---|---|---|---|---|\n"
    entries = [m for m in modules if m.is_entry_point]
    if not entries:
        out += "| MOD-001 | _TBD_ | _TBD_ | 0 | _TBD_ |\n\n"
        return out
    for m in entries:
        out += (
            f"| {m.id} | `{m.path}` | {_safe(m.language)} | "
            f"{m.loc} | {_safe(m.purpose)} |\n"
        )
    out += "\n"
    return out


def _render_loc_table(modules: list[ModuleEntry]) -> str:
    out = _h(2, "6. LOC by Language")
    if not modules:
        out += "| Language | Files | LOC (approx) | % |\n|---|---|---|---|\n"
        out += "| _TBD_ | 0 | 0 | 0% |\n\n"
        return out
    by_lang: dict[str, list[ModuleEntry]] = defaultdict(list)
    for m in modules:
        by_lang[m.language or "(unknown)"].append(m)
    total_loc = sum(m.loc for m in modules) or 1
    out += "| Language | Files | LOC (approx) | % |\n|---|---|---|---|\n"
    for lang_name in sorted(by_lang.keys()):
        files = by_lang[lang_name]
        loc = sum(m.loc for m in files)
        pct = loc * 100 // total_loc
        out += f"| {lang_name} | {len(files)} | {loc:,} | {pct}% |\n"
    out += f"| **Total** | **{len(modules)}** | **{total_loc:,}** | **100%** |\n\n"
    return out


def _render_quickstart() -> str:
    out = _h(2, "7. Build & Run quickstart")
    out += (
        "Detected commands (from `package.json` scripts / `Makefile` / "
        "`justfile` / `pyproject [tool.poetry.scripts]`):\n\n"
        "```bash\n# _TBD_ — fill from detected build files\n```\n\n"
    )
    return out


def _render_revision_history() -> str:
    return (
        "## Revision History\n\n"
        "| Version | Date | Author | Changes |\n"
        "|---|---|---|---|\n"
        f"| 1.0 | {date.today().isoformat()} | morkit (auto) | Initial generation |\n"
    )


def render_codebase_summary(model: ProjectModel, lang: Language) -> str:
    parts = [
        _render_meta(model, lang),
        _render_overview(model.repo_overview),
        _render_tech_stack(model.tech_stack),
        _render_layout(model.modules),
        _render_packages(model.packages),
        _render_entry_points(model.modules),
        _render_loc_table(model.modules),
        _render_quickstart(),
        _render_revision_history(),
    ]
    return "".join(parts)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--project-model", required=True)
    p.add_argument("--language", default="EN", choices=["JP", "EN", "VN"])
    p.add_argument("--output", required=True)
    args = p.parse_args()

    model = load_project_model(args.project_model)
    text = render_codebase_summary(model, Language(args.language))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Rendered codebase summary -> {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
