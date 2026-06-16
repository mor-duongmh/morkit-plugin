---
description: Generate fresh docs (SRS / API / DB / system-architecture / code-standards / codebase-summary / design-guidelines — user picks which) from a ProjectModel JSON. Outputs to ./docs/ in current project. Single-language (JP|EN|VN).
argument-hint: "--project-model <path> --language <JP|EN|VN> [--outputs srs,api,db,arch,standards,summary,guidelines]"
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
  - label: "System Architecture", description: "arc42-lite (8 sections) + Mermaid component diagram"
  - label: "Code Standards", description: "Conventional Commits + auto-extracted lint/format rules"
  - label: "Codebase Summary", description: "README-style: tech stack, repo layout, packages, entry points, LOC by language"
  - label: "Design Guidelines", description: "Design Principles + Patterns + ADRs (MADR format)"

Map the user's selection to the `--outputs` flag:
- SRS → `srs`
- API docs → `api`
- DB design → `db`
- System Architecture → `arch`
- Code Standards → `standards`
- Codebase Summary → `summary`
- Design Guidelines → `guidelines`

Join selected codes with commas (e.g. `srs,api,arch` or `srs,api,db,arch,standards,summary,guidelines`). If the user selects nothing valid, abort with a message and ask again — do NOT fall back to a default.

If `--outputs` WAS provided on the command line, skip the question and use the provided value verbatim.

**Then invoke the orchestrator skill:**

Use the **Skill tool** to invoke `docs-hero-orchestrator` with mode `init`, passing the resolved `--outputs` value plus the other user arguments. The skill will:

1. Parse inputs from `${PWD}/.tmp/` or `--inputs` directory → `project-model.json`
2. **Implementation status detection** (populates `FR.impl_status` + `FR.evidence_refs` BEFORE rendering):
   - Scan `openspec/changes/` and `openspec/specs/`: an FR-ID referenced by an archived change → `Done`; pending change → `InProgress`; spec-only mention → `InProgress` with `kind: openspec` evidence.
   - Scan tracked source files + `git log --grep` for FR-IDs (e.g. `FR-001`): hits → at least `InProgress` with `kind: code` or `kind: commit` evidence.
   - Scan test files (path matches `**/test*` or `**/*spec.*`) for FR-IDs: hits → bump to `Verified` with `kind: test` evidence.
   - **Manual override wins**: if `project-model.json` already specifies `impl_status` for an FR (set by the user in inputs), do NOT overwrite — auto-detect only fills `NotStarted` entries.
   - Default for FRs with no signal at all: `NotStarted`.
3. **Gap & Risk analysis (REQUIRED gate before any doc rendering):** Claude reads `project-model.json` plus the raw inputs and writes `${PWD}/.tmp/docs-plan.md` containing **in this order**:
   - **§0 Project Overview**: 1-paragraph "what it is", current phase (greenfield / MVP / scaling / legacy refactor), inferred stack, stakeholders mentioned in inputs, doc maturity in this repo (which docs already exist), source input quality assessment (per-input notes on completeness/conflicts), entity counts, render strategy (which input is primary source for each doc).
   - **§1 Per-doc plan**: for each selected output (srs / api / db), the sections that will be generated and which entities feed each section.
   - **§2 Gaps**: missing/ambiguous inputs that block or weaken a section (e.g. FR without acceptance criteria, endpoint without request schema, table without PK, undefined NFR thresholds). Each gap tagged with severity (blocker / warning / info) and the doc section it affects.
   - **§3 Risks**: scope creep, conflicting requirements, undocumented external dependencies, unclear stakeholders, language/terminology drift.
   - **§4 Implementation Status Snapshot**: the auto-detection result from step 2 — counts by status (Done / InProgress / Verified / Blocked / NotStarted) and a per-FR table (FR-ID, status, evidence summary). This previews what §3 of the SRS will show.
   - **§5 Recommended action per gap**: ask user, fill placeholder `<TBD: …>`, drop the section, or proceed with assumption (assumption stated explicitly).
4. **Plan approval gate**: present a short summary of `docs-plan.md` to the user via **AskUserQuestion** with options: `Proceed`, `Revise plan` (user gives feedback, Claude rewrites the plan), `Abort`. Do NOT skip this gate. Only on `Proceed` continue.
5. **Apply plan decisions to `project-model.json` BEFORE dispatch**: for each gap whose action is `placeholder`, set the affected field to `<TBD: <reason>>`; for `drop section`, remove the entity; for `assumption`, prefix the description with `[ASSUMPTION] `. This way the existing sub-skills render the right markers without needing new flags.
6. Dispatch to the selected sub-skills only (parallel where safe). The `generate-srs` sub-skill consumes the `impl_status` / `evidence_refs` populated in step 2 and renders the §3 dashboard + Impl Status column automatically — no extra flag needed.
7. Render docs to `${PWD}/docs/`
8. Generate aggregate report; Claude then appends a "Gaps & Risks" section copying the unresolved entries (placeholder + assumption) from `docs-plan.md`.
9. Spawn the `docs-hero` QA agent for cross-reference + BrSE-quality validation. The agent verifies every blocker/warning gap in `docs-plan.md` is either resolved or explicitly carried forward as `<TBD: …>`, and cross-checks that the Implementation Status snapshot in SRS §3 matches the project-model values.

Output files (per selected output):

| Output flag | File(s) written |
|---|---|
| `srs` | `docs/srs.md` + `docs/screen-specs/SCREEN-*.md` (per screen) |
| `api` | `docs/api-docs.md` |
| `db` | `docs/database-design.md` |
| `arch` | `docs/system-architecture.md` |
| `standards` | `docs/code-standards.md` |
| `summary` | `docs/codebase-summary.md` |
| `guidelines` | `docs/design-guidelines.md` + `docs/adr/{ADR-id}-{slug}.md` (per ADR) |

Sidecar: `.docs-hero-meta.json` (gitignored).
