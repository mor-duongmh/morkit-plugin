#!/usr/bin/env node
'use strict';

/**
 * pretooluse-agent-gate.cjs — PreToolUse hook gate for Agent tool calls.
 *
 * Wired in .claude/settings.json as:
 *   PreToolUse (matcher: Agent) → node pretooluse-agent-gate.cjs
 *
 * Reads Claude Code's PreToolUse stdin JSON, inspects the Agent tool_input
 * for a `model` field, and compares it against the policy-expected model for
 * the given `subagent_type`.
 *
 * Decision rules:
 *   1. model absent or matches expected → ALLOW (no output needed).
 *   2. model MISMATCHES expected AND confidence >= confidenceMin → DENY
 *      with corrective message naming the expected model.
 *   3. model MISMATCHES expected AND confidence < confidenceMin → ALLOW
 *      with optional systemMessage warning (per strictBelowMinFallback: "warn").
 *   4. Any internal error → ALLOW (fail-open; a buggy gate must never
 *      block legitimate work).
 *
 * PreToolUse deny contract (verified from Claude Code hooks docs,
 * https://code.claude.com/docs/en/hooks, 2026-05-26):
 *   stdout: { "hookSpecificOutput": { "hookEventName": "PreToolUse",
 *             "permissionDecision": "deny",
 *             "permissionDecisionReason": "<msg>" } }
 *   exit code: 0
 *
 * Exports `buildGateDecision` for unit testing without subprocess spawning.
 */

const path = require('node:path');
const { routeTask, loadPolicy } = require(path.join(__dirname, '../helpers/router.js'));

/**
 * Compute the expected policy model for a given subagent_type.
 *
 * Uses routeTask to mirror the same agent-detection + tier-computation logic
 * that the route handler uses. The subagent_type is used as the prompt prefix
 * so the pattern matcher can identify the correct agent.
 *
 * Returns null when policy is unavailable (gate should fail-open).
 *
 * @param {string} subagentType - e.g. "coder", "tester", "architect"
 * @param {string} prompt       - original task prompt (may be empty)
 * @param {object} policy       - loaded policy object
 * @returns {string|null}       - expected model string or null
 */
function expectedModelForSubagent(subagentType, prompt, policy) {
  if (!policy) return null;

  // Build a synthetic prompt that will route to the correct agent.
  // Prefer the original prompt if it already routes to the right agent;
  // otherwise prepend the subagent_type keyword so the pattern fires.
  const syntheticPrompt = `${subagentType} task: ${prompt || 'task'}`;
  const result = routeTask(syntheticPrompt, { harness: 'claude' });

  // If the routed agent does not match, force via agentBase directly.
  // We compute tier using the policy's agentBase for this subagentType.
  const agentForType = result.agent === subagentType ? result.agent : subagentType;

  // Compute the base tier for this agent from policy
  const baseTier = Object.prototype.hasOwnProperty.call(policy.agentBase, agentForType)
    ? policy.agentBase[agentForType]
    : 2;

  const harnessMap = policy.tierModel['claude'] || {};
  const model = harnessMap[String(baseTier)];
  return model || null;
}

/**
 * Compute the gate decision for an Agent tool_input.
 *
 * Pure function — no side effects except routeTask (which reads the policy file).
 * Exported for unit testing.
 *
 * @param {object} toolInput        - The Agent call's tool_input (subagent_type, model, prompt, …)
 * @param {object} opts
 * @param {number}  opts.confidence - Routing confidence (0–1). If unknown, pass 1.0 to be strict.
 * @param {object}  opts.policy     - Loaded policy (may be null → fail-open).
 * @returns {{ action: "allow"|"deny", output: object|null }}
 */
