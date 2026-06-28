# Greenfield Pipeline — Conventions (Single Source of Truth)

> Every `/morkit:greenfield` stage skill **links** to this file. Do **not** restate
> these rules elsewhere — reference them (DRY). Built on the **docs-hero**
> architecture (`ProjectModel JSON` per `normalized_schema.py`).

## 1. Workspace layout

One directory per greenfield project run, under the user's project (`$PWD`):

```
morkit/output/greenfield/<proj-slug>/
  inputs/                 # G0  customer docs (pdf/xlsx/docx/md/openspec)
  state.json              #     orchestrator stage tracker (see §3)
  source-manifest.json    #     doc-ingest: source → targets → facts (see §4)
  brainstorm-report.md    # G1  /morkit:brainstorming output
  user-story-list.md      # G2  generate-user-stories output
  gap-analysis.md         # G3  gap-risk-analysis (canonical)
  risk-register.md        # G3  gap-risk-analysis (canonical)
  clarification-log.md    # G4  clarification-loop (resume-able state lives here)
  project-model.json      # G5  build-project-model bridge → consumed by init
```

Final docs land in the **project's** `docs/` (via `/morkit:init`), NOT in the
workspace. The workspace holds only intermediate/BA artifacts.

## 2. Stages G0–G7

| Stage | Name | Skill | Gate | Artifact |
|---|---|---|---|---|
| G0 | Intake | orchestrator | — | `inputs/`, `state.json` |
| G1 | Brainstorm | `brainstorming` (+ doc-ingest) | — | `brainstorm-report.md` |
| G2 | UserStory | `generate-user-stories` | **BrSE: confirm list** | `user-story-list.md` (+ `g2-clarification-log.md`) |
| G3 | Analysis | `gap-risk-analysis` | **BA: Proceed/Adjust** | `gap-analysis.md`, `risk-register.md` |
| G4 | Clarify | `clarification-loop` | **enough-answered/force-close** | `clarification-log.md` |
| G5 | Bridge | `build-project-model` | — | `project-model.json` |
| G6 | SRS+Visual | `init --outputs srs` + visualize | **BrSE/BA review** | `docs/srs.md`, `srs.html` |
| G7 | DesignDocs | `init --outputs arch,standards,summary,db` | _review-loop (warn-only soft gate)_ | `docs/*.md` |

The G7 gate is **warn-only**: it is the per-doc Review Gate (staged render →
`[Approve | Sửa tiếp]` → promote), NOT the `set-gate`/`advance()` checklist engine
that hard-blocks G2/G3/G4/G6. Skipping review never blocks the run — see
`docs-hero-orchestrator/SKILL.md` → "Review Gate (per-doc loop)".

Stage order is fixed; gates persist their decision into `state.json` (§3). Stages
align with `init`'s existing `docs-plan.md` §0–§5 gap/risk flow (reference, don't fork).

## 3. `state.json`

Tracks the current stage and per-stage status so a run resumes from `state.json`
alone. Schema: [`schemas/state.schema.json`](../schemas/state.schema.json).

```json
{
  "project": "acme-portal",
  "stage": "G3",
  "format": "brse",
  "lang": "JP",
  "created": "2026-06-18T00:00:00Z",
  "updated": "2026-06-18T00:00:00Z",
  "stages": {
    "G0": { "status": "done", "artifact": "inputs/", "updated": "2026-06-18T00:00:00Z" },
    "G1": { "status": "done", "artifact": "brainstorm-report.md", "updated": "2026-06-18T00:00:00Z" },
    "G2": { "status": "done", "artifact": "user-story-list.md", "updated": "2026-06-18T00:00:00Z",
            "gate": { "decision": "proceed", "note": "BrSE confirmed list" } },
    "G3": { "status": "in_progress", "artifact": null, "updated": null,
            "gate": { "decision": "pending", "note": "" } }
  }
}
```

