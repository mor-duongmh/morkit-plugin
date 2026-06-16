"""Tests for generate-code-standards sub-skill."""
from __future__ import annotations

import sys
from pathlib import Path

_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))

_STD = Path(__file__).resolve().parents[2] / "generate-code-standards" / "scripts"
sys.path.insert(0, str(_STD))

from code_standards_sync_apply import parse_proposal  # noqa: E402
from code_standards_sync_propose import (  # noqa: E402
    diff_configs,
    parse_existing_lint_ids,
    render_proposal,
)
from lib.normalized_schema import (  # noqa: E402
    CommitPolicy,
    FormattingRule,
    Language,
    LintConfig,
    NamingConvention,
    ProjectMeta,
    ProjectModel,
)
from parse_codebase_lint import LintConfigDef, scan_lint_configs  # noqa: E402
from render_code_standards import render_code_standards  # noqa: E402


def _build_minimal_standards_model() -> ProjectModel:
    return ProjectModel(
        meta=ProjectMeta(project_name="TestStd", version="1.0"),
        lint_configs=[
            LintConfig(id="LNT-eslint", tool="eslint", config_path=".eslintrc.json",
                       extends=["eslint:recommended"]),
            LintConfig(id="LNT-ruff", tool="ruff", config_path="pyproject.toml"),
        ],
        formatting_rules=[
            FormattingRule(id="FMT-001", tool="ruff", option="line-length",
                           value="100", source_path="pyproject.toml"),
        ],
        naming_conventions=[
            NamingConvention(id="NAM-001", scope="class", pattern="PascalCase",
                             example="UserService"),
        ],
        commit_policies=[
            CommitPolicy(id="CMT-001", style="conventional",
                         allowed_types=["feat", "fix", "docs"], example="feat(api): add"),
        ],
    )


# --- Renderer ---


def test_render_standards_top_sections():
    model = _build_minimal_standards_model()
    text = render_code_standards(model, Language.EN)
    assert text.startswith("# Code Standards — TestStd")
    for heading in (
        "## 1. Languages & Tooling",
        "## 2. Formatting Rules",
        "## 3. Naming Conventions",
        "## 4. Lint Configuration",
        "## 5. Commit Convention",
        "## 6. Branch & PR Rules",
        "## 7. Pre-commit Hooks",
        "## Appendix: Detected Config Paths",
    ):
        assert heading in text, f"missing {heading!r}"
    # Lint IDs surface in §4 table
    assert "LNT-eslint" in text
    assert "LNT-ruff" in text
    # Extends listed verbatim, not resolved
    assert "`eslint:recommended`" in text
    # Naming + commit data flow through
    assert "PascalCase" in text
    assert "feat(api): add" in text


def test_render_standards_empty_model_uses_placeholders():
    pm = ProjectModel(meta=ProjectMeta(project_name="Empty"))
    text = render_code_standards(pm, Language.EN)
    # Default 4-row Naming table appears when empty
    assert "NAM-001" in text and "NAM-002" in text
    # Default conventional commit policy block appears
    assert "CMT-001" in text
    # Lint placeholder
    assert "| LNT-001 | _TBD_" in text


def test_render_standards_jp_title():
    model = _build_minimal_standards_model()
    text = render_code_standards(model, Language.JP)
    assert text.startswith("# コーディング規約")


# --- Scanner ---


def test_scan_lint_configs_eslint_extends(tmp_path):
    (tmp_path / ".eslintrc.json").write_text(
        '{"extends": ["eslint:recommended", "prettier"], "rules": {}}',
        encoding="utf-8",
    )
    cfgs = scan_lint_configs([str(tmp_path)])
    eslint = next(c for c in cfgs if c.tool == "eslint")
    assert "eslint:recommended" in eslint.extends
    assert "prettier" in eslint.extends


def test_scan_lint_configs_pyproject_subsections(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[tool.ruff]\nline-length = 100\n\n[tool.black]\nline-length = 100\n",
        encoding="utf-8",
    )
    cfgs = scan_lint_configs([str(tmp_path)])
    tools = {c.tool for c in cfgs}
    assert "ruff" in tools
    assert "black" in tools


def test_scan_lint_configs_contributing_conventional_hint(tmp_path):
    (tmp_path / "CONTRIBUTING.md").write_text(
        "# Contributing\n\nWe use **Conventional Commits** for messages.\n"
        "Example: `feat(auth): add JWT refresh`.\n",
        encoding="utf-8",
    )
    cfgs = scan_lint_configs([str(tmp_path)])
    hint = next((c for c in cfgs if c.tool == "conventional-commits-hint"), None)
    assert hint is not None
    assert "CONTRIBUTING.md" in hint.config_path


def test_scan_lint_configs_ignores_node_modules(tmp_path):
    nm = tmp_path / "node_modules" / "some-pkg"
    nm.mkdir(parents=True)
    (nm / ".eslintrc.json").write_text("{}", encoding="utf-8")
    cfgs = scan_lint_configs([str(tmp_path)])
    assert cfgs == []


# --- Sync propose / apply ---


def test_diff_configs_add_and_deprecate():
    code = [
        LintConfigDef(id="LNT-new", tool="eslint", config_path=".eslintrc.json"),
        LintConfigDef(id="LNT-keep", tool="prettier", config_path=".prettierrc.json"),
    ]
    doc_ids = {"LNT-keep", "LNT-old"}
    to_add, to_dep = diff_configs(code, doc_ids)
    assert [c.id for c in to_add] == ["LNT-new"]
    assert to_dep == ["LNT-old"]


def test_render_standards_proposal_has_checkboxes(tmp_path):
    code = [LintConfigDef(id="LNT-new", tool="eslint",
                          config_path=".eslintrc.json", extends=["eslint:recommended"])]
    text = render_proposal([str(tmp_path)], tmp_path / "fake.md", code, code, ["LNT-old"])
    assert "[ ] ADD LNT-new" in text
    assert "[ ] DEPRECATE LNT-old" in text
    assert "`eslint:recommended`" in text


def test_parse_standards_proposal_picks_only_checked():
    proposal = (
        "### [x] ADD LNT-eslint\n"
        "- Tool: `eslint`\n"
        "- Config Path: `.eslintrc.json`\n\n"
        "### [ ] ADD LNT-skipped\n"
        "- Tool: `tslint`\n\n"
        "### [X] DEPRECATE LNT-old\n"
    )
    changes = parse_proposal(proposal)
    assert len(changes) == 2
    by_id = {c.entity_id: c for c in changes}
    assert by_id["LNT-eslint"].op == "ADD"
    assert by_id["LNT-eslint"].payload == {
        "tool": "eslint", "config_path": ".eslintrc.json"
    }
    assert by_id["LNT-old"].op == "DEPRECATE"


def test_parse_existing_lint_ids_finds_inline_refs(tmp_path):
    doc = tmp_path / "code-standards.md"
    doc.write_text(
        "## 4. Lint Configuration\n\n"
        "| ID | Tool | Path |\n|---|---|---|\n"
        "| LNT-eslint | eslint | `.eslintrc.json` |\n"
        "| LNT-ruff | ruff | `pyproject.toml` |\n",
        encoding="utf-8",
    )
    ids = parse_existing_lint_ids(doc)
    assert ids == {"LNT-eslint", "LNT-ruff"}
