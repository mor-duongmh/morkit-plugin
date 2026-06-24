# 機能一覧 / Function List — {{PROJECT_NAME}}

> **BrSE format** (JP ITO clients). Function-list rows. Columns mirror SRS §3.1 so
> the SRS later fills from this with zero remap (`FUNC-ID→FR-ID`, `Function→Function`,
> `Description→Summary`, `Actor→Role`, `Priority→Priority`, `Source→Source`).
> All rows are `doc_status: Draft` until reconciled (greenfield). Every row carries a Source.

| FUNC-ID | 機能名 / Function | 概要 / Description | アクター / Actor | 優先度 / Priority | 関連FR / Related FR | Source |
|---|---|---|---|---|---|---|
| FUNC-001 | {{function name}} | {{what it does, 1 line}} | {{actor/role}} | High | FR-001 | inputs/prd.pdf §2.1 |
| FUNC-002 | {{function name}} | {{what it does}} | {{actor}} | Mid | FR-002 | inputs/prd.pdf §2.2 |

**Priority:** `High` · `Mid` · `Low` (or MoSCoW `Must`/`Should`/`Could`/`Won't`).

<!-- Bridge mapping (build-project-model): each row → FunctionalRequirement{
  id: FR-00x (from Related FR, else derive from FUNC-id), name: Function,
  description: Description, role: Actor, priority: Priority,
  source: SourceRef(origin from file), doc_status: "Draft" }. -->
