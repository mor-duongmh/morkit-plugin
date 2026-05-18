---
name: generate-code-standards
description: "Generate or update code-standards.md (Conventional Commits + auto-extracted lint/format rules). Init renders from ProjectModel; update applies a Delta filtered for standards scope (LNT/NAM/CMT/FMT); sync scans the repo for lint/format/commit configs and proposes Add/Deprecate per rule. Honors existing CONTRIBUTING.md by linking, not duplicating."
category: documentation
keywords: [code-standards, lint, formatter, conventional-commits, naming, style-guide]
argument-hint: "init|update|sync|apply-sync [options]"
metadata:
  author: morkit
  version: "1.0.0"
---

# Generate Code Standards Skill

Sub-skill that owns `docs/code-standards.md`. Single-language output (JP / EN / VN).

## Environment (plugin context)

```bash
MORKIT_PLUGIN_ROOT="${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:?must be set by Claude Code or MORKIT_PLUGIN_ROOT must be set by Codex}}"
VENV="${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data}}/docs-hero/.venv"
PY="${VENV}/bin/python3"
STD_SCRIPTS="${MORKIT_PLUGIN_ROOT}/skills/generate-code-standards/scripts"
ORCH_SCRIPTS="${MORKIT_PLUGIN_ROOT}/skills/docs-hero-orchestrator/scripts"
PROJECT_DOCS_DIR="${PWD}/docs"
PROJECT_META="${PWD}/.docs-hero-meta.json"
```

## Modes

| Mode | Purpose |
|---|---|
| `init` | Render `docs/code-standards.md` from a ProjectModel JSON |
| `update` | Apply Delta filtered for standards scope (LNT / NAM / CMT / FMT) |
| `sync` | Scan repo for lint/format/commit configs, write proposal — DOES NOT touch docs |
| `apply-sync` | Read proposal (with user-checked boxes) → convert to Delta |

## Init Workflow

```bash
"$PY" "$STD_SCRIPTS/render_code_standards.py" \
  --project-model "$PROJECT_MODEL" \
  --language EN \
  --output "$PROJECT_DOCS_DIR/code-standards.md"
```

Section IDs (stable for diff engine):

```
LNT-{id}       # Per-lint-config (referenced inline in §4 table)
NAM-{id}       # Per-naming-convention (inline in §3)
CMT-{id}       # Per-commit-policy (inline in §5)
FMT-{id}       # Per-formatting-rule (inline in §2)
```

## Sync Workflow (2-step)

### Step 1: propose

```bash
"$PY" "$STD_SCRIPTS/code_standards_sync_propose.py" \
  --codebase-paths "." \
  --existing-doc "$PROJECT_DOCS_DIR/code-standards.md" \
  --output "${PWD}/.tmp/code-standards-sync-proposal.md"
```

Detects:
- ESLint: `.eslintrc*`, `eslint.config.*`
- Prettier: `.prettierrc*`, `prettier.config.*`
- Python: `pyproject.toml` (`[tool.ruff]` / `[tool.black]` / `[tool.isort]`),
  `.flake8`, `setup.cfg`
- EditorConfig: `.editorconfig`
- TypeScript: `tslint.json`
- Go: `golangci.yml` / `.golangci.yaml`
- Rust: `rustfmt.toml`, `clippy.toml`
- Ruby: `.rubocop.yml`
- Commit policy: `.commitlintrc*`, `commitlint.config.*`, `.husky/commit-msg`,
  `CONTRIBUTING.md` (looks for "Conventional Commits" / "feat:" examples)

`extends` chains are recorded verbatim, not resolved.

### Step 2: apply-sync

```bash
"$PY" "$STD_SCRIPTS/code_standards_sync_apply.py" \
  --proposal "${PWD}/.tmp/code-standards-sync-proposal.md" \
  --output "${PWD}/.tmp/code-standards-delta.json"
```

## File Ownership

This skill owns:
- `docs/code-standards.md`

It does **not** modify:
- `CONTRIBUTING.md` (linked from §1 if detected)
- Lint/format config files (read-only scan)

## References

- `templates/code-standards-template.md`
- Conventional Commits: <https://www.conventionalcommits.org/>
