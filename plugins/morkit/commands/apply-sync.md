---
description: Apply user-approved sync proposal (with ticked checkboxes) — converts to Delta and runs the standard update flow.
argument-hint: "--proposal <path-to-*-sync-proposal.md>"
---

Pre-flight:

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /morkit:setup first." >&2
  exit 1
}
```

Invoke orchestrator skill with mode `apply-sync` + the proposal path. The skill will:

1. Detect the proposal's doc type from its filename and pick the matching
   `*_sync_apply.py` — `api` / `db` / `codebase-summary` / `system-architecture` / `code-standards`
2. Parse proposal → extract checked items only → scoped Delta JSON in `${PWD}/.tmp/<doc>-delta.json`
3. Run standard update flow with that Delta (same as `/morkit:docs-update`) — `run_update`
   routes each entity_type to the right doc
4. Manual edits preserved via diff engine
