---
description: Generate fresh SRS + API docs + DB design from a ProjectModel JSON. Outputs to ./docs/ in current project. Single-language (JP|EN|VN).
argument-hint: "--project-model <path> --language <JP|EN|VN> [--outputs srs,api,db]"
---

Pre-flight check:

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /docs-hero:setup first." >&2
  exit 1
}
```

Then invoke the orchestrator skill:

Use the **Skill tool** to invoke `docs-hero-orchestrator` with mode `init` and pass through the user-provided arguments. The skill will:

1. Parse inputs from `${PWD}/.tmp/` or `--inputs` directory
2. Dispatch to sub-skills (parallel where safe)
3. Render docs to `${PWD}/docs/`
4. Generate aggregate report
5. Spawn the `docs-hero` QA agent for cross-reference + BrSE-quality validation

Output files:
- `docs/srs.md`
- `docs/api-docs.md`
- `docs/database-design.md`
- `docs/screen-specs/SCREEN-*.md` (per FR with screens)
- `.docs-hero-meta.json` (sidecar, gitignored)
