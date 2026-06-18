---
name: build-project-model
description: "Bridge skill — author a valid ProjectModel JSON (per normalized_schema) from greenfield inputs (parsed customer docs + brainstorm report + user-story list + risk register + clarification answers), then validate it so /morkit:init can render docs/srs.md and friends with no hand-authored JSON. The missing brainstorm→init link for the greenfield pipeline."
category: documentation
keywords: [project-model, bridge, greenfield, normalized-schema, srs, provenance, doc-ingest, brse]
argument-hint: "--workspace morkit/output/greenfield/<proj> [--language JP|EN|VN]"
metadata:
  author: morkit-greenfield
  version: "1.0.0"
---

# Build ProjectModel (Bridge) 🌉

The **keystone** of `/morkit:greenfield`. Turns the BA/BrSE artifacts into a
single `project-model.json` that the existing `docs-hero` `init` pipeline
consumes. After this skill, `customer docs → project-model.json → init → docs/srs.md`
works end-to-end.

> Conventions (workspace layout, provenance, classification) are defined once in
> [`../greenfield-orchestrator/references/greenfield-conventions.md`](../greenfield-orchestrator/references/greenfield-conventions.md).
> Schema authoring rules: [`references/schema-cheatsheet.md`](references/schema-cheatsheet.md).
> Do not restate them — follow them.

## Inputs (read what exists, skip what doesn't)

All under the run workspace `morkit/output/greenfield/<proj>/`:

| File | Produced by | Use |
|---|---|---|
| `inputs/*` | G0 intake | raw customer docs (parsed below) |
| `brainstorm-report.md` | G1 `/morkit:brainstorming` | scope, goals, actors |
| `user-story-list.md` | G2 `generate-user-stories` | FR / UseCase candidates |
| `gap-analysis.md` | G3 `gap-risk-analysis` | gaps → `open_questions` |
| `risk-register.md` | G3 `gap-risk-analysis` | rows → `constraints_risks.risks` |
| `clarification-log.md` | G4 `clarification-loop` | answers → fill `<TBD>`, FR detail |

## Step 1 — Doc-ingest (reuse `parse_inputs.py`, no new parser)

```bash
PY="${HOME}/.claude/plugins/data/docs-hero/.venv/bin/python3"
ORCH="${CLAUDE_PLUGIN_ROOT:?}/skills/docs-hero-orchestrator/scripts"
WS="morkit/output/greenfield/<proj>"

"$PY" "$ORCH/parse_inputs.py" --inputs-dir "$WS/inputs" \
  --language "$LANG" --project-name "<proj>" --output "$WS/raw-bundle.json"
```

`parse_inputs.py` does **structural** extraction only (text/tables) and never
crashes on empty inputs (returns `warnings`). Then **you** (LLM) read
`raw-bundle.json` and, per source, write a short fact list — never dump full
text. Emit `source-manifest.json` per the
[schema](../greenfield-orchestrator/schemas/source-manifest.schema.json): each
source → `classified_as` (entity types, see conventions §5) → `facts`.
For large docs, summarize each source in a subagent so context stays small.

## Step 2 — Author `project-model.json`

Using `raw-bundle.json` + `source-manifest.json` + the markdown artifacts above,
author `$WS/project-model.json` following the
[cheatsheet](references/schema-cheatsheet.md). Non-negotiable rules:

- **Only `meta.project_name` is required.** Start minimal, add only justified entities.
- **No fiction.** Every seeded entity carries `source` (SourceRef) and/or
  `external_sources: [path]`, and `doc_status: "Draft"`. A fact with no source
  becomes an `open_questions` entry or a `<TBD: reason>` string — never invented.
- **Skip code-derived** entities (screen items, db tables/columns, api endpoints,
  naming/lint, modules) — greenfield has no code; `init` backfills later.
- **Canonical/drift** (conventions §6): external doc is primary for WHAT/WHY; on a
  conflict between two docs, record an `open_questions`/`risk` row rather than guess.
- Map user-stories to entities by format: **brse → `functional_requirements`**,
  **agile → `business_flow.use_cases`** (+ derived FR). Keep ids stable from G2.

## Step 3 — Validate (hard gate, loop until clean)

```bash
VAL="${CLAUDE_PLUGIN_ROOT:?}/skills/build-project-model/scripts/validate_project_model.py"
"$PY" "$VAL" --project-model "$WS/project-model.json"
```

- Exit 0 → valid; proceed to G6 (`init`).
- Exit 1 → the script prints exact `field.path: message` lines. **Re-author only
  the offending fields** and re-run. Cap at ~5 iterations; if still failing,
  surface the remaining errors to the user (don't loop forever).
- Exit 2 → file missing / malformed JSON → fix the JSON and re-run.

Common fixes: `id` regex (`FR-001`, `UC-001`, `ENT-001`, `DATA-001`, `INT-001`,
`CONS-001`, `ASM-001`); `priority`/`status` enum typos; provenance `draft` placed
in `doc_status`, not `status`.

## Step 4 — Hand off to `init`

The validated file is consumed unchanged by the orchestrator:

```bash
"$PY" "$ORCH/dispatch_coordinator.py" init \
  --project-model "$WS/project-model.json" \
  --language "$LANG" --outputs srs --docs-dir "$PWD/docs"
```

(The `greenfield-orchestrator` G6/G7 stages call this for you with the resolved
`--outputs`.)

## Tests

`tests/test_validate_project_model.py` — valid minimal model, missing-required
error path, provenance extras preserved, bad id rejected, the `status`-vs-`doc_status`
pitfall. `tests/fixtures/seeded-greenfield.json` is a known-good bridge output.