- `stage` — current stage id (enum `G0..G7`).
- `format` — `brse` | `agile` (user-story render format; default `brse`).
- `lang` — `JP` | `EN` | `VN` (matches `normalized_schema.Language`).
- `stages.<Gx>.status` — `pending` | `in_progress` | `done` | `blocked`.
- `stages.<Gx>.gate` (gated stages **G2, G3, G4, G6**) — `{ decision: pending|proceed|adjust|force-close, note, checklist? }`.
  G2 uses `proceed` (confirm function list) / `adjust` (run another G2 scoped-Q&A round); `Abort` halts (not persisted), same as G3/G6.
  Optional `checklist: { required:[id], confirmed:[id] }` records the must-pass subset
  from the gate checklist ([`gate-checklists/`](gate-checklists/)); `advance` **hard-blocks**
  until `decision==proceed` and `required ⊆ confirmed` (G4 `force-close` leaves with a note).

Validated by [`scripts/validate_state.py`](../scripts/validate_state.py) on every load.

## 4. `source-manifest.json`

Doc-ingest output: each customer doc → the ProjectModel entity types it feeds →
a short fact list (provenance, no full-text dump). Schema:
[`schemas/source-manifest.schema.json`](../schemas/source-manifest.schema.json).

```json
{
  "generated": "2026-06-18T00:00:00Z",
  "sources": [
    {
      "path": "inputs/prd.pdf",
      "type": "pdf",
      "classified_as": ["FunctionalRequirement", "Overview", "UseCase"],
      "facts": [
        { "summary": "User can reset password via email link", "target": "FunctionalRequirement", "ref": "p.4 §2.1" }
      ],
      "warnings": []
    }
  ]
}
```

## 5. Classification table (external doc → ProjectModel entity)

Re-targeted from the superseded `writing-docs` taxonomy to **`normalized_schema`
entities**. Every target below is a real entity/field in `normalized_schema.py`
(verified). 1 source may feed N targets; ambiguous → surface at the G3 gate.

| Source doc | ProjectModel target (schema entity) |
|---|---|
| PRD / requirements | `FunctionalRequirement` (FR-*), `Overview.in_scope`/`out_of_scope`, `UseCase` (UC-*) |
| design / RFC | `Constraint` (CONS-*), `Assumption` (ASM-*), `Risk` (notes; no `design.md` in greenfield) |
| OpenAPI / API spec | `ExternalInterface` (INT-*), `ApiSpec.endpoints` (`api` output) |
| data dictionary / ER | `EntityDef` (ENT-*), `DataItem` (DATA-*), `Table`/`Column` (`db` output) |
| coding standards | `naming_conventions`/`lint_configs` (**code-derived — defer to `init`**) |
| ops / runbook | 90-operations (**no schema entity — defer**) |
| glossary | `GlossaryEntry` |
| meeting notes | `OpenQuestion` (Q-*), `Risk`, `Assumption` |

Items tagged **defer** are NOT seeded by the bridge; `init` backfills them from
code later (greenfield has no code yet → skip, never fabricate).

## 6. Canonical / drift rule + no-fiction invariant

Ported from the superseded plan, re-targeted to docs-hero:

- **CODE is canonical for HOW** (SYS-SPEC / source-derived facts).
- **External doc is canonical for WHAT / WHY** (FRs, scope, risks).
- **Conflict** → record a `drift` row (code wins), batched into **one** G3 gate
  (not per-conflict).
- **Greenfield has no code yet** → the external doc IS primary. Still **no fiction**:
  every seeded fact MUST trace to a `source_ref` (§7). If a fact has no source, it
  is a `<TBD>` / `OpenQuestion`, never an invented value.

## 7. Provenance (reconciled against the existing schema)

Reuse what `normalized_schema.py` already provides; add only what it can't express
(permitted by `_Base` `extra="allow"`):

| Need | How (schema-native first) |
|---|---|
| Where a fact came from | `entity.source: SourceRef` — `origin ∈ {pdf, excel, docx, openspec, manual, ...}`, `file_path`, `line_range`. **Reuse.** |
| Draft / unreconciled state | `entity.doc_status: "Draft"` (`DocStatus.DRAFT`). **Reuse — do NOT use `status`** (that enum is `active`/`deprecated` only). |
| Multiple contributing source files | `external_sources: ["<path>", ...]` — **extra field** (rides on `extra="allow"`), complements the single `source` ref. |

**Pitfall (locked):** entities have **two** status concepts — `status` (`active`/`deprecated`,
lifecycle) and `doc_status` (`Draft`/`In Review`/`Reviewed`/`Approved`/`Deferred`,
review state). Greenfield seeds use `doc_status: "Draft"`; leave `status` at its
`active` default.
