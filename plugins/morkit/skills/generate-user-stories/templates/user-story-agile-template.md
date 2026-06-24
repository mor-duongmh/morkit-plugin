# User Stories — {{PROJECT_NAME}}

> **Agile format**. `As-a / I-want / So-that` rows with acceptance criteria.
> Same underlying items as the BrSE function list — different renderer. All rows
> are `doc_status: Draft` (greenfield); every row carries a Source.

| US-ID | As a (role) | I want (goal) | So that (benefit) | Acceptance criteria | Priority | Source |
|---|---|---|---|---|---|---|
| US-001 | {{role}} | {{goal}} | {{benefit}} | Given … When … Then … | High | inputs/prd.pdf §2.1 |
| US-002 | {{role}} | {{goal}} | {{benefit}} | Given … When … Then … | Mid | inputs/prd.pdf §2.2 |

**Priority:** `High` · `Mid` · `Low` (or MoSCoW).

<!-- Bridge mapping (build-project-model): each row → UseCase{
  id: UC-00x, name: goal, actor: role, summary: benefit,
  main_success_scenario: [acceptance steps], priority: Priority,
  source: SourceRef } (+ a derived FunctionalRequirement when the story implies
  a concrete function). doc_status: "Draft". -->
