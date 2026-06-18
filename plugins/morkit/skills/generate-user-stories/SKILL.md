---
name: generate-user-stories
description: "Turn the greenfield brainstorm report (+ source manifest) into a standalone user-story-list.md — the S2 deliverable that otherwise only exists buried in SRS §3. Two output formats via --format brse|agile: brse = function-list rows aligned 1:1 with SRS §3.1 (JP ITO clients); agile = As-a/I-want/So-that with acceptance criteria. Both map cleanly to ProjectModel FunctionalRequirement / UseCase for the bridge."
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
> Templates: [`templates/user-story-brse-template.md`](templates/user-story-brse-template.md),
> [`templates/user-story-agile-template.md`](templates/user-story-agile-template.md).

## Shared item shape (one model, two renderers — DRY)

Internally every story is the same item; `--format` only picks the renderer:

```
{ id, title, actor, goal, benefit, acceptance, priority, source_ref }
```

- `brse` renders the function-list table (columns mirror **SRS §3.1**).
- `agile` renders the `As-a / I-want / So-that` table with acceptance criteria.

Because both are views of one item shape, the bridge maps either to ProjectModel
without loss — formats can't drift.

## Inputs

From the run workspace `morkit/output/greenfield/<proj>/`:
- `brainstorm-report.md` (G1) — the candidate stories' source.
- `source-manifest.json` — provenance refs to cite per story.

## Procedure

1. Extract candidate stories from `brainstorm-report.md` (+ manifest facts).
2. Assign **deterministic, stable ids**: `FUNC-001`, `FUNC-002`, … (brse) or
   `US-001`, `US-002`, … (agile), in document order. Re-runs reuse existing ids
   (allocate only new ones — same pattern as `docs-hero-orchestrator/scripts/lib/id_allocator.py`).
3. Render the selected `--format` into `user-story-list.md`.
4. Every row carries a `Source` (provenance) and is `status: Draft` (greenfield —
   no fiction; a story with no source is instead a gap for G3, not an invented row).

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