function buildGateDecision(toolInput, opts) {
  try {
    const policy = opts && opts.policy != null ? opts.policy : null;
    const confidence = (opts && typeof opts.confidence === 'number') ? opts.confidence : 1.0;

    // Fail-open: no policy → allow
    if (!policy) {
      return { action: 'allow', output: null };
    }

    const subagentType = toolInput.subagent_type || toolInput.subagentType || '';
    const requestedModel = toolInput.model;
    const prompt = toolInput.prompt || '';

    // Rule 1: no model specified → allow (nothing to enforce)
    if (!requestedModel) {
      return { action: 'allow', output: null };
    }

    const expectedModel = expectedModelForSubagent(subagentType, prompt, policy);

    // Rule 1b: can't determine expected model → fail-open
    if (!expectedModel) {
      return { action: 'allow', output: null };
    }

    // Rule 1c: model matches → allow
    if (requestedModel === expectedModel) {
      return { action: 'allow', output: null };
    }

    // Model MISMATCHES — check confidence
    const confidenceMin = (policy.complexity && typeof policy.complexity.confidenceMin === 'number')
      ? policy.complexity.confidenceMin
      : 0.65;

    if (confidence < confidenceMin) {
      // Rule 3: low confidence → allow with optional warning
      const warning = `[model-routing] Low-confidence routing (${confidence.toFixed(2)} < ${confidenceMin}): ` +
        `requested model "${requestedModel}" differs from policy model "${expectedModel}" ` +
        `for agent "${subagentType}". Allowing due to low confidence.`;
      return {
        action: 'allow',
        output: { systemMessage: warning },
      };
    }

    // Rule 2: high confidence mismatch → DENY
    // Deny contract: https://code.claude.com/docs/en/hooks (verified 2026-05-26)
    const reason = `[model-routing] Agent "${subagentType}" policy requires model "${expectedModel}" ` +
      `but "${requestedModel}" was requested. ` +
      `Please use model="${expectedModel}" to comply with the routing policy.`;
    return {
      action: 'deny',
      output: {
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason: reason,
        },
      },
    };
  } catch (_) {
    // Rule 4: any internal error → fail-open
    return { action: 'allow', output: null };
  }
}

// ── stdin reader ──────────────────────────────────────────────────────────────

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

// ── Main (only runs when executed directly) ───────────────────────────────────

async function main() {
  // Global safety timer
  const safetyTimer = setTimeout(() => {
    process.stderr.write('[WARN] pretooluse-agent-gate: global timeout (5s), forcing exit\n');
    process.exit(0);
  }, 5000);
  safetyTimer.unref();

  let stdinData = '';
  try { stdinData = await readStdin(); } catch (_) { /* ignore */ }

  let hookInput = {};
  if (stdinData.trim()) {
    try { hookInput = JSON.parse(stdinData); } catch (_) { /* ignore parse errors */ }
  }

  // Normalize snake_case / camelCase
  const toolInput = hookInput.toolInput || hookInput.tool_input || {};

  // Load policy and derive confidence from a quick routeTask call on the prompt
  let policy = null;
  let confidence = 1.0;
  try {
    policy = loadPolicy();
    const prompt = toolInput.prompt || hookInput.prompt || '';
    if (prompt && policy) {
      const result = routeTask(prompt, { harness: 'claude' });
      if (typeof result.confidence === 'number') {
        confidence = result.confidence;
      }
    }
  } catch (_) { /* fail-open */ }

  const { action, output } = buildGateDecision(toolInput, { confidence, policy });

  if (action === 'deny' && output) {
    process.stdout.write(JSON.stringify(output) + '\n');
  } else if (action === 'allow' && output && output.systemMessage) {
    process.stdout.write(JSON.stringify(output) + '\n');
  }
  // allow with no output → write nothing (Claude Code interprets empty stdout as allow)
}

if (require.main === module) {
  process.exitCode = 0;
  main().catch((e) => {
    try { process.stderr.write(`[WARN] pretooluse-agent-gate: ${e.message}\n`); } catch (_) {}
  }).finally(() => {
    process.exit(0);
  });
}

module.exports = { buildGateDecision };
