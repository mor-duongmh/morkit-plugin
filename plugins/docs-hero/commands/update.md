---
description: Apply OpenSpec change or brainstorm plan to existing docs (SRS/API/DB) — preserves manual edits via diff engine.
argument-hint: "--from-openspec <change-name> | --from-plan <path-to-plan.md>"
---

Pre-flight check:

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /docs-hero:setup first." >&2
  exit 1
}

test -f "${PWD}/.docs-hero-meta.json" || {
  echo "ERROR: .docs-hero-meta.json missing. Run /docs-hero:init first or use rebuild-meta." >&2
  exit 1
}
```

Then invoke the orchestrator skill with mode `update`. Synergy with `spec` plugin:

```
/spec:propose "feature-X"                          # creates openspec/changes/feature-X/...
# (review-checklist gate)
/spec:apply feature-X                              # implements code
/docs-hero:update --from-openspec feature-X        # SRS/API/DB updated atomically
```

The diff engine flow:
1. `parse_openspec.py` (or `parse_plan.py`) → Delta JSON (ADD/UPDATE/DEPRECATE per entity)
2. `detect_manual_edits.py` → identify BrSE manual edits to preserve
3. `compute_diff.py` → compute patch plan
4. `apply_patch.py` → atomic write
5. Spawn `docs-hero` QA agent for verification
