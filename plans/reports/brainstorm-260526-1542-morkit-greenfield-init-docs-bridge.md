# Brainstorm — morkit greenfield `/morkit:init` + change-spec → docs bridge

- Date: 2026-05-26
- Branch: feat/morkit-init-command
- Mode: brainstorm (advisory only — no implementation done)
- Scope: how `/morkit:init` behaves on a greenfield repo; how `docs/` stays accurate/complete as code grows

---

## Problem statement

User Q: chạy `/morkit:init` trên repo greenfield trống trơn thì ra gì?

Findings from reading the implementation:

- **init has NO greenfield branch.** Stage 0 only checks state of `docs/` — never checks whether *code* exists. Command copy claims "brownfield or greenfield" but every stage is scout-driven (code → docs).
- **On empty repo → hollow scaffold.** Scout finds nothing → 0 conditional folders → Stage 3 content generators (FEATURE-LIST, ARCHITECTURE, TEST-*, CODE-STANDARDS) have no source → bare placeholder templates, empty SOURCE-MAP/FEATURE-LIST/STACK, `CLAUDE.md` pointer into empty rooms. **Real hallucination risk** (LLM fills templates with plausible fiction).
- **Two artifact systems, easily confused:**
  - `docs/` taxonomy — persistent knowledge map, format owned end-to-end by skill `writing-docs` (init + docs update). Reverse-doc (code → docs).
  - `morkit/output/spec/<change>/` — ephemeral change-specs (proposal/design/tasks/spec), archived after merge. Owned by skill `propose`.
  - **Forward workflow (propose→execute) never produces `docs/` format** → redirecting greenfield users to propose does NOT give the originally-designed taxonomy. (This killed Option A.)
- **`docs update` is code-driven only.** Drift via front-matter `source_files`; re-scouts changed CODE; Step 5 grows conditional folders from CODE signals; requires `00-overview/` precondition. **Does NOT read change-specs** → the authored WHAT (spec.md WHEN/THEN scenarios, SHALL) and WHY (design.md decisions/alternatives) never flow into docs; they die in `archive/`.

## Requirements (what the solution must satisfy)

- Greenfield init must NOT emit fiction / hollow docs.
- `docs/` must end up in the **originally-designed taxonomy format** regardless of greenfield vs brownfield.
- As code grows, docs must backfill into the SAME format (no second format).
- Capture the authored WHAT/WHY (requirements, decisions, risks) that code cannot express, without letting stale intent poison code-truth.

---

## Approaches evaluated

| Option | Behavior on empty repo | Verdict |
|--------|------------------------|---------|
| **A — Redirect** | STOP, send user to `/morkit:propose` | ❌ propose ≠ docs/ format; docs/ stays empty; doesn't meet "right format" requirement |
| **C — Interview** | scout→interview to seed SCOPE/FEATURE/ARCH from answers | ❌ heavy; duplicates propose/brainstorming (DRY); speculative content drifts from code |
| **B — Seed skeleton** | detect empty → seed minimal correct-format spine; skip code-derived files; backfill later via `docs update` | ✅ only option guaranteeing correct format, no fiction, KISS |

---

## Final decision (LOCKED)

### 1. Greenfield handling = **Option B** + new detector

