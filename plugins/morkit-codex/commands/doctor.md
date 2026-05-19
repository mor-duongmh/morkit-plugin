---
description: Health-check docs-hero install (Python version, venv, deps, schema importable, mmdc availability). Read-only.
---

Run the health check:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.sh"
```

Expected output (all green):

```
=== docs-hero doctor ===
Python: OK (3.X.X)
venv: OK (~/.claude/plugins/data/docs-hero/.venv)
deps: OK (8 packages importable)
schema: OK (ProjectModel + Delta importable)
mmdc: not installed (optional) — agent uses syntax sanity check fallback
=== done ===
```

If `venv: MISSING` → run `/morkit:setup`.
If `deps: FAIL` → re-run `/morkit:setup` to refresh.
`mmdc: not installed` is optional and does NOT block functionality.
