---
description: Apply user-approved sync proposal (with ticked checkboxes) — converts to Delta and runs the standard update flow.
argument-hint: "--proposal <path-to-*-sync-proposal.md>"
---

Pre-flight:

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /docs-hero:setup first." >&2
  exit 1
}
```

Invoke orchestrator skill with mode `apply-sync` + the proposal path. The skill will:

1. Parse proposal → extract checked items only
2. Emit Delta JSON to `${PWD}/.tmp/<api|db>-delta.json`
3. Run standard update flow with that Delta (same as `/docs-hero:update`)
4. Manual edits preserved via diff engine
