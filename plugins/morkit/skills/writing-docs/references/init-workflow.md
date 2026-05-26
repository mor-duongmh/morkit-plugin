# Init Workflow

`/morkit:init [path] [--scope project|module] [--yes]`

Create the initial doc taxonomy for a codebase. Core principle: **Scout → Content → MAP** (never write a MAP before its content exists), and create a folder only when scout finds the matching component.

Load `taxonomy.md` + `anchor-conventions.md` before generating. Templates: `references/doc-templates/`.

## Stage 0 — Preflight & Scope

1. Check `docs/` at the target path:
   - already a new-style taxonomy (`00-overview/` exists) → **STOP**, tell user to run `/morkit:docs update` (init is first-time only).
   - flat legacy docs (`project-overview-pdr.md`, `codebase-summary.md`, …) → mark **MIGRATE** (handle at Stage 6).
   - empty / no `docs/` → proceed.
2. **Scale: ALWAYS ask the user** (AskUserQuestion: project-level vs per-module) unless `--scope` was passed. Surface monorepo markers found (`pnpm-workspace.yaml`, `packages/*`, `apps/*`, `go.work`, lerna) as hints in the question.

## Stage 1 — Scout (read-only, parallel)

Dispatch morkit-native (Task tool / `dispatching-parallel-agents`). Skip `.git`, `node_modules`, `vendor`, `dist`, `__pycache__`, secrets. Collect:
- directory tree + LOC by dir/language · entry points · tech stack (from manifest)
- routes/endpoints · data models/schema/migrations · UI components
- test setup · lint/format/commit config · CI

Map signals → conditional folders (see `taxonomy.md` table): schema→20-data, routes→30-api, UI→40-ui, lint/commit→CODE-STANDARDS, manifest→STACK.

## Stage 2 — Docs Plan + GATE

Build a docs-plan: folders/files to create (core + detected conditional) + provisional feature list + chosen scale. Present **Proceed / Adjust (pick folders, scope) / Abort** via AskUserQuestion. **Skip the gate if `--yes`.**

## Stage 3 — Generate Content (FIRST)

Dispatch parallel by group with **distinct file ownership** (no overlapping edits):
- `10-requirements/` — FEATURE-LIST (from features/routes), USER-FLOWS index + `flows/FR-NNN-*` (user-facing)
- `20-design/` — ARCHITECTURE (arc42-lite), INVARIANTS, one `*-SYS-SPEC` per feature, DATA/API/UI-MAP (conditional), ADR (if decisions exist)
- `30-test/` — TEST-STRATEGY, TEST-RUNBOOK, TEST-MATRIX (from test scan)
- `40-ai-coding/` — CODE-STANDARDS (from lint/commit), KNOWN-PITFALLS, RISK-REGISTER, COMMON-CHANGE-PLAYBOOKS, CODE-SEARCH-GUIDE
- `00-overview/` content — SCOPE, STACK, GLOSSARY, DEPENDENCY-MAP

Each file: minimal front-matter (`source_files` where derived from code) + content + boundary line + cross-link placeholders. Target ~100 LOC.

## Stage 4 — Generate Anchors (AFTER content)

From the content written in Stage 3, generate the indexes so links resolve to real files:
- `00-overview/SOURCE-MAP` (concern→file→symbol→code-search-keywords)
- `00-overview/DOCUMENT-MAP` (directory roles + read paths + canonical source rules)
- `20-design/DESIGN-MAP`, `40-ai-coding/AI-CODING-GUIDE` (meta-index → links), README (root thin + per-folder)

## Stage 4b — Generate Agent Instructions (AFTER anchors)

Now that the MAP/guide files exist, write the root pointer per `references/agent-instructions.md`:
- Build the **B-refined block**: orientation (1–2 sentences, sourced from the DOCUMENT-MAP/README opening line) + 3 task pointers (DOCUMENT-MAP, AI-CODING-GUIDE, INVARIANTS). Drop a pointer if its target was not generated.
- Apply the state machine: `[A]` create / `[B]` append at end / `[C]` replace inside marker. Never touch content outside the marker block.
- Write the harness's agent-instruction file (`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex); add the other when detected (existing file / its config / `--agents`).
- Approve gate per file (AskUserQuestion + Edit diff).
- per-module scope: repeat for each module root, pointing to that module's docs.

## Stage 5 — Validate

- Size: each file ~100 LOC; >800 → split.
- Cross-links: every relative link resolves to an existing file (no broken links). Include the `CLAUDE.md`/`AGENTS.md` pointer links.
- Front-matter present where required (`source_files` on code-derived docs).
- Traceability: FR/NFR/INV IDs consistent; TEST-MATRIX.Ref codes exist.
- Output a short report: what was created, gaps, oversize files.

## Stage 6 — Migrate (only if Stage 0 found legacy docs)

Ask the user: absorb legacy content into the new taxonomy / keep side-by-side / skip. Do not delete legacy files without confirmation.
