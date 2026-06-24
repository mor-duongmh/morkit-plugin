---
name: generate-user-stories
description: "Turn the greenfield brainstorm report (+ source manifest) into a standalone user-story-list.md — the S2 deliverable that otherwise only exists buried in SRS §3. Confidence-gated co-creation: self-scores each story (source/completeness/interpretation) + a coverage map, runs scoped human Q&A only where unsure (reusing clarification-loop), then a confirm gate — depth adapts to G1 quality. Two output formats via --format brse|agile: brse = function-list rows aligned 1:1 with SRS §3.1 (JP ITO clients); agile = As-a/I-want/So-that with acceptance criteria. Both map cleanly to ProjectModel FunctionalRequirement / UseCase for the bridge."
category: documentation
keywords: [user-stories, function-list, brse, agile, srs, greenfield, requirements]
argument-hint: "--workspace morkit/output/greenfield/<proj> --format brse|agile [--lang JP|EN|VN]"
metadata:
  author: morkit-greenfield
  version: "1.0.0"
---

# Generate User Stories

Stage **G2** of `/morkit:greenfield`. Reads what was learned at G1 and emits the
user-story list the rest of the pipeline (G3 gap-risk, G5 bridge) attaches to.

> Conventions: [`../greenfield-orchestrator/references/greenfield-conventions.md`](../greenfield-orchestrator/references/greenfield-conventions.md).
> Confidence rubric (scoring + question templates): [`references/confidence-rubric.md`](references/confidence-rubric.md).
> Templates: [`templates/user-story-brse-template.md`](templates/user-story-brse-template.md),
> [`templates/user-story-agile-template.md`](templates/user-story-agile-template.md).

## Shared item shape (one model, two renderers — DRY)

Internally every story is the same item; `--format` only picks the renderer:

```
{ id, title, actor, goal, benefit, acceptance, priority, source_ref,
  source_strength, field_completeness, interpretation }   # last 3 = G2 self-score (working metadata)
```

The first 8 fields render into `user-story-list.md`; the last 3 are confidence
metadata (see rubric) that drive B2–B3 and the gate review-aid — not rendered.

- `brse` renders the function-list table (columns mirror **SRS §3.1**).
- `agile` renders the `As-a / I-want / So-that` table with acceptance criteria.

Because both are views of one item shape, the bridge maps either to ProjectModel
without loss — formats can't drift.

## Inputs

From the run workspace `morkit/output/greenfield/<proj>/`:
- `brainstorm-report.md` (G1) — the candidate stories' source.
- `source-manifest.json` — provenance refs to cite per story.

## Procedure — confidence-gated co-creation

G2 is **gated** (the function list is the foundational doc everything downstream is
built on). Rather than auto-emit and hope, self-score confidence and spend human
attention only where it's unsure. Rubric + question templates:
[`references/confidence-rubric.md`](references/confidence-rubric.md).

**B1 — Draft with source discipline (kills *fiction*).**
Extract candidate stories from `brainstorm-report.md` (+ manifest facts). Assign
**deterministic, stable ids** (`FUNC-001…` brse / `US-001…` agile) in document order;
re-runs reuse existing ids (same pattern as `docs-hero-orchestrator/scripts/lib/id_allocator.py`).
Every row MUST carry a `Source` and is `doc_status: Draft`. **Assert 0 stories without
`source_ref`** — a sourceless candidate becomes a B3 question or a G3 gap, never a row.

**B2 — Self-score + coverage map (detects *shallow / missing / wrong*).**
Per story set `source_strength`, `field_completeness`, `interpretation` per the rubric.
Build the coverage map of function-areas (from actors/scope/modules in G1) and mark
zero-story areas. Flag any story with a low/weak/inferred signal.

**B3 — Scoped interactive Q&A (the co-creation; reuse `clarification-loop`).**
For flagged items only, write grouped questions into `g2-clarification-log.md` using the
**same table shape** as `clarification-loop`'s `clarification-log-template.md` (do not
invent a second format). High-confidence stories are listed for awareness, not
interrogated (respect the BrSE's time). Ingest answers → update the affected stories →
re-score. This loop is **interpretation/coverage-driven and runs *before* G3** —
distinct from G4 (gap-driven, after G3); the separate log file keeps them from colliding.

**B4 — Render + review-aid (feeds the G2 gate).**
Render the selected `--format` into `user-story-list.md`, then emit the review-aid
summary (rubric §"Review-aid summary"). The orchestrator runs the **G2 confirm gate**
(`Proceed` / `Another round` = re-run B2–B3 / `Abort`) and persists it via
`state_manager set-gate --stage G2`. This skill produces the artifact + review-aid; it
does **not** run the gate UI itself.

## Bridge mapping (consumed at G5)

| Format | ProjectModel target |
|---|---|
| `brse` row | `FunctionalRequirement` (`id` from Related FR / derived from FUNC-id; `name`=Function; `role`=Actor; `priority`; `source`; `doc_status: Draft`) |
| `agile` row | `UseCase` (`id` UC-00x; `name`=goal; `actor`=role; `summary`=benefit; `main_success_scenario`=acceptance) **+ a derived FR** when the story implies a concrete function |

Verify every required FR/UseCase field is populated before handing to the bridge
(see [`../build-project-model/references/schema-cheatsheet.md`](../build-project-model/references/schema-cheatsheet.md)).

## Format choice

`--format` is inherited from `state.json` (set at G0; default `brse` for JP ITO).
The orchestrator passes it through; this skill never decides format on its own.
