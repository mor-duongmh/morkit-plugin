#!/usr/bin/env node
'use strict';

/**
 * hook-handler.cjs — Model-routing hook dispatcher for claude-plugins.
 *
 * Supported commands (via argv[2]):
 *   route          - Read prompt from stdin JSON, call routeTask, print [ROUTING] line.
 *   record-outcome - Persist a routing outcome via adaptive-store.
 *
 * Safety contract:
 *   - 5-second global safety timer (.unref()) prevents hanging Claude Code.
 *   - readStdin() has a 500 ms fallback timer.
 *   - All handlers are wrapped in try/catch; errors are logged to stderr.
 *   - Exit code is always 0 (non-zero blocks subsequent hooks in Claude Code).
 *
 * Exports (for unit testing without spawning subprocesses):
 *   buildRouteOutput(prompt, opts) → string
 *   handleRecordOutcome(inputJson)  → void
 */

const fs = require('node:fs');
const path = require('node:path');

const { routeTask, loadPolicy } = require('./router.js');
const { recordOutcome, adaptiveAdjust: storeAdaptiveAdjust } = require('./adaptive-store.cjs');
const { isClaudePluginsRepo } = require('./scope-guard.cjs');

/**
 * Decision-context cache (FIX I-3).
 *
 * The `route` handler knows the full routing decision (agent, bucket, tier) at
 * the time it fires. The later PostToolUse/Stop outcome event does NOT carry this
 * context — Claude payloads only have tool_input.subagent_type and similar fields.
 *
 * This tiny file-backed cache bridges the gap: `route` writes {agent,bucket,tier,ts}
 * here; `record-outcome` falls back to reading it when the payload lacks those fields.
 *
 * Best-effort only: the cache is last-write-wins (single-agent flow), may be stale
 * in parallel sessions, and is never read if the payload already supplies agent/tier.
 * Never throws — any I/O error is silently swallowed.
 */
const LAST_ROUTING_CACHE = path.join(__dirname, '.last-routing.json');

/** Write {agent, bucket, tier, ts} to the decision cache. Never throws. */
function writeCachedDecision(agent, bucket, tier) {
  try {
    fs.writeFileSync(LAST_ROUTING_CACHE, JSON.stringify({ agent, bucket, tier, ts: Date.now() }), 'utf8');
  } catch (_) {}
}

/** Read last routing decision from cache. Returns null on any error. */
function readCachedDecision() {
  try {
    return JSON.parse(fs.readFileSync(LAST_ROUTING_CACHE, 'utf8'));
  } catch (_) {
    return null;
  }
}

// ── Pure, testable function for the route handler ─────────────────────────────

/**
 * Build the [ROUTING] output line for a given prompt.
 *
 * When the policy loads successfully, emits:
 *   [ROUTING] agent=<agent> tier=<tier> model=<model> (conf <0.00>; <escalators>)
 *
 * When policy is absent (routeTask returns bare shape without tier/model),
 * emits a minimal backward-compatible line:
 *   [ROUTING] agent=<agent> (conf <0.00>)
 *
 * @param {string} prompt - Task prompt.
 * @param {object} [opts]
 * @param {string}   [opts.harness="claude"]      - Model harness.
 * @param {string}   [opts._policyPath]           - Override policy path (for testing).
 * @param {function} [opts._adaptiveAdjust]       - Override adaptiveAdjust fn (for testing).
 * @returns {string} Line suitable for stdout / additionalContext.
 */
