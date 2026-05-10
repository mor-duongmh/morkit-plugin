---
description: Generate fresh docs (SRS / API / DB — user picks which) from a ProjectModel JSON. Outputs to ./docs/ in current project. Single-language (JP|EN|VN).
argument-hint: "--project-model <path> --language <JP|EN|VN> [--outputs srs,api,db]"
---

Pre-flight check:

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /morkit:setup first." >&2
  exit 1
}
```

**Ask the user which doc types to generate (BEFORE invoking the orchestrator):**

If the user did NOT pass `--outputs` on the command line, you MUST call **AskUserQuestion** with `multiSelect: true` to let them pick which documents to generate. Do not assume — always ask.

Question template:
- question: "Bạn muốn generate những loại tài liệu nào?"
- header: "Doc types"
- multiSelect: true
- options:
  - label: "SRS", description: "Software Requirements Specification (BrSE template, 13 sections + screen specs)"
  - label: "API docs", description: "REST endpoints + cURL samples + error codes"
  - label: "DB design", description: "Tables, indexes, Mermaid ERD"

Map the user's selection to the `--outputs` flag:
- SRS → `srs`
- API docs → `api`
- DB design → `db`

Join selected codes with commas (e.g. `srs,api` or `srs,api,db`). If the user selects nothing valid, abort with a message and ask again — do NOT fall back to a default.

If `--outputs` WAS provided on the command line, skip the question and use the provided value verbatim.

**Then invoke the orchestrator skill:**

Use the **Skill tool** to invoke `docs-hero-orchestrator` with mode `init`, passing the resolved `--outputs` value plus the other user arguments. The skill will:

1. Parse inputs from `${PWD}/.tmp/` or `--inputs` directory
2. Dispatch to the selected sub-skills only (parallel where safe)
3. Render docs to `${PWD}/docs/`
4. Generate aggregate report
5. Spawn the `docs-hero` QA agent for cross-reference + BrSE-quality validation

Output files:
- `morkit/output/docs/srs.md`
- `morkit/output/docs/api-docs.md`
- `morkit/output/docs/database-design.md`
- `docs/screen-specs/SCREEN-*.md` (per FR with screens)
- `.docs-hero-meta.json` (sidecar, gitignored)
