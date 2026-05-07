---
name: docs-hero
description: "Generate or update full project documentation suite (SRS + API Docs + DB Design) following BrSE standards for ITO Japan. Single entry point orchestrating 3 sub-skills with conflict-minimal updates from OpenSpec changes or brainstorm plans. Supports init / update / sync."
category: documentation
keywords: [docs, srs, api, database, brse, openspec, ito, japan]
argument-hint: "init|update|sync|apply-sync|rebuild-meta [options]"
metadata:
  author: docs-hero
  version: "1.0.0"
---

# Docs Hero Orchestrator

Single entry point for the documentation generation pipeline. Coordinates three
sub-skills (`generate-srs`, `generate-api-docs`, `generate-db-design`) with shared
parsers, the diff engine, atomic write, and a session lock.

## Environment (plugin context)

This skill runs as a Claude Code plugin. Path resolution uses these variables:

```bash
# Plugin root (set by Claude Code at runtime)
CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:?must be set by Claude Code}"

# Python venv (created by /docs-hero:setup)
VENV="${HOME}/.claude/plugins/data/docs-hero/.venv"
PY="${VENV}/bin/python3"

# Skill scripts (within plugin)
ORCH_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/docs-hero-orchestrator/scripts"
SRS_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-srs/scripts"
API_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-api-docs/scripts"
DB_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-db-design/scripts"

# Project paths (always relative to user's cwd, NOT plugin root)
PROJECT_DOCS_DIR="${PWD}/docs"
PROJECT_META="${PWD}/.docs-hero-meta.json"
PROJECT_LOCK="${PWD}/.docs-hero.lock"
PROJECT_TMP="${PWD}/.tmp"
```

**Pre-flight check** every mutating operation must perform:

```bash
test -d "$VENV" || { echo "ERROR: venv missing. Run /docs-hero:setup first." >&2; exit 1; }
```

## Operations

| Command | Purpose |
|---|---|
| `/docs-hero init` | Create docs from inputs (PDF/Excel/Docx/OpenSpec + codebase) |
| `/docs-hero update --from-plan {path}` | Apply changes from a brainstorm plan.md |
| `/docs-hero update --from-openspec [name]` | Apply 1 OpenSpec change |
| `/docs-hero sync` | Generate sync proposals (codebase → docs) — read-only |
| `/docs-hero apply-sync --proposal {path}` | Apply approved sync proposal |
| `/docs-hero rebuild-meta` | Bootstrap `.docs-hero-meta.json` from existing docs |

## Routing Logic

Parse first arg:
- `init` → init flow (collect inputs → parse → render all 3 docs)
- `update` → parse `--from-{plan,openspec}` → Delta → diff engine → apply
- `sync` → fan out to sub-skills' `*_sync_propose.py` (no doc mutation)
- `apply-sync` → call sub-skill's `*_sync_apply.py` to convert proposal → Delta → run update
- `rebuild-meta` → meta-manager rebuild
- empty → AskUserQuestion (5 operations)

## Init Flow

```bash
# Pre-flight
test -d "$VENV" || { echo "ERROR: run /docs-hero:setup first." >&2; exit 1; }
mkdir -p "$PROJECT_TMP"

# 1. Parse inputs → ProjectModel JSON
"$PY" "$ORCH_SCRIPTS/parse_inputs.py" \
  --inputs "$INPUT_DIR" \
  --output "$PROJECT_TMP/raw-bundle.json"

# 2. Dispatch to sub-skills (CLAUDE_PLUGIN_ROOT inherited from env)
"$PY" "$ORCH_SCRIPTS/dispatch_coordinator.py" init \
  --project-model "$PROJECT_TMP/project-model.json" \
  --language EN \
  --outputs srs,api,db \
  --docs-dir "$PROJECT_DOCS_DIR"

# 3. Aggregate report
"$PY" "$ORCH_SCRIPTS/aggregate_report.py" \
  --docs-dir "$PROJECT_DOCS_DIR" \
  --output "$PROJECT_TMP/init-report.md"

# 4. Spawn docs-hero agent for QA review (Skill tool: docs-hero)
```

## Update Flow

```bash
# Pre-flight + lock
test -d "$VENV" || { echo "ERROR: run /docs-hero:setup first." >&2; exit 1; }
"$PY" "$ORCH_SCRIPTS/lock_manager.py" acquire --lock "$PROJECT_LOCK" || exit 1
trap '"$PY" "$ORCH_SCRIPTS/lock_manager.py" release --lock "$PROJECT_LOCK"' EXIT

# 1. Parse delta source
"$PY" "$ORCH_SCRIPTS/parse_plan.py"     --plan "$PLAN_PATH"           --output "$PROJECT_TMP/delta.json"
# OR
"$PY" "$ORCH_SCRIPTS/parse_openspec.py" --change-dir "$OPENSPEC_DIR"  --output "$PROJECT_TMP/delta.json"

# 2. dispatch_coordinator update mode automates: filter delta by entity_type per doc,
#    detect manual edits, compute diff, apply patch.
"$PY" "$ORCH_SCRIPTS/dispatch_coordinator.py" update \
  --delta "$PROJECT_TMP/delta.json" \
  --docs-dir "$PROJECT_DOCS_DIR" \
  --meta "$PROJECT_META"

# 3. Aggregate + spawn docs-hero agent
```

## Sync Flow (2-step)

Step 1 — propose (read-only, no lock):
```bash
"$PY" "$API_SCRIPTS/api_sync_propose.py" \
  --codebase-paths "$CODEBASE_PATHS" \
  --existing-doc "$PROJECT_DOCS_DIR/api-docs.md" \
  --output "$PROJECT_TMP/api-sync-proposal.md"

"$PY" "$DB_SCRIPTS/db_sync_propose.py" \
  --codebase-paths "$CODEBASE_PATHS" \
  --existing-doc "$PROJECT_DOCS_DIR/database-design.md" \
  --output "$PROJECT_TMP/db-sync-proposal.md"
# SRS sync not supported (requirements cannot be inferred from code)
```

Step 2 — apply-sync (after user ticks checkboxes):
```bash
"$PY" "$API_SCRIPTS/api_sync_apply.py" \
  --proposal "$PROJECT_TMP/api-sync-proposal.md" \
  --output "$PROJECT_TMP/api-delta.json"

# Then run standard update flow with the resulting delta
"$PY" "$ORCH_SCRIPTS/dispatch_coordinator.py" update \
  --delta "$PROJECT_TMP/api-delta.json" \
  --docs-dir "$PROJECT_DOCS_DIR" \
  --meta "$PROJECT_META"
```

## Lock Acquisition (mutating ops only)

Before any mutate:
1. `"$PY" "$ORCH_SCRIPTS/lock_manager.py" acquire --lock "$PROJECT_LOCK"`
2. If lock exists + valid (PID alive, < 1h) → exit
3. If stale → cleanup + acquire
4. On exit → release

Read-only ops (sync propose, rebuild-meta verify) skip the lock.

## File Ownership

The orchestrator owns:
- `.docs-hero-meta.json` (sidecar, gitignored)
- `.docs-hero.lock` (transient, gitignored)
- Coordination scripts in `scripts/`

Sub-skills own their respective doc files (see each `SKILL.md`).

## References

- Templates: each sub-skill's `templates/`
- Phase specs: `plans/260503-2222-generate-prd-skill/phase-*.md`
- Schema: `scripts/lib/normalized_schema.py` (Pydantic single source of truth)
- Diff engine: `scripts/compute_diff.py` + `scripts/apply_patch.py`