function buildRouteOutput(prompt, opts) {
  const harness = (opts && opts.harness) || 'claude';

  // Support injecting a broken policy path to exercise the bare-result path in tests.
  if (opts && opts._policyPath) {
    // Temporarily monkey-patch loadPolicy by providing a custom policyPath.
    // We re-implement the bare routeTask call here to support override.
    const { loadPolicy: lp } = require('./router.js');
    const policy = lp(opts._policyPath);
    if (!policy) {
      // Policy null → use bare routeTask result (no tier/model)
      const result = routeTask(prompt);  // returns bare {agent,confidence,reason}
      const conf = result.confidence.toFixed(2);
      return `[ROUTING] agent=${result.agent} (conf ${conf})`;
    }
  }

  // FIX I-1: wire adaptiveAdjust from adaptive-store so accumulated outcomes influence tier.
  // Injectable via opts._adaptiveAdjust for tests; defaults to the real store function.
  const adaptiveAdjustFn = (opts && typeof opts._adaptiveAdjust === 'function')
    ? opts._adaptiveAdjust
    : storeAdaptiveAdjust;

  // FIX I-2: complexity live-wiring is DEFERRED behind policy.complexity.liveInHook (default false).
  // Only call score() when liveInHook === true; otherwise keyword-only path (current behavior).
  let complexityScore = null;
  try {
    const policy = loadPolicy();
    if (policy && policy.complexity && policy.complexity.liveInHook === true) {
      const { score } = require('./complexity-scorer.cjs');
      const scored = score(prompt);
      if (scored) complexityScore = scored.bucket;
    }
  } catch (_) {
    // score() failing must never block routing — stay on keyword-only path
  }

  const routeOpts = { harness, adaptiveAdjust: adaptiveAdjustFn, complexityScore };

  let result;
  try {
    result = routeTask(prompt, routeOpts);
  } catch (_) {
    return '[ROUTING] agent=coder (conf 0.50)';
  }

  // Enriched shape (policy loaded)
  if (typeof result.tier === 'number' && typeof result.model === 'string') {
    const conf = result.confidence.toFixed(2);
    const escPart = result.escalators && result.escalators.length > 0
      ? `; ${result.escalators.join(' ')}`
      : '';

    // FIX I-3: cache the routing decision so record-outcome can fall back to it
    // when the PostToolUse/Stop payload lacks agent/bucket/tier context.
    writeCachedDecision(result.agent, complexityScore, result.tier);

    return `[ROUTING] agent=${result.agent} tier=${result.tier} model=${result.model} (conf ${conf}${escPart})`;
  }

  // Bare shape (policy null at runtime)
  const conf = result.confidence.toFixed(2);
  return `[ROUTING] agent=${result.agent} (conf ${conf})`;
}

// ── record-outcome handler ────────────────────────────────────────────────────

/**
 * Handle a "record-outcome" event from stdin JSON.
 *
 * FIX I-2: Agent is read from data.agent OR data.tool_input.subagent_type
 * (real Claude PostToolUse payloads carry the agent name in tool_input.subagent_type).
 *
 * FIX I-3: When the payload lacks agent/bucket/tier, fall back to the decision cache
 * written by the most-recent `route` invocation. This is best-effort only — the cache
 * is last-write-wins and may be stale in concurrent sessions.
 *
 * @param {string} inputJson - Raw JSON string from the hook invocation.
 * @returns {void}
 */
function handleRecordOutcome(inputJson) {
  try {
    const data = JSON.parse(inputJson);

    // FIX I-2: resolve agent from direct field or from Claude PostToolUse tool_input
    const toolInput = data.tool_input || data.toolInput || {};
    let agent = typeof data.agent === 'string' ? data.agent : null;
    if (!agent && typeof toolInput.subagent_type === 'string') {
      agent = toolInput.subagent_type;
    }

    let bucket = typeof data.bucket === 'string' ? data.bucket : null;
    let tier = typeof data.tier === 'number' ? data.tier : null;

    // FIX I-3: fall back to cached decision when payload lacks agent/bucket/tier.
    // Best-effort: never throw, treat stale/missing cache as if absent.
    if (!agent || tier === null) {
      const cached = readCachedDecision();
      if (cached) {
        if (!agent && typeof cached.agent === 'string') agent = cached.agent;
        if (bucket === null && (cached.bucket !== undefined)) bucket = cached.bucket;
        if (tier === null && typeof cached.tier === 'number') tier = cached.tier;
      }
    }

    const outcome = typeof data.outcome === 'string' ? data.outcome : 'success';
    const statePath = typeof data.statePath === 'string' ? data.statePath : undefined;

    // Ignore events with no agent (malformed input, cache also absent)
    if (!agent) return;

    // Use tier=2 as a safe default if still unknown after cache fallback
    recordOutcome(agent, bucket, tier !== null ? tier : 2, outcome, statePath);
  } catch (_) {
    // Never throw — hook handlers must always exit cleanly
  }
}

