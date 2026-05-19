---
name: generate-db-design
description: "Generate or update database design document with Mermaid ERD. Init mode renders database-design.md from ProjectModel; update mode applies a Delta to existing docs; sync is a 2-step propose→apply that scans ORM models in the codebase."
category: documentation
keywords: [database, erd, mermaid, schema, migration]
argument-hint: "init|update|sync|apply-sync [options]"
metadata:
  author: docs-hero
  version: "1.0.0"
---

# Generate DB Design Skill

Sub-skill that owns `morkit/output/docs/database-design.md`. Single-language output (JP / EN / VN).
Embeds a Mermaid `erDiagram` for tables + relationships.

## Environment (plugin context)

```bash
MORKIT_PLUGIN_ROOT="${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:?must be set by Claude Code or MORKIT_PLUGIN_ROOT must be set by Codex}}"
VENV="${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data}}/docs-hero/.venv"
PY="${VENV}/bin/python3"
DB_SCRIPTS="${MORKIT_PLUGIN_ROOT}/skills/generate-db-design/scripts"
ORCH_SCRIPTS="${MORKIT_PLUGIN_ROOT}/skills/docs-hero-orchestrator/scripts"
PROJECT_DOCS_DIR="${PWD}/docs"
PROJECT_META="${PWD}/.docs-hero-meta.json"
```

## Modes

| Mode | Purpose |
|---|---|
| `init` | Render `morkit/output/docs/database-design.md` from a ProjectModel JSON |
| `update` | Apply Delta filtered for DB scope (TABLE/INDEX/REL/ENUM) |
| `sync` | Scan ORM models in codebase, write proposal — DOES NOT touch docs |
| `apply-sync` | Read proposal (with user-checked boxes) → convert to Delta |

## Init Workflow

```bash
"$PY" "$DB_SCRIPTS/render_db_design.py" \
  --project-model "$PROJECT_MODEL" \
  --language JP \
  --output "$PROJECT_DOCS_DIR/database-design.md"
```

Section IDs (stable for diff engine):

```
TBL-{id}        # Per-table H3 anchor (e.g. TBL-001, TBL-USERS)
IDX-{id}        # Per-index
REL-{id}        # Per-relationship
ENUM-{id}       # Per-enum
ERD             # Single Mermaid block
```

## Update Workflow

The orchestrator pre-filters Delta to DB scope, then runs the standard diff-engine
flow (detect_manual_edits → compute_diff → apply_patch).

## Sync Workflow (2-step)

### Step 1: propose

```bash
"$PY" "$DB_SCRIPTS/db_sync_propose.py" \
  --codebase-paths "$CODEBASE_PATHS" \
  --existing-doc "$PROJECT_DOCS_DIR/database-design.md" \
  --output "${PWD}/.tmp/db-sync-proposal.md"
```

Scans Prisma / TypeORM / Sequelize / Django / SQLAlchemy / GORM / raw SQL models,
diffs with documented tables, writes a markdown proposal with `[ ]` checkboxes.
**No doc changes.**

### Step 2: apply-sync

```bash
"$PY" "$DB_SCRIPTS/db_sync_apply.py" \
  --proposal "${PWD}/.tmp/db-sync-proposal.md" \
  --output "${PWD}/.tmp/db-delta.json"
```

Parses checked items, emits Delta JSON for the standard update flow.

## File Ownership

This skill owns:
- `morkit/output/docs/database-design.md`

It does **not** modify:
- `morkit/output/docs/srs.md`
- `morkit/output/docs/api-docs.md`

## References

- `templates/database-design-template.md` — full structure reference
- `references/mermaid-erd-syntax.md` — Mermaid ERD cheat sheet
