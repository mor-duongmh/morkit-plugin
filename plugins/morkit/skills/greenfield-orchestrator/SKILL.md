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
CL="${CLAUDE_PLUGIN_ROOT:?}/skills/greenfield-orchestrator/scripts/checklist_loader.py"
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
| **G7** DesignDocs | `init --outputs arch,standards,summary,db` (+ `api`,`guidelines` if selected) → **per-doc Review Gate (warn-only soft gate)** → promote → QA via `docs-reviewer` | review-loop (warn-only) | mark `done` |

Per stage: run the action → on success `state_manager set-stage <Gx> done <artifact>`
→ for gated stages run the checklist-driven gate (below) → `advance` (which hard-blocks
until the gate clears).

## The 4 gates (focused — value over count)

Each gate is **checklist-driven and hard-blocked**. The per-gate must-pass
subset lives in the canonical checklist
([`references/gate-checklists/`](references/gate-checklists/), front-matter
`required`). `advance` **refuses to leave a gated stage** until its gate is
`proceed` with every `required` item confirmed (G4 `force-close` may leave with
a note) — so a gate can't be rubber-stamped past.

**Gate procedure (every gated stage `Gx`):**
1. Load the must-pass subset: `"$PY" "$CL" show --gate Gx` → read `required` + item titles.
2. Render those items (title + `Tiêu chí:`) in visible text, then `AskUserQuestion`:
   one multiSelect "Mục bắt buộc nào đã ĐẠT?" (options = the required items) + the decision question.
3. Persist with the confirmed ids: `set-gate --decision <enum> --checklist-required <all> --checklist-confirmed <met>`.
4. `advance`. If required ids are missing (or decision isn't a pass) it raises — report
   "gate chưa đủ điều kiện, ở lại Gx" and re-run the stage; never fabricate a pass.

Decision enums per gate (label → enum, from each checklist's `decisions`):

- **G2 — story confirm (foundational doc):** `Proceed` (accept list, `proceed`) / `Another round`
  (re-run G2 scoped Q&A, `adjust`) / `Abort`. The function list is what every downstream stage
  is built on, so it gets its own gate. `generate-user-stories` surfaces a review-aid
  (low-confidence stories, zero-coverage areas) for the BrSE to react to, not a blank "approve?".
- **G3 — BA review:** `Proceed` / `Adjust` (revise gap/risk rows, re-run G3) / `Abort`.
- **G4 — clarification:** `Close loop` (`proceed`) / `Another round` (`adjust`) / `Force-close`
  (`force-close` — leaves the gate with a logged reason despite open questions).
- **G6 — stakeholder SRS review:** `Proceed` / `Revise` (`adjust`) / `Abort`.

```bash
# G2 — confirm the must-pass subset surfaced from the checklist, then advance:
REQ=$("$PY" "$CL" show --gate G2 | "$PY" -c 'import json,sys;print(",".join(json.load(sys.stdin)["required"]))')
"$PY" "$SM" set-gate --state "$WS/state.json" --stage G2 --decision proceed \
  --note "BrSE confirmed function list" --checklist-required "$REQ" --checklist-confirmed "$REQ"
"$PY" "$SM" advance  --state "$WS/state.json"   # raises if any required id is unconfirmed
```

## G6 / G7 — delegate to the render backend (no new render code)

G6/G7 call the render backend (`dispatch_coordinator.py init`) directly — the
same engine `/morkit:init`'s brownfield branch uses. They do NOT call the
interactive `/morkit:init` front door, so the project-type question is never
re-asked. The validated `project-model.json` is consumed unchanged:

```bash
ORCH="${CLAUDE_PLUGIN_ROOT:?}/skills/docs-hero-orchestrator/scripts"
STAGING="$PWD/.tmp/staged"; mkdir -p "$STAGING"
# G6: SRS (no review gate — G6's stakeholder gate already covers requirements)
"$PY" "$ORCH/dispatch_coordinator.py" init \
  --project-model "$WS/project-model.json" --language "$LANG" \
  --outputs srs --docs-dir "$PWD/docs"
# G7: design docs. The 5 code-derived docs render to STAGING and pass through the
#     per-doc Review Gate before promotion; guidelines renders direct + light confirm.
"$PY" "$ORCH/dispatch_coordinator.py" init \
  --project-model "$WS/project-model.json" --language "$LANG" \
  --outputs arch,standards,summary,db --docs-dir "$STAGING"
# (+ api to STAGING, + guidelines direct to docs/, when the user selected them)
```

**G7 Review Gate (per-doc loop):** for each staged design doc, run the loop
defined once in `docs-hero-orchestrator/SKILL.md` → "Review Gate (per-doc loop)"
(`review_gate.py` snapshot → surface → AskUserQuestion `[Approve | Sửa tiếp]` →
promote; `--meta "$PWD/docs/.docs-hero-meta.json"`). `design-guidelines` gets the
light `[OK | Sửa | Bỏ]` confirm. **Do NOT copy the loop here — reference it**, so
brownfield and greenfield stay in sync.

> **Convention — G7 is a warn-only soft gate (divergence, by design).** Unlike
> G2/G3/G4/G6, G7 is **NOT** wired into the `advance()`-guard / `set-gate`
> checklist engine. Skipping a doc's review never hard-blocks: the doc is just
> not promoted and is reported in the warn-only summary. This is the user-chosen
> trade-off (per the plan's Open Question #1) so doc review can't stall a
> greenfield run. **Do not "fix" this into a hard block** without re-confirming
> with the user. *(v2 hook: a review-checklist per doc-type could reuse
> `references/gate-checklists/` to upgrade this to a real gate.)*

## QA gate (after G7 promote — reuses /morkit:init's gate)

Once the reviewed docs are **promoted** into `docs/`, spawn the `docs-reviewer`
agent (Task tool, `subagent_type: docs-reviewer`) to validate the full `docs/`
set (cross-references + BrSE quality + Mermaid). This is the same QA agent
`/morkit:init` runs at its final step — greenfield reuses it so
greenfield-generated docs get an identical gate. Surface the report path to the
user (including any docs left un-promoted by the warn-only review gate), then
`state_manager set-stage G7 done "$PWD/docs"`.

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