// ── stdin reader ──────────────────────────────────────────────────────────────

/**
 * Read stdin with a 500 ms fallback timer.
 * Returns '' immediately when stdin is a TTY.
 *
 * @returns {Promise<string>}
 */
function readStdin() {
  if (process.stdin.isTTY) return Promise.resolve('');
  return new Promise((resolve) => {
    let data = '';
    const timer = setTimeout(() => {
      process.stdin.removeAllListeners();
      process.stdin.pause();
      resolve(data);
    }, 500);
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => { clearTimeout(timer); resolve(data); });
    process.stdin.on('error', () => { clearTimeout(timer); resolve(data); });
    process.stdin.resume();
  });
}

// ── Main dispatcher (only runs when executed directly) ────────────────────────

async function main() {
  // Global safety timer — hooks must NEVER hang.
  const safetyTimer = setTimeout(() => {
    process.stderr.write('[WARN] hook-handler: global timeout (5s), forcing exit\n');
    process.exit(0);
  }, 5000);
  safetyTimer.unref();

  let stdinData = '';
  try { stdinData = await readStdin(); } catch (_) { /* ignore */ }

  let hookInput = {};
  if (stdinData.trim()) {
    try { hookInput = JSON.parse(stdinData); } catch (_) { /* ignore */ }
  }

  // Normalize snake_case / camelCase (Claude Code sends tool_input, tool_name)
  const toolInput = hookInput.toolInput || hookInput.tool_input || {};
  const _toolName = hookInput.toolName || hookInput.tool_name || '';  // reserved

  // Resolve prompt: prefer stdin JSON fields, then argv tail
  const args = process.argv.slice(3);  // argv[2] is the command
  const prompt = hookInput.prompt || hookInput.command || toolInput.command
    || args.join(' ') || '';

  const command = process.argv[2] || '';

  // Scope guard: this hook is only active within the claude-plugins repo.
  // When the guard returns false, silently exit 0 (noop) — never block other projects.
  // Any error in the guard → noop (fail-open-to-noop is the contract).
  try {
    if (!isClaudePluginsRepo()) {
      process.exit(0);
    }
  } catch (_) {
    process.exit(0);
  }

  const handlers = {
    route: () => {
      // Accept --harness <value> from argv OR a `harness` field in stdin JSON.
      // Defaults to 'claude' so existing Claude Code behavior is unchanged.
      let harness = hookInput.harness || 'claude';
      const harnessIdx = args.indexOf('--harness');
      if (harnessIdx !== -1 && args[harnessIdx + 1]) {
        harness = args[harnessIdx + 1];
      }
      const line = buildRouteOutput(prompt, { harness });
      process.stdout.write(line + '\n');
    },

    'record-outcome': () => {
      handleRecordOutcome(stdinData);
    },
  };

  if (command && handlers[command]) {
    try {
      await Promise.resolve(handlers[command]());
    } catch (e) {
      process.stderr.write(`[WARN] hook-handler: ${command} error: ${e.message}\n`);
    }
  } else if (command) {
    // Unknown command — pass through without error (future compatibility)
    process.stdout.write(`[OK] hook-handler: unknown command "${command}"\n`);
  } else {
    process.stdout.write('Usage: hook-handler.cjs <route|record-outcome>\n');
  }
}

// Only run main() when executed directly (not when required for testing)
if (require.main === module) {
  process.exitCode = 0;
  main().catch((e) => {
    try { process.stderr.write(`[WARN] hook-handler: ${e.message}\n`); } catch (_) {}
  }).finally(() => {
    process.exit(0);
  });
}

module.exports = {
  buildRouteOutput,
  handleRecordOutcome,
  'record-outcome': handleRecordOutcome,
};
