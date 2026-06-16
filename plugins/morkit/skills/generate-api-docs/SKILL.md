---
name: generate-api-docs
description: "Generate or update REST API documentation. Init mode renders api-docs.md from ProjectModel; update mode applies a Delta to existing docs; sync is a 2-step propose→apply that scans the codebase and asks the user to pick which discoveries to apply."
category: documentation
keywords: [api-docs, rest, openapi, codebase-sync]
argument-hint: "init|update|sync|apply-sync [options]"
metadata:
  author: docs-hero
  version: "1.0.0"
---

# Generate API Docs Skill

Sub-skill that owns `morkit/output/docs/api-docs.md`. Single-language output (JP / EN / VN).

## Environment (plugin context)

```bash
CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:?must be set by Claude Code}"
VENV="${HOME}/.claude/plugins/data/docs-hero/.venv"
PY="${VENV}/bin/python3"
API_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-api-docs/scripts"
ORCH_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/docs-hero-orchestrator/scripts"
PROJECT_DOCS_DIR="${PWD}/docs"
PROJECT_META="${PWD}/.docs-hero-meta.json"
```

## Modes

| Mode | Purpose |
|---|---|
| `init` | Render `morkit/output/docs/api-docs.md` from a ProjectModel JSON |
| `update` | Apply Delta filtered for API scope (ENDPOINT/ERROR_CODE/WEBHOOK/AUTH/RATE_LIMIT) |
| `sync` | Scan codebase, write a human-readable proposal — DOES NOT touch docs |
| `apply-sync` | Read proposal (with user-checked boxes) → convert to Delta → apply |

## Init Workflow

```bash
"$PY" "$API_SCRIPTS/render_api_docs.py" \
  --project-model "$PROJECT_MODEL" \
  --language JP \
  --output "$PROJECT_DOCS_DIR/api-docs.md"
```

Resource grouping: endpoints whose path shares a first segment go in one section (e.g. `/users`, `/users/{id}` → "Users Resource").

Section IDs (stable for diff engine):

```
ENDPOINT-GET-users
ENDPOINT-GET-users-by-id
ENDPOINT-POST-users
ENDPOINT-DELETE-users-by-id
ERR-USER_NOT_FOUND
WEBHOOK-users-created
```

## Update Workflow

```bash
"$PY" "$ORCH_SCRIPTS/detect_manual_edits.py" \
  --doc "$PROJECT_DOCS_DIR/api-docs.md" --meta "$PROJECT_META" \
  --output "${PWD}/.tmp/api-edits.json"

"$PY" "$ORCH_SCRIPTS/compute_diff.py" \
  --delta "${PWD}/.tmp/api-delta.json" \
  --doc "$PROJECT_DOCS_DIR/api-docs.md" \
  --manual-edits "${PWD}/.tmp/api-edits.json" \
  --output "${PWD}/.tmp/api-plan.json"

"$PY" "$ORCH_SCRIPTS/apply_patch.py" \
  --plan "${PWD}/.tmp/api-plan.json" \
  --doc "$PROJECT_DOCS_DIR/api-docs.md" \
  --meta "$PROJECT_META"
```

## Sync Workflow (2-step, report before add)

### Step 1: propose

```bash
"$PY" "$API_SCRIPTS/api_sync_propose.py" \
  --codebase-paths "$CODEBASE_PATHS" \
  --existing-doc "$PROJECT_DOCS_DIR/api-docs.md" \
  --output "${PWD}/.tmp/api-sync-proposal.md"
```

Generates a markdown proposal with `[ ]` / `[x]` checkboxes for ADD / UPDATE / DEPRECATE candidates. **No doc changes.** User edits the file, ticks checkboxes, then runs apply-sync.

### Step 2: apply-sync

```bash
"$PY" "$API_SCRIPTS/api_sync_apply.py" \
  --proposal "${PWD}/.tmp/api-sync-proposal.md" \
  --output "${PWD}/.tmp/api-delta.json"
```

Parses the proposal, extracts checked items, emits a Delta JSON. The orchestrator then runs the standard update flow with that Delta.

## File Ownership

This skill owns:
- `morkit/output/docs/api-docs.md`

It does **not** modify:
- `morkit/output/docs/srs.md`
- `morkit/output/docs/database-design.md`

## References

- `templates/api-docs-template.md` — full structure reference
- `references/api-docs-conventions.md` — REST patterns + error code conventions
