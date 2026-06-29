---
description: Single entry for doc generation. Asks project type — greenfield (build docs from requirements/customer docs via the BA pipeline) or brownfield (render docs from a ProjectModel against an existing codebase) — then routes. Outputs to ./docs/. Single-language (JP|EN|VN).
argument-hint: "[--type greenfield|brownfield] [--project-model <path>] [--language <JP|EN|VN>] [--outputs srs,api,db,arch,standards,summary,guidelines]"
---

Pre-flight check:

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /morkit:setup first." >&2
  exit 1
}
```

## Step 0 — Project type (routing — do this FIRST)

Decide the starting point before anything else:

- If `--type greenfield` or `--type brownfield` was passed, use it.
- If the user invoked `/morkit:greenfield`, treat as `greenfield`.
- Otherwise call **AskUserQuestion** (single-select):
  - question: "Điểm xuất phát của dự án?"
  - header: "Project type"
  - options:
    - label: "Greenfield — từ tài liệu yêu cầu", description: "Dự án mới: có tài liệu khách hàng / yêu cầu, chưa (hoặc ít) code. Chạy pipeline BA G0→G7: brainstorm → user stories → gap/risk → clarify → ProjectModel → docs."
    - label: "Brownfield — từ code/model sẵn có", description: "Đã có codebase và/hoặc ProjectModel JSON (hoặc inputs). Render thẳng bộ docs, có quét repo dò trạng thái implement."

Route on the answer:
- **greenfield** → invoke the `greenfield-orchestrator` skill via the **Skill tool**, passing through any args (`<proj>`, `--format`, `--lang`, `--resume`). That pipeline owns the full G0→G7 flow and renders the docs itself at G6/G7. **Stop here — do NOT run the brownfield flow below.**
- **brownfield** → continue with the flow below.

---

## Brownfield flow — render from a ProjectModel (+ repo scan)

**Ask the user which doc types to generate (BEFORE invoking the orchestrator):**

If the user did NOT pass `--outputs` on the command line, you MUST call **AskUserQuestion** to let them pick which documents to generate. Do not assume — always ask.

There are 7 doc types but `AskUserQuestion` allows at most **4 options per question**. Send BOTH questions below in a **single AskUserQuestion call** (the `questions` array holds both), each with `multiSelect: true`. Then take the **union** of the two answers as the full selection.

Question 1 — spec & structure docs:
- question: "Tài liệu spec & cấu trúc nào?"
- header: "Spec docs"
- multiSelect: true
- options:
  - label: "SRS", description: "Software Requirements Specification (BrSE template, 13 sections + screen specs)"
  - label: "API docs", description: "REST endpoints + cURL samples + error codes"
  - label: "DB design", description: "Tables, indexes, Mermaid ERD"
  - label: "System Architecture", description: "arc42-lite (8 sections) + Mermaid component diagram"

Question 2 — standards & design docs:
- question: "Tài liệu chuẩn & thiết kế nào?"
- header: "Standards docs"
- multiSelect: true
- options:
  - label: "Code Standards", description: "Conventional Commits + auto-extracted lint/format rules"
  - label: "Codebase Summary", description: "README-style: tech stack, repo layout, packages, entry points, LOC by language"
  - label: "Design Guidelines", description: "Design Principles + Patterns + ADRs (MADR format)"

Map the user's combined selection (union of both questions) to the `--outputs` flag:
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
7. Render docs. `srs` + `guidelines` render straight to `${PWD}/docs/`; the 5 code-derived docs (`api`, `db`, `arch`, `standards`, `summary`) render to a **staging** dir (`${PWD}/.tmp/staged/`) instead.
7b. **Review Gate (per-doc loop) — human approval before promote.** For each staged code-derived doc, run the loop defined in `docs-hero-orchestrator/SKILL.md` → "Review Gate (per-doc loop)": `snapshot` baseline → `surface` (section list + ⚠ flags) → **AskUserQuestion `[Approve | Sửa tiếp]`** → on Approve, `promote` into `docs/`; on Sửa tiếp, the reviewer edits the staged file (or gives feedback to re-render) and the loop repeats. `design-guidelines` gets a light one-step confirm `[OK | Sửa | Bỏ]`. **Warn-only:** docs left un-approved are simply not promoted and are reported at the end — coding is never blocked. Re-running `init` resumes (already-approved docs are skipped).
8. Generate aggregate report over the **promoted** docs; Claude then appends a "Gaps & Risks" section copying the unresolved entries (placeholder + assumption) from `docs-plan.md`.
9. Spawn the `docs-reviewer` QA agent for cross-reference + BrSE-quality validation. The agent verifies every blocker/warning gap in `docs-plan.md` is either resolved or explicitly carried forward as `<TBD: …>`, and cross-checks that the Implementation Status snapshot in SRS §3 matches the project-model values.

Output files (per selected output):

| Output flag | File(s) written |
|---|---|
| `srs` | `docs/srs.md` + `docs/screen-specs/SCREEN-*.md` (per screen) + `docs/srs.html` (Mor-themed stakeholder view; default on, disable with `--no-visualize`) |
| `api` | `docs/api-docs.md` |
| `db` | `docs/database-design.md` |
| `arch` | `docs/system-architecture.md` |
| `standards` | `docs/code-standards.md` |
| `summary` | `docs/codebase-summary.md` |
| `guidelines` | `docs/design-guidelines.md` + `docs/adr/{ADR-id}-{slug}.md` (per ADR) |

Sidecar: `.docs-hero-meta.json` (gitignored).
