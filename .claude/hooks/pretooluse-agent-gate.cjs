#!/usr/bin/env node
'use strict';

/**
 * pretooluse-agent-gate.cjs — PreToolUse hook gate for Agent tool calls.
 *
 * Wired in .claude/settings.json as:
 *   PreToolUse (matcher: Agent) → node pretooluse-agent-gate.cjs
 *
 * Reads Claude Code's PreToolUse stdin JSON, inspects the Agent tool_input
 * for a `model` field, and enforces a MINIMUM-capability floor: the spawned
 * model must be at least as capable as the tier the router computes for the
 * agent call's actual task text (escalators + confidence gate included).
 *
 * Enforcing a floor (not an exact base match) avoids false positives on
 * legitimately-escalated spawns — e.g. a "security" coder task that the
 * router escalates from tier 2 (sonnet) to tier 3 (opus); spawning opus must
 * be ALLOWED even though the coder *base* tier is sonnet. Equal or more
 * capable is always fine (the operator may choose to spend more).
 *
 * Decision rules:
 *   1. model absent → ALLOW (nothing to enforce).
 *   2. spawnedTier >= expectedTier → ALLOW (equal or more capable is fine).
 *   3. spawnedTier < expectedTier AND confidence >= confidenceMin → DENY
 *      with a corrective message naming the expected model/tier.
 *   4. spawnedTier < expectedTier AND confidence < confidenceMin → ALLOW
 *      with a systemMessage warning (per strictBelowMinFallback: "warn").
 *   5. Any internal error / undeterminable tier → ALLOW (fail-open; a buggy
 *      gate must never block legitimate work).
 *
 * Expected tier is computed by running `routeTask` on the agent call's task
 * text (`tool_input.prompt`), which carries the escalator keywords. When that
 * text is unavailable, we fall back to the agent's base tier from the policy.
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
 * Build a reverse map of model-string → tier-int from the claude harness map.
 * E.g. { "__direct__":0, "haiku":1, "sonnet":2, "opus":3 } → reverse lookup.
 *
 * @param {object} policy
 * @returns {Map<string, number>}
 */
function modelToTierMap(policy) {
  const map = new Map();
  const harnessMap = (policy && policy.tierModel && policy.tierModel.claude) || {};
  for (const [tierStr, model] of Object.entries(harnessMap)) {
    const tier = Number(tierStr);
    if (Number.isInteger(tier) && typeof model === 'string') {
      map.set(model, tier);
    }
  }
  return map;
}

/**
 * Compute the expected (minimum) tier the router would assign for an agent's
 * task. Runs the SAME routing computation the router/route-handler uses on the
 * agent call's task text so escalators + the confidence gate are included.
 *
 * Falls back to the agent's base tier from policy.agentBase when the task text
 * is empty (so we still enforce a floor without escalator context).
 *
 * @param {string} subagentType - e.g. "coder", "tester", "architect"
 * @param {string} agentPrompt  - the subagent's task description (may be empty)
 * @param {object} policy       - loaded policy object
 * @returns {{ tier: number, confidence: number, model: string|null } | null}
 *   null when policy is unavailable (gate should fail-open).
 */
function expectedTierForAgent(subagentType, agentPrompt, policy) {
  if (!policy) return null;

  const harnessMap = (policy.tierModel && policy.tierModel.claude) || {};

  // Preferred path: route on the agent call's actual task text. routeTask
  // applies the agent's base tier + escalators + the confidence gate, exactly
  // as the route handler does. We prefix the subagent_type so the pattern
  // matcher resolves to the intended agent even if the task text is terse.
  if (agentPrompt && agentPrompt.trim()) {
    const syntheticPrompt = `${subagentType} task: ${agentPrompt}`;
    const result = routeTask(syntheticPrompt, { harness: 'claude' });
    if (typeof result.tier === 'number') {
      return {
        tier: result.tier,
        confidence: typeof result.confidence === 'number' ? result.confidence : 1.0,
        model: result.model || harnessMap[String(result.tier)] || null,
      };
    }
  }

  // Fallback: base tier for this agent (no escalator context available).
  const baseTier = Object.prototype.hasOwnProperty.call(policy.agentBase, subagentType)
    ? policy.agentBase[subagentType]
    : 2;
  return {
    tier: baseTier,
    confidence: 1.0,
    model: harnessMap[String(baseTier)] || null,
  };
}

