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
│         SubagentStart → gate (strict via exit-code, else advisory)│
│         SubagentStop → log outcome → adaptive                     │
└────────────────────────────────────────────────────────────────────┘
```

**Why subagent-only:** neither harness lets a hook switch the *main session* model mid-turn. The only enforceable lever is the per-subagent model (`Agent({model})` on Claude, `spawn_agent({model})` on Codex). Hooks at the prompt boundary can only *inject guidance*; the actual `model` is applied when the orchestrator spawns the subagent.

**Why near-symmetric (not advisory-only on Codex):** Codex CLI v0.130 has `hooks` and `multi_agent` stable, supports `UserPromptSubmit`/`SubagentStart`/`PreToolUse`, and `spawn_agent` exposes a `model` argument. So Codex can do enforced routing comparable to Claude — morkit just hasn't wired it yet (its Codex `hooks.json` currently only has `SessionStart`).

## Tech Stack

- **Node.js (CommonJS)** — `router.js`, `hook-handler.cjs`, `intelligence.cjs` (existing helpers in `.claude/helpers/`). No new runtime.
- **Bash** — Codex hook entry scripts (`SubagentStart`, `UserPromptSubmit`) mirroring existing `hooks/*.sh` style.
- **JSON** — `model-policy.json` (config), `.meta.json`. **TOML** — Codex `.codex/config.toml` custom-agent + `[agents]` section.
- **Embeddings** — reuse `mcp__claude-flow__embeddings_*` (or `intelligence.cjs` vector store) for complexity scoring. ⚠️ Offline/no-API operation is a MUST-VERIFY (see Open questions); keyword escalator is the safety net.
- **Claude Code hooks**: `UserPromptSubmit`, `PreToolUse(Agent)`, `PostToolUse`. stdout on UserPromptSubmit/SessionStart → `additionalContext`.
- **Codex CLI hooks** (v0.130, `features.codex_hooks=true`): events `PreToolUse`, `PostToolUse`, `SessionStart`, `SubagentStart`, `SubagentStop`, `UserPromptSubmit`, `Stop`. `UserPromptSubmit` stdout → `additionalContext`; `PreToolUse` does **not** honor JSON `continue`/`stopReason` (block only via exit-code protocol).
- **Codex `spawn_agent`** args: `agent_type`, `model`, `reasoning_effort`, `task_name`, `message`, `fork_turns`. Model/agent_type overrides are rejected under default full-history fork → must pass `fork_turns:"none"` (issue #20077).

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

Adaptive store (reuse `intelligence.cjs` backing DB): rows keyed by `(agent, complexityBucket)` → `{ tierChosen, success, retry, escalate, lastBumpAt }`.

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

PreToolUse(Agent) gate decision: `allow` | `deny(reason)` (Claude). SubagentStart gate (Codex): exit 0 allow / exit non-zero block (if supported) or `systemMessage` advisory.

## Open questions (MUST-VERIFY — captured as spike tasks)

- **Q1:** Does `multi_agent` v1 (currently enabled) honor a `spawn_agent` `model` override, or is `multi_agent_v2` required? Issue #20077 concerns v2.
- **Q2:** Can a Codex `SubagentStart` hook **block** a spawn via exit-code, or only emit `systemMessage`? If only the latter, the Codex gate degrades to advisory (acceptable per morkit's existing Codex posture).
- **Q3:** Can the embedding complexity scorer run offline (no API cost)? Needs a seeded, labelled reference set (simple/medium/complex). If unavailable, V1 ships with keyword-only complexity and embeddings behind a flag.
- **Q4:** Scope guard mechanism — self-contained config under `claude-plugins/.claude/` vs. cwd-gating in the `work`-root hook. Lean: self-contained.

---

*Generated: 2026-05-26T04:03:06Z*
