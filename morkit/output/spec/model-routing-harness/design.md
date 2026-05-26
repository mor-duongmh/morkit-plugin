# Design: model-routing-harness

## Architecture

One source, three layers. The decision logic is harness-agnostic; only the enforcement layer is split per harness.

```
┌─ POLICY (shared) ─ model-policy.json ─────────────────────────────┐
│ • abstract tiers 0/1/2/3                                          │
│ • agent → base-tier map                                          │
│ • escalator keywords (+1 / -1)                                   │
│ • embedding-complexity config (thresholds, ref-set path)         │
│ • confidence gate                                                │
│ • tier → concrete model PER HARNESS                              │
│     claude: 0=direct 1=haiku 2=sonnet 3=opus                     │
│     codex : 1=gpt-5.4-mini 2=gpt-5.4 3=gpt-5.5/gpt-5.3-codex     │
└───────────────────────────────┬───────────────────────────────────┘
                                ▼
┌─ DECISION (shared) ─ router.js (extended) ───────────────────────┐
│ routeTask(prompt) →                                              │
│   agent (existing keyword match)                                 │
│   baseTier = policy.agentBase[agent]                             │
│   complexity = embeddingScore(prompt) ⊕ keywordEscalators        │
│   tier = clamp(baseTier ± escalators), confidence-gated          │
│         (low confidence ⇒ forbid downgrade)                      │
│   tier = adaptiveAdjust(agent, bucket, tier)   // hysteresis     │
│   model = policy.tierModel[harness][tier]                        │
│ → { agent, tier, model, confidence, reason, escalators }         │
└───────────────────────────────┬───────────────────────────────────┘
                                ▼
┌─ ENFORCE (per-harness) ──────────────────────────────────────────┐
│ CLAUDE: UserPromptSubmit → inject plan (additionalContext)        │
│         PreToolUse(Agent) → strict deny + corrective msg          │
│         PostToolUse(Agent)/Stop → log outcome → adaptive          │
│ CODEX : UserPromptSubmit → inject plan (additionalContext)        │
│         custom agents (.codex) with model baked per agent_type    │
│         spawn_agent MUST pass fork_turns:"none" for model override│
│         (ADVISORY gate — no SubagentStart hook in v0.130.0)        │
│         Stop / PostToolUse → log outcome → adaptive               │
└────────────────────────────────────────────────────────────────────┘
```

**Why subagent-only:** neither harness lets a hook switch the *main session* model mid-turn. The only enforceable lever is the per-subagent model (`Agent({model})` on Claude, `spawn_agent({model, fork_turns:"none"})` on Codex). Hooks at the prompt boundary can only *inject guidance*; the actual `model` is applied when the orchestrator spawns the subagent.

**Enforcement is ASYMMETRIC (verified by spike — see [spike-findings.md](spike-findings.md)):**
- **Claude** = strict: `PreToolUse(Agent)` can `deny` a mismatched-model spawn.
- **Codex (v0.130.0)** = advisory: the installed build dispatches NO `SubagentStart`/`SubagentStop` hook (binary-confirmed event set: PreToolUse, PermissionRequest, PostToolUse, PreCompact, PostCompact, SessionStart, UserPromptSubmit, Stop). So there is no pre-spawn block point. Codex correctness comes from (a) `UserPromptSubmit` inject + (b) **model baked per `agent_type` in custom agents** (correct-by-construction) + (c) `spawn_agent(fork_turns:"none")` for per-call override. A strict pre-spawn gate is deferred behind a future-build feature check.

## Tech Stack

