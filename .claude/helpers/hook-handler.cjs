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

const { routeTask, loadPolicy } = require('./router.js');
const { recordOutcome } = require('./adaptive-store.cjs');

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
 * @param {string}  [opts.harness="claude"] - Model harness.
 * @param {string}  [opts._policyPath]      - Override policy path (for testing).
 * @returns {string} Line suitable for stdout / additionalContext.
 */
function buildRouteOutput(prompt, opts) {
  const harness = (opts && opts.harness) || 'claude';

  // Support injecting a broken policy path to exercise the bare-result path in tests.
  const routeOpts = { harness };
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
 * @param {string} inputJson - Raw JSON string from the hook invocation.
 * @returns {void}
 */
function handleRecordOutcome(inputJson) {
  try {
    const data = JSON.parse(inputJson);

    const agent = typeof data.agent === 'string' ? data.agent : null;
    const bucket = typeof data.bucket === 'string' ? data.bucket : null;
    const tier = typeof data.tier === 'number' ? data.tier : 2;
    const outcome = typeof data.outcome === 'string' ? data.outcome : 'success';
    const statePath = typeof data.statePath === 'string' ? data.statePath : undefined;

    // Ignore events with no agent (malformed input)
    if (!agent) return;

    recordOutcome(agent, bucket, tier, outcome, statePath);
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

  const handlers = {
    route: () => {
      const line = buildRouteOutput(prompt, { harness: 'claude' });
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
