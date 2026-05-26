'use strict';

/**
 * model-router.js — Tier computation and harness-aware model mapping.
 *
 * Heuristic: "file-path-like tokens" are whitespace/comma/semicolon-delimited
 * tokens that contain a forward slash OR a dot followed by 2–4 word characters
 * (e.g. foo.js, src/bar, lib/baz.ts). We count distinct such tokens. This is
 * intentionally simple; it may miss unusual paths or false-positive on things
 * like version numbers (1.2.3) — precision beats recall for escalation decisions.
 *
 * Codex has no tier-0 entry ("__direct__" is Claude-only). If harness is "codex"
 * and the computed tier would be 0, it is clamped up to 1.
 */

const FILE_TOKEN_RE = /(?:^|[\s,;|])(\S*(?:\/\S+|\.\w{2,4}))(?=[\s,;|]|$)/g;

/**
 * Count distinct file-path-like tokens in a prompt string.
 *
 * @param {string} prompt
 * @returns {number}
 */
function countFileTokens(prompt) {
  const seen = new Set();
  // Add sentinel spaces so the regex anchors fire at string boundaries
  const padded = ` ${prompt} `;
  let match;
  FILE_TOKEN_RE.lastIndex = 0;
  while ((match = FILE_TOKEN_RE.exec(padded)) !== null) {
    seen.add(match[1]);
    // Regex has a leading boundary char consumed; step back to allow overlapping matches
    FILE_TOKEN_RE.lastIndex = match.index + 1;
  }
  return seen.size;
}

/**
 * Compute tier, escalators, and model for a routing decision.
 *
 * @param {object} opts
 * @param {string}   opts.agent       - Routed agent name (e.g. "coder").
 * @param {number}   opts.confidence  - Routing confidence (0–1).
 * @param {string}   opts.prompt      - Original task prompt.
 * @param {object}   opts.policy      - Loaded policy object (from loadPolicy).
 * @param {string}  [opts.harness]    - Model harness: "claude" (default) or "codex".
 * @param {string|null} [opts.complexityScore] - Complexity bucket from complexity-scorer:
 *   "simple" | "medium" | "complex" | null.
 *   When provided (liveInHook is ON, or passed explicitly in tests), nudges the tier:
 *     "complex" → +1, "simple" → -1, "medium"/null → 0.
 *   Nudge is recorded in escalators and is subject to the same [0,3] clamp.
 *   Also passed as the `bucket` argument to adaptiveAdjust.
 * @param {function} [opts.adaptiveAdjust] - fn(agent, bucket, tier, policyAdaptive) → tier.
 *   Defaults to identity (no-op). Wired from adaptive-store.cjs in the live hook path.
 * @returns {{ tier: number, model: string, escalators: string[] }}
 */
function computeTierWithPolicy({
  agent,
  confidence,
  prompt,
  policy,
  harness = 'claude',
  complexityScore = null,
  adaptiveAdjust = null,
}) {
  const baseTier = Object.prototype.hasOwnProperty.call(policy.agentBase, agent)
    ? policy.agentBase[agent]
    : 2;

  const promptLower = prompt.toLowerCase();
  const escalators = [];
  let delta = 0;

  // Up escalators: any matching keyword → +1 (only once total)
  const upMatch = policy.escalators.up.find(kw => promptLower.includes(kw.toLowerCase()));
  if (upMatch) {
    escalators.push(`+${upMatch}`);
    delta += 1;
  }

  // Multi-file up escalator: distinct file-path tokens ≥ threshold → +1 (stacks with keyword up)
  const fileCount = countFileTokens(prompt);
  if (fileCount >= policy.multiFileUpThreshold) {
    escalators.push('+multifile');
    delta += 1;
  }

  // Down escalators: any matching keyword → -1 (only once total)
  const downMatch = policy.escalators.down.find(kw => promptLower.includes(kw.toLowerCase()));
  if (downMatch) {
    escalators.push(`-${downMatch}`);
    delta -= 1;
  }

  // FIX I-2 step 3: Complexity bucket nudge (+1 for complex, -1 for simple, 0 otherwise).
  // Only applied when a non-null complexityScore is provided (i.e. liveInHook is ON or tests pass it).
  // Nudge is folded into the escalator delta so the confidence gate and clamp apply to the combined delta.
  if (complexityScore === 'complex') {
    escalators.push('+complexity');
    delta += 1;
  } else if (complexityScore === 'simple') {
    escalators.push('-complexity');
    delta -= 1;
  }
  // 'medium' and null are no-ops (no escalator recorded)

  let tier = baseTier + delta;

  // Confidence gate: low confidence (≤ 0.5) forbids any downgrade
  if (confidence <= 0.5) {
    tier = Math.max(tier, baseTier);
  }

  // Clamp to valid range
  tier = Math.max(0, Math.min(3, tier));

  // Adaptive adjustment (identity by default).
  // Signature: adaptiveAdjust(agent, bucket, tier, policyAdaptive) → tier
  // complexityScore carries the bucket string (or null); the store uses it as the (agent,bucket) key.
  if (typeof adaptiveAdjust === 'function') {
    const policyAdaptive = (policy && policy.adaptive) || null;
    tier = Math.max(0, Math.min(3, adaptiveAdjust(agent, complexityScore, tier, policyAdaptive)));
  }

  // Harness-aware model mapping
  // Codex has no tier-0 entry; clamp up to 1 when harness is "codex" and tier is 0.
  // FIX N-1: return the effective (post-clamp) tier so that tier and model are consistent.
  // A consumer reverse-looking-up tierModel.codex[tier] must get the same model.
  let effectiveTier = tier;
  if (harness === 'codex' && effectiveTier === 0) {
    effectiveTier = 1;
  }

  const harnessMap = policy.tierModel[harness] || policy.tierModel['claude'];
  const model = harnessMap[String(effectiveTier)];

  return { tier: effectiveTier, model, escalators };
}

module.exports = { computeTierWithPolicy, countFileTokens };
