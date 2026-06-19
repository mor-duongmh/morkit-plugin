# Morkit `/morkit:greenfield` Pipeline Delivery — Commit TBD

**Date**: 2026-06-18 18:48
**Severity**: Medium
**Component**: `plugins/morkit/skills/greenfield-orchestrator/`, `build-project-model/`, `gap-risk-analysis/`, `generate-user-stories/`, `clarification-loop/` (new)
**Status**: Resolved

## What Happened

Implemented the full `/morkit:greenfield` BA/BrSE documentation pipeline — all 6 phases of the locked greenfield plan. This closes the **missing gap**: turning customer docs + a brainstorm into a validated `ProjectModel` and a complete docs/ set, with zero hand-authored JSON. Built on the **docs-hero architecture** (`Python/venv`, `ProjectModel` Pydantic schema, `normalized_schema.py`) — not the reverted `writing-docs`. Hybrid approach: built only the missing pieces + a thin stateful orchestrator; reused `parse_inputs.py`, `normalized_schema.py`, `dispatch_coordinator.py init`, and the SRS template.

**Delivered**: 5 new skills (greenfield-orchestrator, build-project-model, gap-risk-analysis, generate-user-stories, clarification-loop) + 1 command (`/morkit:greenfield`) + docs-site registration (new "Greenfield pipeline" skill group; `build.py` now registers 32 skills + 17 commands).

## The Brutal Truth

This feels like *completeness*, and it is — but it carries the weight of a deferred architectural decision. The whole pipeline hinges on Phase 2 (the ProjectModel bridge), which is an LLM writing raw `project-model.json` + a Python validator checking it loads against the Pydantic `ProjectModel` schema. That works, but it's **not automatic**. An LLM-authored JSON file passes validation only if the LLM understood `normalized_schema.py` correctly. There's no self-healing, no auto-correction — if the JSON is structurally valid but semantically wrong (e.g., a FR with both `status:"active"` and `doc_status:"Draft"`), it passes the Pydantic gate and silently breaks downstream. We caught this in code review (H-1: `status:"draft"` on `meta` passes silently), fixed it with a post-parse lint, but the root tension remains: **Pydantic validation ≠ semantic correctness**. That gap will haunt us when LLMs start authoring more complex ProjectModels. Worth documenting for the next person.

The delivery itself was tight — 6 phases in 1 session, tests passing, review done. But the sense of "done" is incomplete until an LLM actually authors a ProjectModel in the wild and we see what breaks.

## Technical Details

**Keystone (Phase 2): ProjectModel Bridge**
- An LLM authors `project-model.json` conforming to `normalized_schema.py` (which defines `ProjectModel` as a Pydantic model with `extra="allow"` for forward compatibility).
- `validate_project_model.py` loads the JSON and calls `ProjectModel.model_validate(data)`.
- If validation passes, the JSON is **guaranteed** to be loadable by `dispatch_coordinator.py init --project-model <file> --outputs srs,api,db,…`.
- **Proven end-to-end**: Bridge JSON → `init` → `docs/srs.md` (FRs traced to source via RTM in §11).

**Stages G0–G7 with 3 Human Gates**
- G0 (brainstorm) → G1 (ingest docs) → **[G2: BA review]** → G3 (gap-risk analysis) → **[G4: Clarification]** → G5 (user-stories) → **[G6: Stakeholder review]** → G7 (render final docs)
- **State machine**: atomic `state.json` + `.md` artifacts (gap-analysis.md, risk-register.md, user-stories.md, srs.md). Resume-able via `state_manager.py` (`advance`, `set-stage`, `set-gate` subcommands).

**Risk Scoring (Locked)**
- Probability/Impact ∈ {H, M, L} → {3, 2, 1}.
- Score = Prob × Impact (range 1–9).
- High = Score ≥ 6 (HH=9, HM/MH=6).
- **Enforcement**: High risk REQUIRES non-empty mitigation (whitespace rejected). Validated in `compute_risk_score.py:76` using `.strip()`.
- Risk & Gap analyses are standalone canonical (`risk-register.md`, `gap-analysis.md`), then synced into ProjectModel entities and rendered in SRS §12/§13 (single source of truth).

**Provenance Pitfall Discovered & Locked**
- ProjectModel entities have **two status concepts**: `status` (active/deprecated enum) vs `doc_status` (Draft/InReview/… for tracking, greenfield uses "Draft").
- **Locked rule**: Greenfield "draft" provenance MUST use `doc_status:"Draft"`, NOT `status:"draft"`.
- Code review (H-1) caught: `status:"draft"` on `meta` passes silently (because `meta` is `_Base`, not `_Entity`, and has `extra="allow"`).
- **Fix applied**: Post-parse lint pass in `validate_project_model.py` walks raw dict; flags any `status:"draft"` (not on `_Entity` subclasses) with a clear error message.

**Clarification Loop Depth (Deferred)**
- Implemented as **template-only** (no state machine). Clarification state lives in markdown; the operator edits `.md` artifacts and calls `greenfield advance --from-gate G4` to move forward.
- State-machine approach deferred to v2 (YAGNI — template-only works; complexity not needed yet).

## What We Tried

