# model-routing-harness — Implementation Tasks

> **For agentic workers:** REQUIRED SUB-SKILL: Use morkit:subagent-driven-development (recommended) or morkit:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> ⚠️ **PLAN-REVIEW-GATE REQUIRED:** Before executing this plan, run `/morkit:review` to generate a developer review checklist, tick all applicable items, and set `Overall Decision: OK`. Implementation skills will refuse to proceed until the gate is open.

**Goal:** Add a model-tier dimension to the harness router and enforce it at the subagent layer, dual-target (Claude Code + Codex CLI), self-contained inside `claude-plugins`.

**Architecture:** One source, three layers (Policy / Decision / Enforce) per `design.md`. Decision logic is harness-agnostic; only enforcement splits per harness. Main session model is never switched — only per-subagent models are routed.

**Tech Stack:** Node.js (CJS) for `router.js`/`hook-handler.cjs`/`intelligence.cjs`; Bash for Codex hook scripts; JSON `model-policy.json`; TOML Codex custom agents; reuse `mcp__claude-flow__embeddings_*` for complexity scoring.

---

## File Structure

### New files

- `claude-plugins/.claude/helpers/model-policy.json` — shared policy (tiers, maps, thresholds)
- `claude-plugins/.claude/helpers/model-router.js` — tier computation module (wraps/extends agent router)
- `claude-plugins/.claude/helpers/complexity-scorer.cjs` — embedding-based complexity score + keyword escalators
- `claude-plugins/.claude/helpers/embeddings/complexity-refset.json` — seeded labelled reference set
- `claude-plugins/.claude/hooks/pretooluse-agent-gate.cjs` — Claude PreToolUse(Agent) enforcement
- `claude-plugins/plugins/morkit/hooks/userpromptsubmit-route.sh` — Codex UserPromptSubmit injector (advisory)
- `claude-plugins/.codex/agents/*.toml` (or config block) — Codex custom agents with model baked per agent_type

### Modified files

- `claude-plugins/.claude/helpers/router.js` — emit `{ agent, tier, model, confidence, reason, escalators }`
- `claude-plugins/.claude/helpers/hook-handler.cjs` — route handler prints routing plan incl. tier/model; new `agent-gate` + outcome (`Stop`/`PostToolUse`) handlers
- `claude-plugins/.claude/settings.json` — add `PreToolUse(Agent)` + `PostToolUse(Agent)` matchers; keep scope to claude-plugins
- `claude-plugins/plugins/morkit/hooks/hooks.json` — add `UserPromptSubmit` + `Stop` events (NO `SubagentStart`/`SubagentStop` — absent in Codex v0.130.0 per spike)
- `claude-plugins/plugins/morkit/skills/using-morkit/references/codex-tools.md` — document `fork_turns:"none"` requirement for model override
- `claude-plugins/plugins/morkit/skills/subagent-driven-development/SKILL.md` — link abstract tiers to policy + concrete models

### Deleted files

- (none)

---

## Task 1: Spike — verify Codex & embedding assumptions (Q1–Q3)

**Files:**

- Create: `claude-plugins/morkit/output/spec/model-routing-harness/spike-findings.md`

**TDD steps:**

- [x] Q1: `spawn_agent` model override under `multi_agent` v1 → VERIFIED-YES (needs `fork_turns:"none"`; v2 not required)
- [x] Q2: Codex `SubagentStart` block → VERIFIED-NO (event absent in v0.130.0) → Codex gate = ADVISORY
- [x] Q3: offline embeddings via `embeddings_*` local ONNX → VERIFIED-YES (`intelligence.cjs` is NOT an embedder)
- [x] Recorded results in `spike-findings.md`; updated design.md + Tasks 4/5/7
- [x] Commit (`46bc6aa`)

---

## Task 2: Policy file + loader

**Files:**

- Create: `claude-plugins/.claude/helpers/model-policy.json`
- Modify: `claude-plugins/.claude/helpers/router.js`

**TDD steps:**

- [ ] Write failing test: loader parses `model-policy.json` and exposes `agentBase`, `escalators`, `tierModel[harness]`, `complexity`, `adaptive`
- [ ] Write failing test: missing/invalid policy file ⇒ loader returns null and router falls back to agent-only behavior
- [ ] Implement policy loader + JSON schema validation
- [ ] Refactor for clarity
- [ ] Commit

---

## Task 3: Router tier computation (agent base + escalators + confidence gate)

**Files:**

- Modify: `claude-plugins/.claude/helpers/router.js`
- Create: `claude-plugins/.claude/helpers/model-router.js`

**TDD steps:**

- [ ] Write failing test: `coder` base→tier 2; `tester`→tier 1; `architect`→tier 3
- [ ] Write failing test: prompt with `security`/`migration`/≥3 files bumps +1; `rename`/`typo` bumps -1; tier clamped 0–3
- [ ] Write failing test: low confidence (≤0.5) forbids any downgrade
- [ ] Write failing test: `routeTask(prompt,{harness})` returns `{agent,tier,model,confidence,reason,escalators}` with `model` from `tierModel[harness][tier]`
- [ ] Implement tier computation + harness-aware model mapping
- [ ] Refactor for clarity
- [ ] Commit

---

## Task 4: Embedding complexity scorer (gated by Q3)

**Files:**

- Create: `claude-plugins/.claude/helpers/complexity-scorer.cjs`
- Create: `claude-plugins/.claude/helpers/embeddings/complexity-refset.json`

**TDD steps:**

