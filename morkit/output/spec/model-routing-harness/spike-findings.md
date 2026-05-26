# Spike Findings — model-routing-harness (Task 1, Q1–Q3)

**Date:** 2026-05-26
**Harness under test:** Codex CLI v0.130.0 (`codex-cli 0.130.0`, Homebrew cask, `/opt/homebrew/bin/codex`)
**Method bias:** Doc- and binary-grounded evidence preferred. Live `codex exec` spawns were deliberately NOT run because the local Codex is logged in with the user's real ChatGPT account (network + quota). Where experiments were safe and offline (embedding generation, MCP schema dump), they were run inside an isolated `CODEX_HOME=$(mktemp -d)` and the temp dir was deleted afterward. The user's real `~/.codex/{config.toml,hooks.json,AGENTS.md}` were verified untouched (mtimes unchanged: config 2026-05-19, hooks/AGENTS 2026-05-18).

---

## Q1 — Does `spawn_agent` honor a `model` override under the enabled `multi_agent` (v1)?

**What I did**
- `codex features list` → `multi_agent` is `stable / true` (enabled); `multi_agent_v2` is `under development / false` (off).
- Dumped the Codex MCP server tool list (`codex mcp-server` over stdio, isolated CODEX_HOME) — only `codex` and `codex-reply` are exposed; `spawn_agent` is an *internal agent-loop tool*, not an MCP tool, so its schema is not externally queryable. It is, however, embedded in the binary.
- Extracted the `spawn_agent` tool definition and the agent-control validation strings from the binary (`strings` on `/opt/homebrew/Caskroom/codex/0.130.0/codex-aarch64-apple-darwin`).

**Evidence (verbatim binary strings)**
- spawn_agent `model` arg exists and overrides are explicitly supported:
  > "Spawned agents inherit your current model by default. Omit `model` to use that preferred default; set `model` only when an explicit override is needed."
- The full-history-fork gotcha — the authoritative runtime guard:
  > "Full-history forked agents inherit the parent agent type, model, and reasoning effort; **omit agent_type, model, and reasoning_effort, or spawn without a full-history fork**"
- The fork parameter and its accepted values:
  > "fork_turns must be `none`, `all`, or a positive integer string"
  > "fork_context is not supported in MultiAgentV2; use fork_turns instead"
- `spawn_agent` is a first-class tool/`ToolCallKind::SpawnAgent` in this build (multi-agent toolset: `spawn_agent`, `send_input`, `wait_agent`, `close_agent`, `list_agents`, `resume_agent`, `spawn_agents_on_csv`).

**Interpretation**
The model override is honored, but ONLY when the spawn is **not** a full-history fork. A default full-history fork forces the worker to inherit the parent's model and *rejects* an explicit `model`/`agent_type`/`reasoning_effort`. To override, pass `fork_turns:"none"` (the current parameter; `fork_context` is the deprecated/v2-rejected name). This matches issue #20077's symptom, and the binary shows the same guard applies in the v0.130.0 build that ships `multi_agent` (v1) as the active stable implementation — i.e. it is **not** exclusive to `multi_agent_v2`.

**Verdict:** VERIFIED-YES (model override works under the enabled `multi_agent`, *conditioned on* `fork_turns:"none"`).
**Confidence:** High for the mechanism (binary-grounded). Medium-high that no separate `multi_agent_v2` enablement is required — I did not run a live spawn to watch the worker's actual model, because that needs the user's ChatGPT session. A 2-minute manual confirmation is recommended before Task 7 ships (see "Residual manual test").

**Recommendation for V1:** Use the currently-enabled `multi_agent` (v1) as-is. On every routed `spawn_agent` call, pass `fork_turns:"none"` together with the policy `model`. As a belt-and-suspenders fallback (and the more robust default), also define Codex **custom agents with the model baked per `agent_type`** (`tierModel.codex`): that way routing works even if a future build changes the per-call override contract, and the per-call `model` override becomes an optimization rather than a hard dependency. Document the `fork_turns:"none"` requirement in `codex-tools.md` (already a Task 7 step).

---

## Q2 — Can a Codex `SubagentStart` hook BLOCK a spawn via exit-code?