- **Node.js (CommonJS)** — `router.js`, `hook-handler.cjs`, `intelligence.cjs` (existing helpers in `.claude/helpers/`). No new runtime.
- **Bash** — Codex hook entry script (`UserPromptSubmit`) mirroring existing `hooks/*.sh` style.
- **JSON** — `model-policy.json` (config), `.meta.json`. **TOML** — Codex `.codex/config.toml` custom-agent + `[agents]` section.
- **Embeddings** — use `mcp__claude-flow__embeddings_*` (local ONNX `Xenova/all-MiniLM-L6-v2`, 384-dim, cosine) for complexity scoring — **verified offline / no API** (only a one-time HF weight download on a fresh machine; pin/vendor the model). NOTE: `intelligence.cjs` is NOT an embedder (it is trigram-Jaccard + PageRank) — do not use it as the vector source; keyword escalator is the graceful fallback when embeddings are unavailable.
- **Claude Code hooks**: `UserPromptSubmit`, `PreToolUse(Agent)`, `PostToolUse`. stdout on UserPromptSubmit/SessionStart → `additionalContext`.
- **Codex CLI hooks** (v0.130.0, `features.codex_hooks=true`) — binary-confirmed event set: `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `SessionStart`, `UserPromptSubmit`, `Stop`. **No `SubagentStart`/`SubagentStop` in this build.** `UserPromptSubmit` stdout → `additionalContext`. `PreToolUse` output schema DOES support `permissionDecision: deny` (not exit-code-only), but per docs it intercepts Bash/`apply_patch`/MCP calls — **not** subagent spawns.
- **Codex `spawn_agent`** args: `agent_type`, `model`, `reasoning_effort`, `task_name`, `message`, `fork_turns`. Model/agent_type overrides are rejected under default full-history fork → must pass `fork_turns:"none"` (verified against the v0.130.0 binary; matches issue #20077).

## Data model

`model-policy.json` (shared):

```jsonc
{
  "schemaVersion": 1,
  "agentBase": { "tester": 1, "researcher": 1, "coder": 2, "backend-dev": 2,
                 "frontend-dev": 2, "architect": 3, "reviewer": 3, "devops": 2 },
  "escalators": {
    "up":   ["security", "migration", "concurrency", "auth", "refactor large", "architecture"],
    "down": ["rename", "typo", "format", "single-line", "comment"]
  },
  "multiFileUpThreshold": 3,
  "complexity": { "enabled": true, "refSet": "embeddings/complexity-refset.json",
                  "confidenceMin": 0.65, "strictBelowMinFallback": "warn" },
  "tierModel": {
    "claude": { "0": "__direct__", "1": "haiku", "2": "sonnet", "3": "opus" },
    "codex":  { "1": "gpt-5.4-mini", "2": "gpt-5.4", "3": "gpt-5.5" }
  },
  "adaptive": { "enabled": true, "minSamples": 8, "hysteresis": 2 }
}
```

Adaptive store (reuse `intelligence.cjs` backing DB for persistence/PageRank — NOT as an embedder): rows keyed by `(agent, complexityBucket)` → `{ tierChosen, success, retry, escalate, lastBumpAt }`. On Codex, outcome is logged at `Stop`/`PostToolUse` (no `SubagentStop` available).

## API contract

`router.routeTask(prompt, { harness })` returns:

```jsonc
{ "agent": "coder", "tier": 2, "model": "sonnet",
  "confidence": 0.8, "reason": "...", "escalators": ["+security"] }
```

Hook output (UserPromptSubmit, both harnesses) — printed as additionalContext:

```
[ROUTING] agent=coder tier=2 model=sonnet (conf 0.80; +security)
```

PreToolUse(Agent) gate decision: `allow` | `deny(reason)` (Claude). Codex has no pre-spawn gate in v0.130.0 → enforcement is advisory (inject + model-baked custom agents).

## Resolved questions (spike Task 1 — see [spike-findings.md](spike-findings.md))

- **Q1 — RESOLVED (VERIFIED-YES, conditional):** `spawn_agent` honors `model` override under the enabled `multi_agent` (v1), but ONLY with `fork_turns:"none"` (full-history fork otherwise inherits parent model). `multi_agent_v2` is NOT required. → use v1 + `fork_turns:"none"`, and bake model per `agent_type` in custom agents as the robust fallback.
- **Q2 — RESOLVED (VERIFIED-NO):** v0.130.0 ships NO `SubagentStart`/`SubagentStop` hook (binary-confirmed); even the newer docs call `SubagentStart` advisory. → Codex gate is **advisory**; strict pre-spawn block deferred behind a future-build feature check.
- **Q3 — RESOLVED (VERIFIED-YES):** `embeddings_*` runs offline via local ONNX (`Xenova/all-MiniLM-L6-v2`, 384-dim), no API key; only a one-time weight download on a fresh machine. → embeddings **ON** with keyword fallback; pin/vendor the model; do NOT use `intelligence.cjs` as the vector source.

## Open questions

- **Q4:** Scope guard mechanism — self-contained config under `claude-plugins/.claude/` vs. cwd-gating in the `work`-root hook. Lean: self-contained.
- **Residual:** ~2-min manual confirmation of Q1 behavior (live `codex exec` spawn) before Task 7 ships — skipped in spike to avoid using the user's ChatGPT quota.

## V2-deferred: Complexity live-wiring <!-- V2-deferred -->

The embedding-based complexity scorer (`complexity-scorer.cjs`) shells out to the claude-flow CLI per call (~1.4s/embedding × 30 reference prompts on first call). This budget is incompatible with the 5-second hook safety timer in `hook-handler.cjs`.

**Status:** complexity live-wiring in the hook path is controlled by `policy.complexity.liveInHook` (boolean, **default false**). When false (the default), the hook uses keyword-only tier computation (current behavior, no shelling out). When true, `score(prompt)` is called and the resulting bucket (`"simple"` → −1, `"complex"` → +1, `"medium"`/null → 0) nudges the tier before the confidence gate and adaptive adjustment.

**Follow-up:** tracked as Task 9 (perf follow-up). Before enabling `liveInHook`, the embedding pipeline must either (a) be pre-warmed so reference-set embeddings are cached in-process across calls, or (b) be replaced with a lighter scoring backend. The `complexityScore` seam in `computeTierWithPolicy` is fully wired — enabling it is a one-flag change once perf is acceptable.

---

*Generated: 2026-05-26T04:03:06Z*
