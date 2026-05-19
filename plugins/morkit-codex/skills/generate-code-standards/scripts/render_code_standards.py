"""Render code-standards.md from a ProjectModel JSON.

Generates `docs/code-standards.md` with sections for languages/tooling,
formatting rules, naming conventions, lint config, commit convention,
branch & PR rules, pre-commit hooks, plus an appendix listing detected
config paths.

CLI:
    render_code_standards.py --project-model {path}.json --language EN \
        --output docs/code-standards.md
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))

from lib.normalized_schema import (  # noqa: E402
    CommitPolicy,
    FormattingRule,
    Language,
    LintConfig,
    NamingConvention,
    ProjectModel,
    load_project_model,
)


def _h(level: int, text: str) -> str:
    return f"{'#' * level} {text}\n\n"


def _safe(v, default: str = "_TBD_") -> str:
    return str(v) if v not in (None, "", []) else default


def _title(lang: Language) -> str:
    if lang == Language.JP:
        return "コーディング規約"
    if lang == Language.VN:
        return "Quy chuẩn mã nguồn"
    return "Code Standards"


def _render_meta(model: ProjectModel, lang: Language) -> str:
    today = date.today().isoformat()
    return (
        f"# {_title(lang)} — {model.meta.project_name}\n\n"
        f"| Field | Value |\n|---|---|\n"
        f"| Project | {model.meta.project_name} |\n"
        f"| Version | {model.meta.version} |\n"
        f"| Date | {today} |\n"
        f"| Language | {lang.value} |\n\n"
        "> If `CONTRIBUTING.md` exists at repo root, this document **links** to "
        "it for any topic already covered there — it does not duplicate.\n\n"
    )


def _render_languages(lints: list[LintConfig]) -> str:
    out = _h(2, "1. Languages & Tooling")
    out += "Primary languages and the lint/format toolchain detected.\n\n"
    out += "| Language | Linter | Formatter | Test |\n|---|---|---|---|\n"
    if not lints:
        out += "| _TBD_ | _TBD_ | _TBD_ | _TBD_ |\n\n"
        return out
    # Group lint tools by language guess (file-extension hints in config_path)
    rows: dict[str, dict[str, str]] = {}
    for lc in lints:
        lang = _guess_language(lc)
        slot = rows.setdefault(lang, {"lang": lang, "linter": "", "formatter": "", "test": ""})
        if lc.tool in {"prettier", "black", "ruff-format", "rustfmt", "gofmt"}:
            slot["formatter"] = (slot["formatter"] + ", " + lc.tool).strip(", ")
        else:
            slot["linter"] = (slot["linter"] + ", " + lc.tool).strip(", ")
    for slot in rows.values():
        out += (
            f"| {slot['lang']} | {slot['linter'] or '-'} | {slot['formatter'] or '-'} "
            f"| {slot['test'] or '_TBD_'} |\n"
        )
    out += "\n"
    return out


def _guess_language(lc: LintConfig) -> str:
    p = (lc.config_path or "").lower()
    if "pyproject" in p or ".flake8" in p or "setup.cfg" in p:
        return "Python"
    if "eslint" in p or "prettier" in p or "tslint" in p:
        return "TypeScript / JavaScript"
    if "golangci" in p:
        return "Go"
    if "rustfmt" in p or "clippy" in p:
        return "Rust"
    if "rubocop" in p:
        return "Ruby"
    if "editorconfig" in p:
        return "(any)"
    return "_TBD_"


def _render_formatting(fmts: list[FormattingRule]) -> str:
    out = _h(2, "2. Formatting Rules")
    out += "Auto-extracted from detected config files.\n\n"
    out += "| ID | Tool | Option | Value | Source |\n|---|---|---|---|---|\n"
    if not fmts:
        out += "| FMT-001 | _TBD_ | _TBD_ | _TBD_ | _TBD_ |\n\n"
        return out
    for f in fmts:
        out += (
            f"| {f.id} | {f.tool} | `{f.option}` | `{f.value}` | "
            f"{_safe(f.source_path)} |\n"
        )
    out += "\n"
    return out


def _render_naming(nams: list[NamingConvention]) -> str:
    out = _h(2, "3. Naming Conventions")
    out += "| ID | Scope | Pattern | Example |\n|---|---|---|---|\n"
    if not nams:
        out += (
            "| NAM-001 | file | `kebab-case` | `user-service.ts` |\n"
            "| NAM-002 | class | `PascalCase` | `UserService` |\n"
            "| NAM-003 | function | `camelCase` | `getUser()` |\n"
            "| NAM-004 | const | `UPPER_SNAKE` | `MAX_RETRIES` |\n\n"
        )
        return out
    for n in nams:
        out += f"| {n.id} | {n.scope} | `{n.pattern}` | `{_safe(n.example)}` |\n"
    out += "\n"
    return out


def _render_lints(lints: list[LintConfig]) -> str:
    out = _h(2, "4. Lint Configuration")
    out += (
        "Detected lint configs. `extends` chains are listed verbatim and "
        "**not** resolved (avoids needing dependency installs at scan time).\n\n"
    )
    out += "| ID | Tool | Config Path | Extends |\n|---|---|---|---|\n"
    if not lints:
        out += "| LNT-001 | _TBD_ | _TBD_ | - |\n\n"
        return out
    for lc in lints:
        ext = ", ".join(f"`{e}`" for e in lc.extends) or "-"
        out += f"| {lc.id} | {lc.tool} | `{lc.config_path}` | {ext} |\n"
    out += "\n"
    return out


def _render_commits(commits: list[CommitPolicy]) -> str:
    out = _h(2, "5. Commit Convention")
    out += (
        "Default: [Conventional Commits](https://www.conventionalcommits.org/).\n\n"
        "```\n"
        "<type>(<scope>): <short summary>\n\n"
        "<body>\n\n"
        "<footer>\n"
        "```\n\n"
    )
    if not commits:
        out += (
            "**Allowed types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, "
            "`test`, `build`, `ci`, `chore`, `revert`.\n\n"
            "**Examples**:\n"
            "- `feat(auth): add JWT refresh endpoint`\n"
            "- `fix(db): null check on user lookup`\n\n"
            "| ID | Style | Allowed Types | Scope Required |\n|---|---|---|---|\n"
            "| CMT-001 | conventional | feat,fix,docs,style,refactor,perf,test,build,ci,chore,revert | No |\n\n"
        )
        return out
    out += "| ID | Style | Allowed Types | Scope Required |\n|---|---|---|---|\n"
    for c in commits:
        types = ", ".join(c.allowed_types) or "-"
        out += (
            f"| {c.id} | {c.style} | {types} | "
            f"{'Yes' if c.scope_required else 'No'} |\n"
        )
    out += "\n"
    for c in commits:
        if c.example:
            out += f"- Example for {c.id}: `{c.example}`\n"
    out += "\n"
    return out


def _render_branch_pr() -> str:
    out = _h(2, "6. Branch & PR Rules")
    out += (
        "- **Branch naming**: `{type}/{short-desc}` (e.g. `feat/auth-jwt`)\n"
        "- **PR title**: matches the squash-commit format (Conventional Commits)\n"
        "- **Merge strategy**: squash + merge to `main`\n"
        "- **Review**: at least 1 reviewer; required CI checks must pass\n"
        "- **Force-push**: forbidden on shared branches\n\n"
    )
    return out


def _render_hooks(lints: list[LintConfig]) -> str:
    out = _h(2, "7. Pre-commit Hooks")
    husky = [lc for lc in lints if "husky" in (lc.config_path or "").lower()]
    if husky:
        out += "Detected Husky hooks:\n\n"
        out += "| Hook | Source |\n|---|---|\n"
        for lc in husky:
            out += f"| {lc.tool} | `{lc.config_path}` |\n"
        out += "\n"
    else:
        out += (
            "| Hook | Tool | What it runs |\n|---|---|---|\n"
            "| pre-commit | _TBD_ | _TBD_ |\n\n"
        )
    return out


def _render_appendix(lints: list[LintConfig]) -> str:
    out = "## Appendix: Detected Config Paths\n\n"
    out += (
        "For human cross-reference. Listed paths are **not** parsed beyond "
        "what's already summarized in §2 / §4.\n\n"
    )
    out += "| Tool | Path |\n|---|---|\n"
    if not lints:
        out += "| _TBD_ | _TBD_ |\n\n"
    else:
        for lc in lints:
            out += f"| {lc.tool} | `{lc.config_path}` |\n"
        out += "\n"
    return out


def _render_revision_history() -> str:
    return (
        "## Revision History\n\n"
        "| Version | Date | Author | Changes |\n"
        "|---|---|---|---|\n"
        f"| 1.0 | {date.today().isoformat()} | morkit (auto) | Initial generation |\n"
    )


def render_code_standards(model: ProjectModel, lang: Language) -> str:
    parts = [
        _render_meta(model, lang),
        _render_languages(model.lint_configs),
        _render_formatting(model.formatting_rules),
        _render_naming(model.naming_conventions),
        _render_lints(model.lint_configs),
        _render_commits(model.commit_policies),
        _render_branch_pr(),
        _render_hooks(model.lint_configs),
        _render_appendix(model.lint_configs),
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
    text = render_code_standards(model, Language(args.language))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Rendered code standards -> {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