- **NEW** at init Stage 0: detect code-empty repo (no recognized manifest + ~0 source LOC; only `.git`/README/config = greenfield).
- Empty → **seed sub-mode** (skip scout-content pipeline; no stubs for code-derived files; no fiction).
- Seed spine (recommended default — confirm exact set at plan time):
  - `docs/00-overview/SCOPE.md` (human-authored project goal/scope)
  - `docs/00-overview/DOCUMENT-MAP.md` (taxonomy nav; note "populated as code grows")
  - `docs/10-requirements/FEATURE-LIST.md` (empty, FR-### ready)
  - root `CLAUDE.md` pointer (marker-block + approve gate)
  - `00-overview/` exists → satisfies `docs update` precondition.

### 2. Lifecycle = init seeds, `docs update` backfills

```
init (seed correct-format spine)  →  build code  →  docs update (Step 5 grows folders + backfills)
```
Format guaranteed: only `writing-docs` (init + docs update) touches `docs/`. Forward workflow never does.

### 3. **B+bridge** = `docs update` reads change-specs (LOCKED scope)

- **Source:** only **active / just-merged** changes under `morkit/output/spec/` (NOT `archive/`).
- **Files read:** **full 4** — `proposal.md` + `design.md` + `tasks.md` + `spec.md`.
- **Canonical-source rule** (conflict resolution — the core mechanism):

```
CODE canonical          → SYS-SPEC, SOURCE-MAP, DATA/API/UI-MAP          (spec = hint only)
design.md canonical     → 20-design/ADR, 40-ai-coding/RISK-REGISTER+KNOWN-PITFALLS
spec.md canonical       → 10-requirements/FEATURE-LIST, flows, 30-test/TEST-MATRIX  (verify vs code)
proposal.md             → SCOPE, FR descriptions
tasks.md Files block     → Source Anchors / SOURCE-MAP (hint, verifiable)
spec ⟂ code             → RECONCILE + flag "drift"; never trust spec blindly
```

### Mapping: change-spec → docs

| change-spec source | unique contribution (code can't give) | lands in docs |
|---|---|---|
| design.md Decisions+alternatives, Risks | the WHY | `20-design/ADR/`, `40-ai-coding/RISK-REGISTER`+`KNOWN-PITFALLS`, STACK, SCOPE(non-goals) |
| spec.md Requirements (SHALL) + Scenario (WHEN/THEN) | the WHAT / acceptance contract | FEATURE-LIST (FR-###), flows/, TEST-MATRIX (1 scenario = 1 test row) |
| tasks.md Files (Create/Modify/Test) | precise file targets | SYS-SPEC Source Anchors + SOURCE-MAP hint |
| proposal.md Why + Capabilities + Impact | motivation | SCOPE, FR descriptions |

---

## Coverage vs accuracy (rationale for the canonical rule)

- Reading the 4 files **raises coverage** (captures WHAT/WHY otherwise lost forever — code has no "SHALL", no "why X over Y").
- It does **NOT** auto-raise accuracy-vs-code; can *lower* it if spec treated as truth (specs = intent at plan time; code = ground truth; they diverge).
- Accuracy preserved by: code canonical for HOW; specs canonical only for WHAT/WHY; conflicts reconciled + flagged, never silently trusted. tasks.md Files give a cheap, verifiable accuracy boost (better-targeted scout).

---

## Workflows (for reference)

**Greenfield lifecycle:** empty repo → `init` seeds spine → build (direct or via propose/execute) → `docs update` grows folders + bridges active change-specs → mature docs in correct taxonomy.

**Per-task coding loop:** read `docs/` (DOCUMENT-MAP→SOURCE-MAP→SYS-SPEC+INVARIANTS, minimal context) → `propose` → review-checklist GATE (`Overall Decision: OK`) → `executing-plans` (TDD) → `deep-review` → merge → `docs update` (bridge while change still active) → `archive`. Note: bridge must run **before** archive (source is active changes only).

---

## Implementation scope (what changes in morkit — for the plan)

1. `skills/writing-docs/references/init-workflow.md` + `SKILL.md`: add greenfield detector at Stage 0 + seed sub-mode.
2. `skills/writing-docs/references/update-workflow.md`: add "read active change-specs (4 files)" step + bridge mapping + canonical-source/reconcile logic + drift flagging.
3. `00-overview/DOCUMENT-MAP` template: encode canonical-source rules.
4. Sequencing note in coding-task docs: run `docs update` (bridge) before `archive`.

## Risks

- Stale spec poisoning accuracy if reconcile logic is weak → must flag drift, code wins.
- FR-### dedup/merge across multiple active changes touching same feature.
- Cost: reading 4 files × each active change per update run.
- Seed `SCOPE`/`FEATURE-LIST` have no `source_files` → drift-detection won't auto-refresh them (human-owned; acceptable).

## Success criteria

- Greenfield `init` emits zero fiction; only seed spine + pointer.
- `docs update` on an active change: decisions→ADR, scenarios→TEST-MATRIX/flows, requirements→FEATURE-LIST(FR-###), Files→Source Anchors.
- spec⟂code conflicts surfaced as drift, not silently written.
- Single consistent taxonomy format across init + update.

## Unresolved questions

1. Exact greenfield detection threshold (LOC=0? config-only repo? partially-empty monorepo module?).
2. Confirm seed spine file set (SCOPE + DOCUMENT-MAP + FEATURE-LIST + CLAUDE.md; is STACK/intended-ARCHITECTURE wanted?).
3. Precise definition of "active / just-merged" for the bridge (all non-archived under `morkit/output/spec/`? require tasks fully ticked? require git-merged signal?).
4. Reconcile mechanics: how to auto-detect spec⟂code vs defer to human flag.
5. FR-### dedup strategy when several active changes map to the same feature.