1. **Phase 01** (Foundation & conventions): Locked stage names, gate semantics, provenance rules, risk-scoring formula.
2. **Phase 02** (Bridge + doc-ingest): Built `build-project-model` skill + `validate_project_model.py`; verified `parse_inputs.py` (PDF/Docx/Excel/OpenSpec intake) works; end-to-end test: seed JSON → validate → init → SRS.
3. **Phase 03** (Gap-Risk analysis): Built `gap-risk-analysis` skill + `compute_risk_score.py`; risk matrix (3×3 Prob/Impact) validated against locked High/Med/Low thresholds; mitigations enforced (not optional).
4. **Phase 04** (User-stories generator): Built `generate-user-stories` skill; 2 output formats (`--format brse` → function-list, `--format agile` → As-a/I-want/So-that); both map to ProjectModel FR/UseCase.
5. **Phase 05** (Clarification loop): Built `clarification-loop` skill (template-only, no state machine); operator edits `.md` to clarify; advance to next gate.
6. **Phase 06** (Orchestrator + visualize): Built `greenfield-orchestrator` skill + `state_manager.py` (atomic state.json, gate/stage controls); wired `/morkit:greenfield` command; docs-site registration (32 skills + 17 commands).

## Root Cause Analysis: The Bridge Question

Why did we build the ProjectModel bridge at all? The original plan (260527) targeted the deleted `writing-docs` skill — a hand-authored `project-model.json` was supposed to come *from* writing-docs output. When `writing-docs` was reverted, we had a choice:

1. **Resurrect `writing-docs`** — author ProjectModel via a separate LLM flow (complex, dual-skill orchestration).
2. **Build the bridge** — LLM authors JSON directly in Phase 2, validate it, consume it in Phase 6 (simpler, tighter).
3. **Skip greenfield** — keep the brainstorm→init path broken until someone invents a new input flow.

We chose #2 because:
- It's **DRY**: reuse the existing Pydantic schema + validation.
- It **closes the loop end-to-end** in one skill.
- **No new auth gates** — the LLM output is JSON in markdown (no executor context needed).

The cost: **semantic correctness depends on LLM understanding**. A Pydantic `extra="allow"` means the schema is forward-compatible but also forgiving. We locked the provenance pitfall in code review (H-1), but the tension remains.

## Verification + Gotchas

**Test Coverage**: 48 new tests across 4 modules + 281 existing docs-hero tests (all pass, no regression).

**Code Review**: 7.5 / 10 (APPROVE WITH CHANGES).
- **Critical**: None.
- **High-1** (FIXED): `status:"draft"` on `meta` was silently accepted → added post-parse lint in `validate_project_model.py`.
- **High-2** (DEFERRED): Cheatsheet error discovery (not code change).
- **Medium-1** (FIXED): `compute_risk_score.py:79` crashed on non-integer score (e.g., "6.5") with unguarded `int()` → wrapped in try/except with clean error message.
- **Medium-2** (FIXED): Atomic write left orphan `.tmp` on mid-write kill; unique temp via `tempfile.mkstemp()` + `finally` cleanup + `fsync`.
- **Medium-3** (FIXED): Inconsistent CLI error handling (two scripts leaked raw tracebacks) → wrapped JSON loads in try/except, return exit code 2 with clean `ERROR:` message (matching the contract set by validator scripts).

**Runtime Environment**: Python 3.9.6 (venv) — all scripts use `from __future__ import annotations` to keep bare `str | Path` unions string-ified (no 3.10+ unions).

**Test Infrastructure**: New test dirs deliberately omit `__init__.py` (pytest collects by file name, not package discovery) to avoid a `tests` package-name clash when collecting from multiple skills' test dirs together.

## Lessons Learned

1. **Semantic validation ≠ Structural validation**: Pydantic catches JSON shape; it doesn't catch intent. A `project-model.json` passing `model_validate()` is structurally sound, not semantically correct. Future bridge versions need downstream lint checks (post-parse, raw-dict inspection) to catch cross-field confusion (e.g., wrong status field).

2. **Atomic writes are subtle**: `os.replace()` is atomic on the *target*, but the tmp path matters. Use `tempfile.mkstemp()` for uniqueness (no cross-process collisions) + `fsync` for durability + `finally` cleanup (no orphans).

3. **Error exit codes are contracts**: A script that sometimes returns 1 (crash) and sometimes 2 (validation fail) is unpredictable for scripted callers. Lock the contract early: internal errors → exit code 1 (rare), user input errors → exit code 2 (expected, clean message).

4. **Reuse > rebuild**: The bridge wouldn't work without `normalized_schema.py` (already shipping) and `parse_inputs.py` (already shipping). Building new validation logic was ~150 lines; building a new schema would have been 500+. DRY saved us.

5. **Deferred state machines are OK when template-only works**: The clarification loop doesn't need state tracking — it's just "operator edits `.md`, calls `advance`". Deferring the state-machine version to v2 kept the MVP simple (YAGNI).

## Next Steps

1. **LLM Testing**: Have an LLM author a real `project-model.json` (e.g., for a sample brainstorm) and observe what fails in validation or downstream rendering. This will expose semantic gaps the Pydantic schema doesn't catch.

2. **Docs Site**: Regenerate `docs-site/` (32 skills + 17 commands now registered); verify greenfield pipeline group appears; test command links.

3. **Integration**: End-to-end test: brainstorm → doc ingest → ProjectModel → init → SRS rendering. Verify RTM (§11) traces FRs to source.

4. **Documentation**: Publish schema cheatsheet + example `project-model.json` in `docs/` or skill README.

5. **Version Release**: Plugin.json still at 1.2.0 (release timing decision for maintainer). Docs/index.html marketing counts left stale (not critical).

**Owner**: (Maintainer to integrate, test with real LLM output, release)

---

**Source reports**:
- `/Users/dangtuanphong/Desktop/claude-plugins/plans/260618-1755-morkit-greenfield-pipeline/reports/tester-260618-greenfield-pipeline.md`
- `/Users/dangtuanphong/Desktop/claude-plugins/plans/260618-1755-morkit-greenfield-pipeline/reports/reviewer-260618-greenfield-pipeline.md`

**Plan**: `/Users/dangtuanphong/Desktop/claude-plugins/plans/260618-1755-morkit-greenfield-pipeline/`
