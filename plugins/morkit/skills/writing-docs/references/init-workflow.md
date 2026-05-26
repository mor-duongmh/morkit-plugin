# Init Workflow

`/morkit:init [path] [--scope project|module] [--yes] [--agents]`

Create the initial doc taxonomy for a codebase. Core principle: **Scout → Content → MAP** (never write a MAP before its content exists), and create a folder only when scout finds the matching component.

Load `taxonomy.md` + `anchor-conventions.md` before generating. Templates: `references/doc-templates/`.

## Examples

```bash
# First-time bootstrap of docs/ for the current project (asks project vs per-module scale)
/morkit:init

# Bootstrap docs for a project in another directory, skip the post-scout gate
/morkit:init ../new-service --yes

# Monorepo: per-module taxonomy, also write the AGENTS.md pointer
/morkit:init --scope module --agents
```

After init, maintain the set with `/morkit:docs update` (refresh against code changes) or `/morkit:docs summarize` (quick MAP refresh).

## Stage 0 — Preflight & Scope

1. Check `docs/` at the target path:
   - already a new-style taxonomy (`00-overview/` exists) → **STOP**, tell user to run `/morkit:docs update` (init is first-time only).
   - flat legacy docs (`project-overview-pdr.md`, `codebase-summary.md`, …) → mark **MIGRATE** (handle at Stage 6).
   - empty / no `docs/` → proceed.
2. **Greenfield vs brownfield — check the CODE** (this decides which pipeline runs; `docs/` state alone does NOT):
   - **greenfield** when BOTH hold: no recognized build manifest (`package.json`, `pyproject.toml`/`setup.py`, `go.mod`, `Cargo.toml`, `pom.xml`/`build.gradle`, `composer.json`, `Gemfile`, `*.csproj`, …) AND ~0 source-file LOC (ignore `.git`, `README*`, `LICENSE*`, dotfiles/config, `docs/`).
   - manifest present but no / near-zero source (fresh scaffold) → **brownfield** (STACK is derivable; scout finds little but real — no fiction risk).
   - ambiguous (a few stray files) → **AskUserQuestion**: "Brownfield (scout & document existing code) or Greenfield (seed an empty docs spine)?"
   - **per-module scope:** run this check per module root — seed only the empty modules, scout the rest.
   - **greenfield → go to Stage 1G (skip Stages 1–4).** brownfield → continue Stages 1–5 normally.
3. **Scale: ALWAYS ask the user** (AskUserQuestion: project-level vs per-module) unless `--scope` was passed. Surface monorepo markers found (`pnpm-workspace.yaml`, `packages/*`, `apps/*`, `go.work`, lerna) as hints in the question.

## Stage 1G — Greenfield Seed (replaces Stages 1–4 when Stage 0 found greenfield)

No code to scout → do NOT derive content. Seed ONLY the format-correct spine; **never invent features, architecture, or sources (no fiction)**. Code-derived docs (SOURCE-MAP, SYS-SPEC, TEST-*, CODE-STANDARDS, INVARIANTS, DATA/API/UI-MAP) are **skipped** — `/morkit:docs update` grows them later (its "new components" step) as code appears. This is the one sanctioned deviation from "core-6 always": seed a reduced spine, not empty folders.

Seed set (exactly these unless the user opts in below):
- `docs/00-overview/SCOPE.md` — from template. Capture the project's *intended* boundary: ask the user 1–2 short questions for In/Out of Scope, or leave the template hints if they decline. Front-matter `status: draft`.
- `docs/00-overview/DOCUMENT-MAP.md` — from template. List ONLY the seeded folders; add a note "Other folders are created by `/morkit:docs update` as the code grows." Keep Read Paths minimal ("Understand the project" → SCOPE). This is the file `CLAUDE.md` points at, so it must exist.
- `docs/10-requirements/FEATURE-LIST.md` — from template, EMPTY catalog: keep Legend + Actors + the FR/NFR table **headers**, delete the placeholder example rows, ready for `FR-001`/`NFR-001`. Omit `source_files` front-matter (no code yet).
- root `CLAUDE.md` pointer — per `references/agent-instructions.md`. Orientation line from SCOPE; **drop the AI-CODING-GUIDE and INVARIANTS pointer lines** (not seeded) — keep only the DOCUMENT-MAP pointer. Approve gate per file. Also write `AGENTS.md` when Codex detected / `--agents`.

Opt-in intent docs (ONE gate; default NO; `--yes` → NO):
- AskUserQuestion: "Also seed intended STACK + ARCHITECTURE (forward-looking — may drift from code)?" If yes:
  - `docs/00-overview/STACK.md` — chosen/intended stack, front-matter `status: draft`; **omit `source_files`** (the template hardcodes manifest paths — no manifest exists yet, so drop them or `update` will flag STACK as perpetually stale).
  - `docs/20-design/00-core/ARCHITECTURE.md` — intended architecture (arc42-lite), front-matter `status: planned`.
  - These are intent, not code-derived — the `status` marks them so `update` reconciles against real code later.

Then run **Stage 4b** (agent-instructions / `CLAUDE.md` pointer) and a **trimmed Stage 5** (validate: links resolve, front-matter present; report what was seeded + "run `/morkit:docs update` once code exists"). Skip Stage 6 (no legacy on greenfield).

## Stage 1 — Scout (read-only, parallel) — brownfield path

> Stages 1–6 below are the **brownfield** pipeline. If Stage 0 found greenfield, you ran Stage 1G instead and are done after its trimmed Stage 5.

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
