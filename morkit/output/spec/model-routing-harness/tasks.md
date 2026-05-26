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
- `claude-plugins/plugins/morkit/hooks/subagent-start-gate.sh` — Codex SubagentStart gate
- `claude-plugins/plugins/morkit/hooks/userpromptsubmit-route.sh` — Codex UserPromptSubmit injector
- `claude-plugins/.codex/agents/*.toml` (or config block) — Codex custom agents with model baked per agent_type

### Modified files

- `claude-plugins/.claude/helpers/router.js` — emit `{ agent, tier, model, confidence, reason, escalators }`
- `claude-plugins/.claude/helpers/hook-handler.cjs` — route handler prints routing plan incl. tier/model; new `agent-gate` + `subagent-outcome` handlers
- `claude-plugins/.claude/settings.json` — add `PreToolUse(Agent)` + `PostToolUse(Agent)` matchers; keep scope to claude-plugins
- `claude-plugins/plugins/morkit/hooks/hooks.json` — add `UserPromptSubmit` + `SubagentStart` + `SubagentStop` events
- `claude-plugins/plugins/morkit/skills/using-morkit/references/codex-tools.md` — document `fork_turns:"none"` requirement for model override
- `claude-plugins/plugins/morkit/skills/subagent-driven-development/SKILL.md` — link abstract tiers to policy + concrete models

### Deleted files

- (none)

---

## Task 1: Spike — verify Codex & embedding assumptions (Q1–Q3)

**Files:**

- Create: `claude-plugins/morkit/output/spec/model-routing-harness/spike-findings.md`

**TDD steps:**

- [ ] Write a probe: enable `multi_agent`, call `spawn_agent({model, fork_turns:"none"})`, assert the worker runs the overridden model (Q1: v1 vs v2)
- [ ] Write a probe: register a `SubagentStart` Codex hook that exits non-zero; assert whether the spawn is blocked or only annotated (Q2)
- [ ] Write a probe: run `embeddings_generate`/`intelligence.cjs` offline (no network); assert a vector is produced without API (Q3)
- [ ] Record results in `spike-findings.md`; decide strict-vs-advisory for Codex gate and embeddings-on/off for V1
- [ ] Commit

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
- [ ] Implement scorer wired to `embeddings_*`/`intelligence.cjs`
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
- [ ] Implement outcome logging + `adaptiveAdjust(agent,bucket,tier)`
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

## Task 7: Codex enforcement (inject + custom agents + SubagentStart gate)

**Files:**

- Create: `claude-plugins/plugins/morkit/hooks/userpromptsubmit-route.sh`
- Create: `claude-plugins/plugins/morkit/hooks/subagent-start-gate.sh`
- Create: `claude-plugins/.codex/agents/*.toml` (or `[agents.*]` config block)
- Modify: `claude-plugins/plugins/morkit/hooks/hooks.json`
- Modify: `claude-plugins/plugins/morkit/skills/using-morkit/references/codex-tools.md`

**TDD steps:**

- [ ] Write failing test: `userpromptsubmit-route.sh` emits the same `[ROUTING]` additionalContext line as Claude (shared router invoked with `--harness codex`)
- [ ] Write failing test: custom agents define `model` per agent_type matching `tierModel.codex`
- [ ] Write failing test (per Q2 outcome): `subagent-start-gate.sh` blocks via exit-code when supported, else emits `systemMessage` advisory
- [ ] Implement hooks + custom agents; register `UserPromptSubmit`/`SubagentStart`/`SubagentStop` in `hooks.json`
- [ ] Document `spawn_agent(... fork_turns:"none")` requirement in `codex-tools.md`
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

*Generated: 2026-05-26T04:03:06Z*
