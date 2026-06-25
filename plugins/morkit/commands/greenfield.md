---
name: "morkit:greenfield"
description: Run the greenfield BA/BrSE documentation pipeline — turn customer docs + a brainstorm into user stories, gap/risk analysis, a validated ProjectModel, and a full docs/ set (SRS + design docs) via a stateful, resume-able guide (stages G0→G7, 4 human gates).
category: Workflow
tags: [greenfield, brse, ba, srs, docs, pipeline, japan-ito]
argument-hint: "<proj> [--format brse|agile] [--lang JP|EN|VN] [--resume]"
---

Invoke the `greenfield-orchestrator` skill using the Skill tool. Pass through any
arguments the user provided (`<proj>`, `--format`, `--lang`, `--resume`).

The skill will:
- Initialize (or resume from) `morkit/output/greenfield/<proj>/state.json`.
- Walk stages **G0→G7**, delegating each to the owning skill:
  - **G1** `/morkit:brainstorming` → `brainstorm-report.md`
  - **G2** `generate-user-stories --format brse|agile` → `user-story-list.md` *(BrSE confirm gate)*
  - **G3** `gap-risk-analysis` → `gap-analysis.md` + `risk-register.md` *(BA gate)*
  - **G4** `clarification-loop` → `clarification-log.md` *(clarification gate)*
  - **G5** `build-project-model` → validated `project-model.json` 🌉
  - **G6** `/morkit:init --outputs srs` + visualize → `docs/srs.md`, `srs.html` *(stakeholder gate)*
  - **G7** `/morkit:init --outputs arch,standards,summary,db` → `docs/*.md`
  - **QA** `docs-reviewer` agent validates the full `docs/` set (cross-refs + BrSE quality + Mermaid) → QA report
- Enforce the **4 human gates** (G2, G3, G4, G6) and persist each decision into
  `state.json` so the run is resume-able after a kill.

Prerequisite: the docs-hero venv (`/morkit:setup`). Default `--format brse`,
`--lang EN`. The orchestrator holds no business logic — every stage skill also
runs standalone.

> `/morkit:greenfield` is the direct shortcut into the **greenfield branch** of
> `/morkit:init` — same pipeline. Use `/morkit:init` if you want to be asked
> greenfield vs brownfield first.
