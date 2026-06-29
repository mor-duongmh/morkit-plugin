# ProjectModel Authoring Cheatsheet

> LLM-facing summary of `docs-hero-orchestrator/scripts/lib/normalized_schema.py`
> — the **single source of truth**. If this drifts, the schema wins. The bridge
> authors JSON; `validate_project_model.py` confirms it loads as `ProjectModel`.
> `extra="allow"` is on every model → unknown keys are **kept**, not rejected.

## Top-level shape

```json
{
  "meta": { "project_name": "..." },        // ONLY required block
  "overview": { ... },
  "business_flow": { "use_cases": [ ... ] },
  "functional_requirements": [ ... ],
  "non_functional_requirements": [ ... ],
  "entities": [ ... ], "data_items": [ ... ],
  "external_interfaces": [ ... ],
  "open_questions": [ ... ],
  "constraints_risks": { "risks": [ ... ], "constraint_records": [ ... ], "assumption_records": [ ... ] },
  "glossary": [ ... ]
}
```

A model with **only** `{"meta": {"project_name": "X"}}` is valid (mirrors the
empty-inputs path). Everything else defaults to empty lists.

## Greenfield seeding rules (no fiction)

1. **Seed only WHAT/WHY** entities the customer docs justify: `functional_requirements`,
   `overview.in_scope/out_of_scope`, `business_flow.use_cases`, `entities`,
   `data_items`, `external_interfaces`, `open_questions`, `glossary`, risks.
2. **Skip code-derived** entities (screens detail, db tables/columns, api endpoints,
   naming/lint, modules, tech_stack) — greenfield has no code; `init` backfills later.
3. **Every seeded entity traces to a source**: set `source` (SourceRef) and/or
   `external_sources`. No source → it's an `open_questions` item or a `<TBD: ...>`
   string, never an invented value.
4. **Draft state** → `doc_status: "Draft"`. **Never** put `draft` in `status`
   (that field only accepts `active`/`deprecated`).

## Entity reference (required ⬛ vs optional ⬜)

### ProjectMeta (`meta`)
⬛ `project_name`. ⬜ `version` (def "1.0"), `language` (`JP|EN|VN`, def EN),
`date`, `customer`, `brse_name`, `doc_status` (`Draft|In Review|Reviewed|Approved|Deferred`).

### Overview (`overview`)
⬜ `purpose`, `background`, `in_scope: [str]`, `out_of_scope: [str]`,
`future_scope: [str]`, `stakeholders`, `references`.

### FunctionalRequirement (`functional_requirements[]`)
⬛ `id` (regex `^FR-[A-Z0-9_-]+$`, e.g. `FR-001`), `name`.
⬜ `description`, `summary`, `priority` (`High|Mid|Low|Must|Should|Could|Won't`, def Mid),
`acceptance_criteria: [str]`, `main_flow: [str]`, `related_uc: [UC ids]`,
`business_rules: [BR ids]`, `doc_status`, `source`, `impl_status` (def `NotStarted`).

### UseCase (`business_flow.use_cases[]`)
⬛ `id` (e.g. `UC-001`), `name`, `actor`.
⬜ `summary`, `goal`, `trigger`, `main_success_scenario: [str]`, `precondition`,
`postcondition`, `related_fr: [FR ids]`, `priority`.

### EntityDef (`entities[]`)
⬛ `id` (`^ENT-[A-Z0-9_-]+$`), `entity` (table/object name).
⬜ `business_meaning`, `owner`, `notes`.

### DataItem (`data_items[]`)
⬛ `id` (`^DATA-[A-Z0-9_-]+$`), `entity`, `field_name`, `field_type`.
⬜ `business_meaning`, `nullable` (def false), `pii`, `validation`, `example`.

### ExternalInterface (`external_interfaces[]`)
⬛ `id` (`^INT-[A-Z0-9_-]+$`), `name`.
⬜ `type` (`REST|GraphQL|File|DB|Message|Webhook|Other`, def REST), `direction`,
`summary`, `endpoint_path`, `method`, `related_fr`.

### OpenQuestion (`open_questions[]`)
⬛ `id` (e.g. `Q-001`).
⬜ `question`, `answer`, `category` (Scope/FR/NFR/Data/UI/Interface/Ops), `topic`,
`owner`, `due_date`, `q_status` (`Open|Answered|Closed`, def Open), `related_id`.

### Risk (`constraints_risks.risks[]`)
⬛ `description`.
⬜ `id` (e.g. `RISK-001`), `impact` (`High|Mid|Low`, def Mid),
`likelihood` (`High|Mid|Low`, def Mid), `mitigation`, `owner`,
`risk_status` (`Open|Monitoring|Closed`, def Open).
*Phase-3 extras (`score`, `category`, `probability`) ride on `extra="allow"`.*

### Constraint (`constraints_risks.constraint_records[]`)
⬛ `id` (e.g. `CONS-001`). ⬜ `category`, `constraint`, `impact`, `owner`.

### Assumption (`constraints_risks.assumption_records[]`)
⬛ `id` (e.g. `ASM-001`). ⬜ `assumption`, `impact_if_false`, `validation_method`.

### GlossaryEntry (`glossary[]`)
⬜ `term_jp`, `term_en`, `term_vn`, `definition`. (No id.)

## SourceRef shape (provenance)

```json
"source": { "origin": "pdf", "file_path": "inputs/prd.pdf", "line_range": [10, 24] }
```
`origin ∈ {openspec, pdf, excel, docx, codebase, plan, manual, codebase-sync}`.
For multi-doc provenance add the extra key `"external_sources": ["inputs/a.pdf", "inputs/b.xlsx"]`.

## ImplStatus enum (FR-level, greenfield default `NotStarted`)
`NotStarted | InProgress | Done | Verified | Blocked`. Leave at `NotStarted` for
greenfield (no code). `init` auto-detects and upgrades from openspec/code/tests.