**What I did**
- Enumerated the hook events this binary actually dispatches via the embedded JSON Schemas (`*.command.input` / `*.command.output` titles) and the `HookEventNameWire` enum.
- Cross-checked against the official hooks documentation (https://developers.openai.com/codex/hooks).

**Evidence**
- The complete set of hook event schemas compiled into v0.130.0:
  `pre-tool-use`, `permission-request`, `post-tool-use`, `pre-compact`, `post-compact`, `session-start`, `user-prompt-submit`, `stop`.
- `HookEventNameWire` enum (verbatim): `["PreToolUse","PermissionRequest","PostToolUse","PreCompact","PostCompact","SessionStart","UserPromptSubmit","Stop"]`.
- **There is NO `subagent-start` or `subagent-stop` hook in v0.130.0.** (The lone `subagentStart`-looking token in the binary is `subagentStarting`, a UI/event-bus status string, not a hook event.)
- The official docs DO list `SubagentStart` and `SubagentStop`, but: `SubagentStart` is "parsed but ignored / doesn't stop the subagent from starting" (advisory only), and the docs explicitly say PreToolUse intercepts "Bash, file edits through `apply_patch`, and MCP tool calls" — subagent starting is handled by `SubagentStart`, NOT PreToolUse. → The docs describe a build newer than / different from the installed v0.130.0.
- Hook exit-code/block protocol confirmed present in the binary: `"hook exited with code "`, `"hook stopped execution"`, `"hook returned invalid ... hook JSON output"`. Exit code `2` + stderr is the documented blocking signal for the block-capable events.
- `PreToolUse` *can* express a block in v0.130.0 — its output schema defines `decision` (`approve`/`block`) and `hookSpecificOutput.permissionDecision` (`allow`/`deny`/`ask`) plus `permissionDecisionReason`. (Note: this contradicts the design.md aside that PreToolUse "block only via exit-code"; in this build the JSON `permissionDecision:"deny"` path is schema-supported. Behavioral confirmation still advised.)

**Interpretation**
A dedicated `SubagentStart` *gate that blocks a spawn* is **not available** in v0.130.0 — the event does not exist here, and even on the newer build the docs call it advisory. The design's `SubagentStart`/`SubagentStop` enforcement plan (design.md line 54, Task 7 `subagent-start-gate.sh`) rests on events this build does not dispatch.

**Verdict:** VERIFIED-NO for a strict `SubagentStart` exit-code block on v0.130.0 (the event isn't implemented here; on the documented newer build it is advisory).
**Confidence:** High (binary schema is authoritative for what this build fires; docs corroborate the advisory nature).

**Recommendation for V1:** Treat the Codex subagent gate as **ADVISORY**, not strict. Concretely:
1. Do enforcement at the **`UserPromptSubmit`** boundary — inject the `[ROUTING] agent=… tier=… model=…` plan as `additionalContext` (this event exists and supports `additionalContext`). This is the realistic Codex lever and mirrors Claude's inject step.
2. Bake the model into **Codex custom agents per `agent_type`** so the worker's model is correct by construction regardless of any gate (ties into the Q1 fallback).
3. If/when a build exposes a real `SubagentStart` hook, the strict path can be added behind a feature check — do NOT make V1 depend on it.
4. Revise design.md and Task 7: drop the hard dependency on `subagent-start-gate.sh`/`SubagentStop` events for v0.130.0; if a pre-spawn gate is truly needed, prototype it via a `PreToolUse` matcher on the spawn tool (schema-supports `permissionDecision:"deny"`) — but this needs behavioral verification, since the docs say PreToolUse does not fire on subagent spawning.

---

## Q3 — Can embedding-based complexity scoring run OFFLINE (no API/network)?

**What I did**
- Inspected `embeddings_status` (uninitialized → initialized), ran `embeddings_init` then `embeddings_generate` on a real string, and located the on-disk model file.
- Read the existing helper `/Users/haiduong/Documents/work/.claude/helpers/intelligence.cjs`.

**Evidence**
- `mcp__claude-flow__embeddings_*` uses a **local ONNX model**, not a remote API:
  - `embeddings_init` description: "Initialize the ONNX embedding subsystem"; default model `Xenova/all-MiniLM-L6-v2`; capabilities list `onnxModels: ["Xenova/all-MiniLM-L6-v2","Xenova/all-mpnet-base-v2"]`.
  - `embeddings_generate("Refactor the authentication module…")` returned a real **384-dim, L2-normalized** vector (`norm ≈ 1.00000`, geometry `euclidean`). No API key was configured or requested.
  - Config written to `.claude-flow/embeddings.json` with `modelPath` local; the quantized weights are cached on disk at `~/.npm/_npx/<hash>/node_modules/@xenova/transformers/.cache/Xenova/all-MiniLM-L6-v2/onnx/model_quantized.onnx` — the file onnxruntime loads. (A second copy of a MiniLM ONNX exists under `~/.cache/chroma/onnx_models/`.)
- The existing `intelligence.cjs` is **NOT** an embedding scorer at all — it is a fully-offline trigram-Jaccard + PageRank text-similarity engine (`tokenize` → character trigrams → `jaccardSimilarity`, plus `computePageRank`). No vectors, no model, no network. Good as a keyword-style fallback, but it does not produce embeddings.

**One honest caveat (the only network dependency):** `@xenova/transformers` downloads the ONNX weights from HuggingFace on *first* use if not already cached. On this machine the model is already cached, so generation runs offline. A clean checkout on a new machine needs a one-time online model fetch (or the weights vendored into `complexity-refset.json`'s sibling model dir). After that, scoring is fully offline and API-free. Network was online during the test, so "offline" is proven by the presence of the local `.onnx` file + the local-ONNX architecture, not by air-gapping the run.

**Verdict:** VERIFIED-YES — embeddings produce a vector locally via ONNX with no API key and no per-call network (after a one-time model download).
**Confidence:** High for offline per-call operation; the only asterisk is the first-run weight download.

**Recommendation for V1:** Ship with **embeddings ON** for complexity scoring (`complexity.enabled = true`), using `embeddings_*` (Xenova/all-MiniLM-L6-v2, 384-dim, cosine to a seeded `complexity-refset.json`). BUT make it **gracefully degradable**: if `embeddings_status` is uninitialized OR init/generate fails (e.g. weights not yet downloaded on a fresh machine), the scorer must return `null` and the router falls back to the **keyword-escalator path** (the design's safety net, and exactly what Task 4 step 2 already specifies). Do NOT use `intelligence.cjs` as the embedding source — it has no embeddings; it can stay as the adaptive-store/PageRank backing (Task 5) and as a pure-offline keyword similarity option, but the vector scorer (Task 4) should call `embeddings_*`. Recommend vendoring/pinning the model so V1 doesn't silently depend on a network fetch at first run.

---

## Summary table

| Q | Question | Verdict | Confidence | V1 recommendation |
|---|----------|---------|-----------|-------------------|
| Q1 | `spawn_agent` model override under `multi_agent` v1 | VERIFIED-YES (needs `fork_turns:"none"`) | High (mechanism) / Med-high (no v2 needed) | Use v1 + `fork_turns:"none"`; ALSO bake model per `agent_type` in Codex custom agents as the robust fallback |
| Q2 | `SubagentStart` hook can block a spawn via exit-code | VERIFIED-NO (event absent in v0.130.0; advisory even in newer docs) | High | Codex gate = **ADVISORY**: enforce via `UserPromptSubmit` inject + model-baked custom agents; drop hard `SubagentStart`/`SubagentStop` dependency from design/Task 7 |
| Q3 | Embedding complexity scoring offline (no API) | VERIFIED-YES (local ONNX; one-time weight download only) | High | Embeddings **ON** via `embeddings_*`, with keyword-escalator fallback when unavailable; pin/vendor the model; `intelligence.cjs` is NOT an embedding source |

## Impact on downstream tasks
- **Task 4 (embeddings):** Proceed with embeddings on; wire to `embeddings_*` (not `intelligence.cjs`); keep keyword fallback; handle first-run/unavailable as `null`.
- **Task 7 (Codex enforcement):** Re-scope. v0.130.0 has no `SubagentStart`/`SubagentStop` hooks — enforcement is `UserPromptSubmit` inject + per-`agent_type` model-baked custom agents (advisory gate). Keep the `fork_turns:"none"` documentation step. Remove/feature-flag `subagent-start-gate.sh`.
- **design.md:** Update line 54 (it lists `SubagentStart`/`SubagentStop` as available) and the PreToolUse "exit-code only" aside (v0.130.0 also supports `permissionDecision` JSON). The "near-symmetric, not advisory-only on Codex" rationale should soften to "advisory + model-baked" for v0.130.0.

## Residual manual test (recommended, ~2 min, needs the user's Codex session — NOT run here for safety)
In an isolated CODEX_HOME, run a real spawn and confirm the worker's model:
`codex exec --enable multi_agent "Spawn one worker via spawn_agent with model=gpt-5.4-mini and fork_turns=\"none\" to echo its own model name; report which model the worker ran."`
Inspect the session log / worker output to confirm the override took effect (and that omitting `fork_turns:"none"` is rejected). This was skipped only to avoid using the user's ChatGPT quota/network; the binary's own validation strings already make the outcome highly predictable.

## Safety note
- All Codex experiments ran with an isolated `CODEX_HOME=$(mktemp -d /tmp/codex-spike.XXXXXX)`, deleted afterward. The user's real `~/.codex/{config.toml,hooks.json,AGENTS.md}` were verified untouched (mtimes unchanged).
- The `embeddings_init`/`generate` MCP calls wrote only to the embeddings data dir `/Users/haiduong/Documents/work/.claude-flow/{embeddings.json,models}` (normal subsystem state, no config/spec/code files touched). No live LLM/model network calls were made by this spike.