- [ ] Seed reference set: ≥10 labelled prompts each for simple/medium/complex
- [ ] Write failing test: scorer returns a bucket + a complexity-confidence in [0,1] via cosine to ref-set
- [ ] Write failing test: when `complexity.enabled=false` or embeddings unavailable, scorer returns `null` and router uses keyword-only path
- [ ] Write failing test: strict deny only engages when complexity-confidence ≥ `confidenceMin`; below ⇒ `warn`
- [ ] Implement scorer wired to `embeddings_*` (local ONNX `Xenova/all-MiniLM-L6-v2`, 384-dim, cosine) — NOT `intelligence.cjs` (it has no embeddings)
- [ ] Pin/vendor the ONNX model so V1 has no first-run network dependency
- [ ] Commit

---

## Task 5: Adaptive feedback loop

**Files:**

- Modify: `claude-plugins/.claude/helpers/intelligence.cjs`
- Modify: `claude-plugins/.claude/helpers/hook-handler.cjs`

**TDD steps:**

- [ ] Write failing test: `recordOutcome(agent,bucket,tier,outcome)` persists rows keyed by `(agent,bucket)`
- [ ] Write failing test: a bucket with ≥`minSamples` repeated retry/escalate auto-bumps base tier by +1
- [ ] Write failing test: hysteresis prevents bump/unbump oscillation within `hysteresis` window
- [ ] Write failing test: Codex outcome is captured at `Stop`/`PostToolUse` (no `SubagentStop` in v0.130.0)
- [ ] Implement outcome logging + `adaptiveAdjust(agent,bucket,tier)` (intelligence.cjs as persistence backing, not embedder)
- [ ] Refactor for clarity
- [ ] Commit

---

## Task 6: Claude Code enforcement (inject + PreToolUse gate)

**Files:**

- Modify: `claude-plugins/.claude/helpers/hook-handler.cjs`
- Create: `claude-plugins/.claude/hooks/pretooluse-agent-gate.cjs`
- Modify: `claude-plugins/.claude/settings.json`

**TDD steps:**

- [ ] Write failing test: `route` handler prints `[ROUTING] agent=… tier=… model=…` line for a sample prompt
- [ ] Write failing test: gate receives an `Agent` tool_input with mismatched `model` + high confidence ⇒ returns deny + corrective message naming the policy model
- [ ] Write failing test: gate allows when `model` matches policy OR confidence below `confidenceMin` (warn-only)
- [ ] Implement gate handler; wire `PreToolUse(Agent)` + `PostToolUse(Agent)` in `settings.json` scoped to claude-plugins
- [ ] Commit

---

## Task 7: Codex enforcement (advisory — inject + model-baked custom agents)

> Re-scoped per spike Q2: Codex v0.130.0 has NO `SubagentStart`/`SubagentStop` hook, so there is no strict pre-spawn gate. Enforcement = `UserPromptSubmit` inject + model baked per `agent_type` in custom agents (correct-by-construction) + `fork_turns:"none"` for per-call override. A strict gate is deferred behind a future-build feature check.

**Files:**

- Create: `claude-plugins/plugins/morkit/hooks/userpromptsubmit-route.sh`
- Create: `claude-plugins/.codex/agents/*.toml` (or `[agents.*]` config block)
- Modify: `claude-plugins/plugins/morkit/hooks/hooks.json`
- Modify: `claude-plugins/plugins/morkit/skills/using-morkit/references/codex-tools.md`

**TDD steps:**

- [ ] Write failing test: `userpromptsubmit-route.sh` emits the same `[ROUTING]` additionalContext line as Claude (shared router invoked with `--harness codex`)
- [ ] Write failing test: custom agents define `model` per agent_type matching `tierModel.codex`
- [ ] Write failing test: `hooks.json` registers only events that exist in v0.130.0 (`UserPromptSubmit`, `Stop`); no `SubagentStart`/`SubagentStop`
- [ ] Implement hook + custom agents; register `UserPromptSubmit`/`Stop` in `hooks.json`
- [ ] Document `spawn_agent(... fork_turns:"none")` requirement in `codex-tools.md`
- [ ] (Optional) Behavioral confirmation of Q1 via a guarded live `codex exec` spawn (isolated CODEX_HOME) before shipping
- [ ] Commit

---

## Task 8: Scope guard + guidance docs + end-to-end check

**Files:**

- Modify: `claude-plugins/.claude/settings.json`
- Modify: `claude-plugins/plugins/morkit/skills/subagent-driven-development/SKILL.md`

**TDD steps:**

- [ ] Write failing test: routing/model-tier logic activates only when project dir is under `claude-plugins`; no-ops elsewhere
- [ ] Write failing test: with policy absent, behavior is identical to current agent-only routing (backward-compatible)
- [ ] Link abstract tier guidance in `SKILL.md` to `model-policy.json` concrete models
- [ ] Run an end-to-end smoke on both harnesses (Claude `Agent({model})`, Codex `spawn_agent`)
- [ ] Commit

---

## Task 9: Complexity live-wiring perf follow-up (DEFERRED — default OFF)

> **Status:** Complexity scoring in the hook path is gated behind `policy.complexity.liveInHook` (boolean, **default false**). When false (current default), the hook uses keyword-only tier computation with no subprocess shelling. The `computeTierWithPolicy` seam is fully wired; enabling it is a one-flag change in `model-policy.json`.

> **Reason for deferral:** the embedding CLI backend shells out ~1.4 s/call (30 reference prompts × per-call latency on first run), exceeding the 5 s hook safety budget. This will be resolved by either (a) pre-warming the reference-set embeddings in-process or (b) replacing the CLI backend with a lighter scorer.

**Files:** (when undeferred)

- `claude-plugins/.claude/helpers/model-policy.json` — set `complexity.liveInHook: true`
- `claude-plugins/.claude/helpers/complexity-scorer.cjs` — optimize backend (pre-warm / lighter)
- `claude-plugins/morkit/output/spec/model-routing-harness/design.md` — update V2-deferred note

---

*Generated: 2026-05-26T04:03:06Z*
