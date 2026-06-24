---
name: greenfield-orchestrator
description: "Stateful guide for /morkit:greenfield — walks the BA/BrSE documentation pipeline G0→G7, runs the owning skill per stage, enforces the 4 human gates, and resumes from state.json. Thin glue: holds NO business logic — every stage delegates to an existing skill (brainstorming, generate-user-stories, gap-risk-analysis, clarification-loop, build-project-model) or to /morkit:init for the final SRS + design docs. Turns customer docs into a validated ProjectModel and a full docs/ set with no hand-authored JSON."
category: documentation
keywords: [greenfield, orchestrator, brse, ba, srs, pipeline, state-machine, resume, gates, japan-ito]
argument-hint: "<proj> [--format brse|agile] [--lang JP|EN|VN] [--resume]"
metadata:
  author: morkit-greenfield
  version: "1.0.0"
---

# Greenfield Orchestrator

The thin router for `/morkit:greenfield`. Drives the pipeline, enforces gates,
and resumes from `state.json`. **No business logic lives here** — each stage
calls the skill that owns it. If you find yourself writing requirement/risk logic
in this file, it belongs in the stage skill instead.

> Conventions (workspace, stages, state schema, classification, provenance) are
> the single source of truth in
> [`references/greenfield-conventions.md`](references/greenfield-conventions.md).
> State helper: [`scripts/state_manager.py`](scripts/state_manager.py)
> (reuses [`scripts/validate_state.py`](scripts/validate_state.py)).

## Pre-flight

```bash
PY="${HOME}/.claude/plugins/data/docs-hero/.venv/bin/python3"
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /morkit:setup first." >&2; exit 1; }
SM="${CLAUDE_PLUGIN_ROOT:?}/skills/greenfield-orchestrator/scripts/state_manager.py"
WS="morkit/output/greenfield/<proj-slug>"
```

## Resume model

Every invocation reads `state.json` and re-enters at `state.stage`. With
`--resume`, do not re-run completed stages — pick up at the current one. State
writes are atomic (`state_manager.py`), so a kill mid-pipeline never corrupts it.

```bash
# Fresh run:
"$PY" "$SM" init --state "$WS/state.json" --project "<proj>" --format brse --lang JP
# Resume:  read current stage, continue.
"$PY" "$SM" show --state "$WS/state.json"
```

## Stage routing table

| Stage | Action (delegate to) | Gate | On pass |
|---|---|---|---|
| **G0** Intake | collect `inputs/`, `state_manager init` | — | `advance` → G1 |
| **G1** Brainstorm | `/morkit:brainstorming` (+ doc-ingest from `build-project-model` Step 1) → `brainstorm-report.md` | — | `advance` → G2 |
| **G2** UserStory | `generate-user-stories --format <fmt>` → `user-story-list.md` (+ scoped Q&A) | **BrSE: confirm list** | gate `proceed` → `advance` → G3 |
| **G3** Analysis | `gap-risk-analysis` → `gap-analysis.md`, `risk-register.md` | **BA: Proceed/Adjust** | gate `proceed` → `advance` → G4 |
| **G4** Clarify | `clarification-loop` → `clarification-log.md` | **enough-answered / force-close** | gate → `advance` → G5 |
| **G5** Bridge | `build-project-model` → `project-model.json` (validated) | — | `advance` → G6 |
| **G6** SRS+Visual | `init --outputs srs` + visualize | **stakeholder review** | gate `proceed` → `advance` → G7 |
| **G7** DesignDocs | `init --outputs arch,standards,summary,db` (+ `api`,`guidelines` if selected) → QA via `docs-reviewer` | — | mark `done` |

Per stage: run the action → on success `state_manager set-stage <Gx> done <artifact>`
→ for gated stages evaluate the gate → `advance`.

## The 4 gates (focused — value over count)

Each uses `AskUserQuestion` and persists via `state_manager set-gate`:

- **G2 — story confirm (foundational doc):** `Proceed` (accept list) / `Another round`
  (re-run G2 scoped Q&A — decision `adjust`) / `Abort`. The function list is what every
  downstream stage is built on, so it gets its own gate. This *cleans* G3/G4 (they now run
  on a human-validated list) — net friction stays ~flat despite the extra gate. The gate is
  cheap because `generate-user-stories` surfaces a review-aid (low-confidence stories,
  zero-coverage areas) for the BrSE to react to, not a blank "approve?".
- **G3 — BA review:** `Proceed` / `Adjust` (revise gap/risk rows, re-run G3) / `Abort`.
- **G4 — clarification:** `Close loop` (enough answered) / `Another round` / `Force-close`.
- **G6 — stakeholder SRS review:** `Proceed` / `Revise` / `Abort`.

```bash
"$PY" "$SM" set-gate --state "$WS/state.json" --stage G2 --decision proceed --note "BrSE confirmed function list"
"$PY" "$SM" set-gate --state "$WS/state.json" --stage G3 --decision proceed --note "BA approved"
"$PY" "$SM" advance  --state "$WS/state.json"
```

## G6 / G7 — delegate to the render backend (no new render code)

G6/G7 call the render backend (`dispatch_coordinator.py init`) directly — the
same engine `/morkit:init`'s brownfield branch uses. They do NOT call the
interactive `/morkit:init` front door, so the project-type question is never
re-asked. The validated `project-model.json` is consumed unchanged:

```bash
ORCH="${CLAUDE_PLUGIN_ROOT:?}/skills/docs-hero-orchestrator/scripts"
# G6: SRS
"$PY" "$ORCH/dispatch_coordinator.py" init \
  --project-model "$WS/project-model.json" --language "$LANG" \
  --outputs srs --docs-dir "$PWD/docs"
# G7: design docs (outputs resolved from the user's selection)
"$PY" "$ORCH/dispatch_coordinator.py" init \
  --project-model "$WS/project-model.json" --language "$LANG" \
  --outputs arch,standards,summary,db --docs-dir "$PWD/docs"
```

## QA gate (after G7 render — reuses /morkit:init's gate)

Once all docs are rendered, spawn the `docs-reviewer` agent (Task tool,
`subagent_type: docs-reviewer`) to validate the full `docs/` set
(cross-references + BrSE quality + Mermaid). This is the same QA agent
`/morkit:init` runs at its final step — greenfield reuses it so
greenfield-generated docs get an identical gate. Surface the report path to the
user, then `state_manager set-stage G7 done "$PWD/docs"`.

## Visualize (G6, stakeholder-facing)

`srs.html` is produced **deterministically by the render backend** — the same
`dispatch_coordinator.py init` call at G6 emits `docs/srs.html` alongside
`docs/srs.md` (visualize defaults on whenever `srs` is built). It applies the
fixed **Mor theme** (brand tokens + sidebar navigation + scrollspy) via
`render_html.py`, so output is consistent every run and on-brand — no ad-hoc
preview/show-off rendering. The HTML is print-friendly (sidebar/topbar hidden
on print, ideal for JP stakeholders). Presentation only — it never edits the
SRS content.

## Invariants

- **Routing/gating only.** Business logic stays in the stage skills; they remain
  independently usable standalone.
- **Resume-safe.** All progress is in `state.json` (atomic writes) + the per-stage
  `.md` artifacts. Kill any time; re-invoke with `--resume`.
- **No fiction.** Inherited from every stage skill (see conventions §6).

## Tests

`tests/test_state_manager.py` — init validity, advance transitions, gate guards,
atomic save/load round-trip, and an explicit **kill + resume** restoration test.
