---
name: generate-codebase-summary
description: "Generate or update codebase-summary.md (README-style overview: tech stack, repo layout, packages, entry points, LOC by language). Init renders from ProjectModel; update applies a Delta filtered for summary scope (RPO/TCH/PKG/MOD); sync scans the repo for file tree + manifests + LOC and proposes Add/Deprecate."
category: documentation
keywords: [codebase, summary, tech-stack, loc, repo-overview]
argument-hint: "init|update|sync|apply-sync [options]"
metadata:
  author: morkit
  version: "1.0.0"
---

# Generate Codebase Summary Skill

Sub-skill that owns `docs/codebase-summary.md`. Single-language output (JP / EN / VN).

## Environment (plugin context)

```bash
MORKIT_PLUGIN_ROOT="${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:?must be set by Claude Code or MORKIT_PLUGIN_ROOT must be set by Codex}}"
VENV="${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data}}/docs-hero/.venv"
PY="${VENV}/bin/python3"
SUM_SCRIPTS="${MORKIT_PLUGIN_ROOT}/skills/generate-codebase-summary/scripts"
ORCH_SCRIPTS="${MORKIT_PLUGIN_ROOT}/skills/docs-hero-orchestrator/scripts"
PROJECT_DOCS_DIR="${PWD}/docs"
PROJECT_META="${PWD}/.docs-hero-meta.json"
```

## Modes

| Mode | Purpose |
|---|---|
| `init` | Render `docs/codebase-summary.md` from a ProjectModel JSON |
| `update` | Apply Delta filtered for summary scope (RPO / TCH / PKG / MOD) |
| `sync` | Scan repo (file tree + manifests + LOC), write proposal — DOES NOT touch docs |
| `apply-sync` | Read proposal (with user-checked boxes) → convert to Delta |

## Init Workflow

```bash
"$PY" "$SUM_SCRIPTS/render_codebase_summary.py" \
  --project-model "$PROJECT_MODEL" \
  --language EN \
  --output "$PROJECT_DOCS_DIR/codebase-summary.md"
```

Section IDs (stable for diff engine):

```
RPO-001        # Singleton repo overview (§1)
TCH-{id}       # Per tech-stack item (inline in §2)
PKG-{id}       # Per package/workspace (inline in §4)
MOD-{id}       # Per entry-point module (inline in §5)
```

## Sync Workflow (2-step)

### Step 1: propose

```bash
"$PY" "$SUM_SCRIPTS/codebase_summary_sync_propose.py" \
  --codebase-paths "." \
  --existing-doc "$PROJECT_DOCS_DIR/codebase-summary.md" \
  --output "${PWD}/.tmp/codebase-summary-sync-proposal.md"
```

Detects:
- File tree (depth-3, ignores `node_modules`/`.venv`/`dist`/`build`/etc.)
- Pure-Python LOC counter by extension (no `cloc` dependency — flagged as approximate)
- Package manifests: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`,
  `pom.xml`, `Gemfile`, `composer.json`
- Tech-stack inference from manifest contents (declared deps + framework presence)
- Entry points: `main.py`, `index.{js,ts}`, `cmd/*`, `bin/*`,
  `pyproject [project.scripts]`, `package.json bin/main`

### Step 2: apply-sync

```bash
"$PY" "$SUM_SCRIPTS/codebase_summary_sync_apply.py" \
  --proposal "${PWD}/.tmp/codebase-summary-sync-proposal.md" \
  --output "${PWD}/.tmp/codebase-summary-delta.json"
```

## File Ownership

This skill owns:
- `docs/codebase-summary.md`

It does **not** modify:
- Source files / manifests (read-only scan)

## References

- `templates/codebase-summary-template.md`
