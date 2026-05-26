# model-routing-harness

## Why

The harness routing in `claude-plugins` currently routes only the **agent type** (`coder`/`tester`/`reviewer`/…) via keyword matching in `.claude/helpers/router.js`, surfaced through the `UserPromptSubmit` hook. It has no concept of **which model** should run a task. Every task therefore runs on whatever model the session was started with — wasting capacity (Opus on a rename) or under-powering hard work (Haiku on a security review). `CLAUDE.md` already documents a "3-Tier Model Routing" intent, but nothing implements it.

This change adds a **model-tier** dimension to the router and enforces it at the **subagent** layer (the only layer the harness allows a hook to influence), so simple work is delegated to cheap/fast models and hard reasoning to capable ones — automatically, on both Claude Code and Codex CLI, scoped to `claude-plugins` only.

## What changes

- `router.js` gains a `modelTier` output (abstract tiers 0–3) alongside the existing `agent`, computed from: agent base map + embedding-based complexity score + keyword escalators + a confidence gate that forbids downgrading low-confidence tasks.
- A shared, editable **policy file** (`model-policy.json`) holds the agent→base-tier map, escalator keywords, embedding thresholds, and the tier→concrete-model map **per harness** (Claude: direct/haiku/sonnet/opus; Codex: gpt-5.4-mini/gpt-5.4/gpt-5.5).
- **Claude Code enforcement:** `UserPromptSubmit` injects a routing plan; a new `PreToolUse(Agent)` gate strict-denies an `Agent` spawn whose `model` deviates from policy (when complexity-confidence is high), returning a corrective message.
- **Codex CLI enforcement:** `UserPromptSubmit` injects the same plan; per-agent models are baked into Codex **custom agents**; `spawn_agent` calls must pass `fork_turns:"none"` for the `model` override to take effect; a `SubagentStart` gate enforces (strict via exit-code if supported, else advisory).
- **Adaptive feedback loop:** outcomes (success / retry / escalate) are logged and used to auto-bump a bucket's base tier with hysteresis, reusing `intelligence.cjs` + model-stats tooling.
- All of the above is **self-contained inside `claude-plugins`** and does not alter the routing already running at the `work` repo root.

## Impact

- **Affected components:** `claude-plugins` copy of `router.js`, hook handler, `.claude/settings.json` (add `Agent` matcher), morkit `hooks.json` (add `UserPromptSubmit`/`SubagentStart`), morkit `.codex` config (custom agents), new `model-policy.json`, embedding reference set, `subagent-driven-development` / `codex-tools.md` guidance.
- **Affected users:** developers running Claude Code or Codex CLI inside `claude-plugins`; cost/latency profile of delegated subagents changes.
- **Migration required:** No — additive. If `model-policy.json` is absent the router falls back to current agent-only behavior.

## Out of scope

- Changing the **main session model** (harness does not allow a hook to switch it — only subagents are routed).
- Modifying routing in the `work` repo root or any project other than `claude-plugins`.
- Cross-provider routing inside claude-flow/agentic-flow internals (Tier C) — not touched.
- A UI/dashboard for routing analytics (telemetry is logged, not visualized).

---

*Generated: 2026-05-26T04:03:06Z*
