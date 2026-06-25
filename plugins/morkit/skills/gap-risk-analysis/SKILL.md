---
name: gap-risk-analysis
description: "Read the greenfield user-story list + brainstorm report (+ source manifest) and emit two standalone canonical artifacts — gap-analysis.md and risk-register.md — with fixed templates and numeric risk scoring (H/M/L→3/2/1, Score=Prob×Impact, High≥6 requires mitigation). These are the G3 BA-review gate, then sync into ProjectModel so SRS §13 (Risks) and §12 (Open Q&A) render from the same data."
category: documentation
keywords: [gap-analysis, risk-register, risk-scoring, brse, ba, srs, greenfield, traceability]
argument-hint: "--workspace morkit/output/greenfield/<proj>"
metadata:
  author: morkit-greenfield
  version: "1.0.0"
---

# Gap & Risk Analysis

Stage **G3** of `/morkit:greenfield`. Produces the BA's two review artifacts.
They are the **canonical** source — ProjectModel and SRS derive from them, never
the reverse.

> Conventions: [`../greenfield-orchestrator/references/greenfield-conventions.md`](../greenfield-orchestrator/references/greenfield-conventions.md).
> Scoring helper: [`scripts/compute_risk_score.py`](scripts/compute_risk_score.py).
> Templates: [`templates/gap-analysis-template.md`](templates/gap-analysis-template.md),
> [`templates/risk-register-template.md`](templates/risk-register-template.md).

## Inputs

From the run workspace `morkit/output/greenfield/<proj>/`:
- `user-story-list.md` (G2) — the FR/US set gaps & risks attach to.
- `brainstorm-report.md` (G1) — scope, goals, mentioned constraints/risks.
- `source-manifest.json` — provenance for each fact.

## Output (two canonical files)

- `gap-analysis.md` — from the gap template. Columns:
  `GAP-ID | Description | Affected US/FR | Type(new-requirement|out-of-scope) | Severity(blocker|warning|info) | Recommended Action | Resolution`.
- `risk-register.md` — from the risk template. Columns:
  `Risk-ID | Category | Risk | Probability(H/M/L) | Impact(H/M/L) | Score(1-9) | High? | Mitigation | Owner | Status`.
  Categories: `Technical · Business · Dependency · Gaps`.

## Procedure

1. **Enumerate gaps.** For each ambiguous/missing input, write a `GAP-00x` row;
   tag `new-requirement` vs `out-of-scope`; set severity; link the affected
   `US-*`/`FR-*` id. A High-impact gap also gets a `Gaps`-category risk row.
2. **Enumerate risks** per category (`Technical`, `Business`, `Dependency`, plus
   `Gaps` from step 1).
3. **Score** every risk with the helper — do not hand-compute:
   ```bash
   PY="${HOME}/.claude/plugins/data/docs-hero/.venv/bin/python3"
   "$PY" scripts/compute_risk_score.py --prob H --impact M     # → score=6 high=True
   ```
   Fill `Score` and `High?`. **Every High risk MUST have a Mitigation** — validate
   the whole register before finishing:
   ```bash
   "$PY" scripts/compute_risk_score.py --rows /tmp/risk-rows.json   # exits 1 on any High-without-mitigation
   ```
   (`risk-rows.json` = `[{"id","probability","impact","mitigation","score"}, …]`.)
4. **Render** both files from the templates into the workspace.
5. **G3 GATE — BA review.** Present a summary via `AskUserQuestion`:
   `Proceed` / `Adjust` (revise rows) / `Abort`. Persist the decision into
   `state.json` (`stages.G3.gate`).
6. **Sync into ProjectModel** (done by the `build-project-model` bridge at G5, not
   here): risk rows → `constraints_risks.risks[]`; `new-requirement` gaps needing
   an answer → `open_questions[]`; `out-of-scope` gaps → `overview.out_of_scope[]`.
   The register stays canonical; SRS §13.3/§12 render derived. Mapping is documented
   in the template footers so the bridge has a 1:1 column map.

## Single-source-of-truth rule

Never edit a risk in both `risk-register.md` and the SRS. The register is
canonical; the SRS §13.3 table is a *render* of it. Same for gaps → §12 Q&A.

## Tests

`tests/test_compute_risk_score.py` — full 3×3 scoring truth table, High≥6
threshold, High-without-mitigation rejection, High/Mid/Low alias folding,
precomputed-score mismatch detection.