/**
 * Compute the gate decision for an Agent tool_input.
 *
 * Enforces a minimum-capability floor: the spawned model must map to a tier
 * >= the tier the router computes for the agent's task. Equal or more capable
 * is allowed. Pure function — side effects limited to routeTask (reads policy).
 * Exported for unit testing.
 *
 * @param {object} toolInput        - The Agent call's tool_input (subagent_type, model, prompt, …)
 * @param {object} opts
 * @param {number} [opts.confidence] - Optional confidence override. When omitted,
 *   the confidence from routing the agent's task text is used.
 * @param {object}  opts.policy     - Loaded policy (may be null → fail-open).
 * @returns {{ action: "allow"|"deny", output: object|null }}
 */
function buildGateDecision(toolInput, opts) {
  try {
    const policy = opts && opts.policy != null ? opts.policy : null;

    // Fail-open: no policy → allow
    if (!policy) {
      return { action: 'allow', output: null };
    }

    const subagentType = toolInput.subagent_type || toolInput.subagentType || '';
    const requestedModel = toolInput.model;
    const agentPrompt = toolInput.prompt || '';

    // Rule 1: no model specified → allow (nothing to enforce)
    if (!requestedModel) {
      return { action: 'allow', output: null };
    }

    // Compute the expected (minimum) tier the router would assign for this task.
    const expected = expectedTierForAgent(subagentType, agentPrompt, policy);

    // Rule 5a: can't determine expected tier → fail-open
    if (!expected || typeof expected.tier !== 'number') {
      return { action: 'allow', output: null };
    }

    // Reverse-lookup the spawned model → tier.
    const spawnedTier = modelToTierMap(policy).get(requestedModel);

    // Rule 5b: spawned model not in the policy table → can't compare → fail-open.
    if (typeof spawnedTier !== 'number') {
      return { action: 'allow', output: null };
    }

    // Rule 2: equal OR more capable than the floor → allow.
    if (spawnedTier >= expected.tier) {
      return { action: 'allow', output: null };
    }

    // Under-powered (spawnedTier < expectedTier). Caller may override confidence
    // (e.g. from a complexity score); otherwise use the routing confidence.
    const confidence = (opts && typeof opts.confidence === 'number')
      ? opts.confidence
      : expected.confidence;

    const confidenceMin = (policy.complexity && typeof policy.complexity.confidenceMin === 'number')
      ? policy.complexity.confidenceMin
      : 0.65;

    const expectedModel = expected.model || `tier ${expected.tier}`;

    if (confidence < confidenceMin) {
      // Rule 4: low confidence → allow with a warning (strictBelowMinFallback: "warn").
      const warning = `[model-routing] Low-confidence routing (${confidence.toFixed(2)} < ${confidenceMin}): ` +
        `requested model "${requestedModel}" (tier ${spawnedTier}) is below policy floor ` +
        `"${expectedModel}" (tier ${expected.tier}) for agent "${subagentType}". Allowing due to low confidence.`;
      return {
        action: 'allow',
        output: { systemMessage: warning },
      };
    }

    // Rule 3: high-confidence under-powered spawn → DENY.
    // Deny contract: https://code.claude.com/docs/en/hooks (verified 2026-05-26)
    const reason = `[model-routing] Agent "${subagentType}" task expects model ≥ "${expectedModel}" ` +
      `(tier ${expected.tier}) but "${requestedModel}" (tier ${spawnedTier}) was requested. ` +
      `Please use model="${expectedModel}" or higher to comply with the routing policy.`;
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
    // Rule 5: any internal error → fail-open
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

  // Load policy. buildGateDecision derives the expected tier AND confidence
  // by routing the agent call's own task text, so we don't pre-compute here.
  let policy = null;
  try {
    policy = loadPolicy();
  } catch (_) { /* fail-open */ }

  const { action, output } = buildGateDecision(toolInput, { policy });

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
