'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const { computeTier, routeTask } = require('./router.js');

const VALID_POLICY_PATH = path.join(__dirname, 'model-policy.json');

// ── Test 1: agentBase tier defaults ──────────────────────────────────────────
// coder → base tier 2, tester → base tier 1, architect → base tier 3
test('computeTier returns correct base tier for known agents (no escalators)', () => {
  // coder → agentBase[coder] = 2
  const coder = computeTier({ agent: 'coder', confidence: 0.8, prompt: 'implement feature' });
  assert.equal(coder.tier, 2, 'coder base tier must be 2');
  assert.deepEqual(coder.escalators, [], 'no escalators should fire for a plain coder prompt');

  // tester → agentBase[tester] = 1
  const tester = computeTier({ agent: 'tester', confidence: 0.8, prompt: 'write some tests' });
  assert.equal(tester.tier, 1, 'tester base tier must be 1');

  // architect → agentBase[architect] = 3
  const architect = computeTier({ agent: 'architect', confidence: 0.8, prompt: 'plan the system' });
  assert.equal(architect.tier, 3, 'architect base tier must be 3');
});

// ── Test 2: escalators and clamping ──────────────────────────────────────────
// "security" / "migration" bumps +1; "rename" / "typo" bumps -1; clamp 0–3
test('computeTier applies escalators and clamps tier to [0, 3]', () => {
  // coder (base 2) + "security" keyword → tier 3
  const up = computeTier({ agent: 'coder', confidence: 0.8, prompt: 'security review of auth module' });
  assert.equal(up.tier, 3, 'security keyword should bump coder from 2 to 3');
  assert.ok(up.escalators.some(e => e.startsWith('+')), 'escalators must contain a + entry');

  // tester (base 1) + "rename" keyword → tier 0 (clamped)
  const down = computeTier({ agent: 'tester', confidence: 0.8, prompt: 'rename the test helper variable' });
  assert.equal(down.tier, 0, 'rename keyword should bump tester from 1 to 0');
  assert.ok(down.escalators.some(e => e.startsWith('-')), 'escalators must contain a - entry');

  // architect (base 3) + "security" → would be 4, clamped to 3
  const clampUp = computeTier({ agent: 'architect', confidence: 0.8, prompt: 'security architecture design' });
  assert.equal(clampUp.tier, 3, 'tier must be clamped at 3 (not 4)');

  // researcher (base 1) + "rename" → would be 0, clamped to 0
  const clampDown = computeTier({ agent: 'researcher', confidence: 0.8, prompt: 'rename and typo fixes' });
  assert.equal(clampDown.tier, 0, 'tier must be clamped at 0 (not negative)');

  // ≥3 file-path-like tokens → multifile escalator fires
  const multifile = computeTier({
    agent: 'coder',
    confidence: 0.8,
    prompt: 'update src/foo.js, src/bar.js, and lib/baz.ts',
  });
  assert.equal(multifile.tier, 3, 'three file references should bump coder from 2 to 3');
  assert.ok(
    multifile.escalators.some(e => e === '+multifile'),
    'escalators must include "+multifile" for multi-file prompt',
  );
});

// ── Test 3: low-confidence confidence gate forbids downgrade ──────────────────
// confidence ≤ 0.5 → tier must NOT go below baseTier
test('computeTier forbids downgrade when confidence is at or below 0.5', () => {
  // tester (base 1) + "rename" would push to 0; but confidence=0.5 → tier stays at 1
  const result = computeTier({
    agent: 'tester',
    confidence: 0.5,
    prompt: 'rename the variable',
  });
  assert.equal(result.tier, 1, 'low confidence must prevent downgrade: tier should stay at baseTier 1');
  // escalator for "rename" should still be recorded
  assert.ok(result.escalators.some(e => e.startsWith('-')), 'escalator must still be recorded even when gate prevents downgrade');

  // coder (base 2) + "rename" + confidence=0.5 → tier stays at 2
  const coder = computeTier({ agent: 'coder', confidence: 0.5, prompt: 'rename method' });
  assert.equal(coder.tier, 2, 'low-confidence coder with rename must not go below baseTier 2');

  // high confidence should still allow downgrade
  const highConf = computeTier({ agent: 'tester', confidence: 0.8, prompt: 'rename the variable' });
  assert.equal(highConf.tier, 0, 'high confidence must allow downgrade to 0');
});

// ── Test 4: routeTask(prompt, {harness}) returns enriched shape ───────────────
// Returns {agent, tier, model, confidence, reason, escalators}
// model comes from policy.tierModel[harness][tier]
test('routeTask with harness option returns enriched shape with model from policy', () => {
  // claude harness (default)
  const claude = routeTask('implement a new feature', { harness: 'claude' });
  assert.equal(typeof claude.agent, 'string', 'agent must be a string');
  assert.equal(typeof claude.tier, 'number', 'tier must be a number');
  assert.equal(typeof claude.model, 'string', 'model must be a string');
  assert.equal(typeof claude.confidence, 'number', 'confidence must be a number');
  assert.equal(typeof claude.reason, 'string', 'reason must be a string');
  assert.ok(Array.isArray(claude.escalators), 'escalators must be an array');
  // "implement" → coder (tier 2, model "sonnet" for claude)
  assert.equal(claude.model, 'sonnet', 'coder tier 2 on claude harness must map to "sonnet"');

  // codex harness
  const codex = routeTask('implement a new feature', { harness: 'codex' });
  assert.equal(codex.model, 'gpt-5.4', 'coder tier 2 on codex harness must map to "gpt-5.4"');

  // codex tier 0 → should clamp up to 1 (codex has no tier 0)
  // tester base=1, "rename" → would drop to 0; but codex: clamp to 1
  const codexLow = routeTask('rename the variable', { harness: 'codex' });
  // tester (base=1) + rename (-1) = 0 → codex clamps to 1
  // but this only applies if the routed agent is tester; "rename" may not route to tester
  // so we set confidence explicitly via a prompt that routes to tester
  const codexTester = routeTask('write tests and rename variables', { harness: 'codex' });
  // "test" pattern → tester (base=1); "rename" → -1 → tier 0 → codex clamps to 1
  assert.equal(typeof codexTester.model, 'string', 'codex tester must return a string model');
  assert.notEqual(codexTester.model, undefined, 'codex must never produce undefined model');

  // no harness (default = "claude") — backward compat: must still have agent/confidence/reason
  const noOpts = routeTask('implement a feature');
  assert.equal(typeof noOpts.agent, 'string', 'agent must be present without opts');
  assert.equal(typeof noOpts.confidence, 'number', 'confidence must be present without opts');
  assert.equal(typeof noOpts.reason, 'string', 'reason must be present without opts');
  // enriched fields when policy loads successfully
  assert.equal(typeof noOpts.tier, 'number', 'tier must be present when policy is available');
  assert.equal(typeof noOpts.model, 'string', 'model must be present when policy is available');
});

// ── Test 5 (FIX N-1): codex tier-0 case — tier and model are consistent ─────
// When harness=codex and logical tier would be 0, it is clamped to 1.
// The returned {tier, model} must correspond: tier===1 and model==="gpt-5.4-mini".
test('FIX N-1: codex tier-0 clamp returns consistent {tier, model} (both at tier 1)', () => {
  const { computeTierWithPolicy } = require('./model-router.js');
  const { loadPolicy } = require('./router.js');
  const policy = loadPolicy();
  assert.ok(policy, 'policy must be loadable for this test');

  // tester (base=1) + "rename" (-1) = 0 → codex clamps to 1
  const result = computeTierWithPolicy({
    agent: 'tester',
    confidence: 0.8,     // high confidence allows downgrade
    prompt: 'rename the helper variable',
    policy,
    harness: 'codex',
  });

  assert.equal(result.tier, 1, 'FIX N-1: codex tier must be the effective (post-clamp) tier 1, not 0');
  assert.equal(result.model, 'gpt-5.4-mini', 'FIX N-1: codex tier-1 must map to gpt-5.4-mini');
  // Verify consistency: policy.tierModel.codex[tier] === model
  assert.equal(
    policy.tierModel.codex[String(result.tier)],
    result.model,
    'tier and model must be consistent: policy.tierModel.codex[tier] must equal result.model',
  );
});

// ── Test 6 (A1): liveInHook ON by default; confident prompts are NOT scored ─────
// liveInHook is now ON, but the hook gates scoring to uncertain prompts. A prompt
// that matches a keyword pattern (confidence 0.8) must NOT trigger an embedding,
// so no complexity escalator appears on the keyword-only path.
test('A1: confident keyword-matched prompt is not scored even with liveInHook ON', () => {
  const policy = JSON.parse(require('node:fs').readFileSync(VALID_POLICY_PATH, 'utf8'));
  // liveInHook is now ON by default (A1 decision).
  assert.equal(
    policy.complexity && policy.complexity.liveInHook, true,
    `complexity.liveInHook must be true (A1 default on); got: ${policy.complexity && policy.complexity.liveInHook}`,
  );

  // "implement a feature" matches the coder pattern → confidence 0.8 (≥ embed threshold),
  // so the hook stays on the keyword-only path and never embeds.
  const { buildRouteOutput } = require('./hook-handler.cjs');
  const output = buildRouteOutput('implement a feature', { harness: 'claude' });
  assert.ok(output.includes('[ROUTING]'), 'must produce [ROUTING] line on keyword-only path');
  assert.ok(output.includes('tier='), 'must include tier= on the keyword-only path');
  // No +complexity / -complexity escalator: a confident prompt is never scored.
  assert.ok(!output.includes('+complexity'), 'must NOT include +complexity escalator on a confident prompt');
  assert.ok(!output.includes('-complexity'), 'must NOT include -complexity escalator on a confident prompt');
});

// ── Test 7 (FIX I-2): complexityScore nudges tier — complex +1, simple -1 ────
// computeTierWithPolicy must apply a ±1 nudge when complexityScore is provided.
test('FIX I-2: complexityScore nudges tier (+1 for complex, -1 for simple, 0 for medium)', () => {
  const { computeTierWithPolicy } = require('./model-router.js');
  const { loadPolicy } = require('./router.js');
  const policy = loadPolicy();
  assert.ok(policy, 'policy must be loadable');

  // coder base tier=2; no keyword escalators in a plain prompt
  const base = computeTierWithPolicy({ agent: 'coder', confidence: 0.8, prompt: 'implement', policy });
  assert.equal(base.tier, 2, 'baseline coder tier must be 2');

  // complex → +1 → tier 3
  const complex = computeTierWithPolicy({
    agent: 'coder', confidence: 0.8, prompt: 'implement', policy, complexityScore: 'complex',
  });
  assert.equal(complex.tier, 3, 'complex bucket must nudge tier from 2 to 3');
  assert.ok(complex.escalators.includes('+complexity'), 'escalators must include +complexity');

  // simple → -1 → tier 1
  const simple = computeTierWithPolicy({
    agent: 'coder', confidence: 0.8, prompt: 'implement', policy, complexityScore: 'simple',
  });
  assert.equal(simple.tier, 1, 'simple bucket must nudge tier from 2 to 1');
  assert.ok(simple.escalators.includes('-complexity'), 'escalators must include -complexity');

  // simple with low confidence (≤0.5) → confidence gate prevents downgrade → stays at 2
  const simpleLowConf = computeTierWithPolicy({
    agent: 'coder', confidence: 0.5, prompt: 'implement', policy, complexityScore: 'simple',
  });
  assert.equal(
    simpleLowConf.tier, 2,
    'simple bucket with low confidence must not downgrade (confidence gate); got ' + simpleLowConf.tier,
  );

  // medium → 0 (no change)
  const medium = computeTierWithPolicy({
    agent: 'coder', confidence: 0.8, prompt: 'implement', policy, complexityScore: 'medium',
  });
  assert.equal(medium.tier, 2, 'medium bucket must not change tier');
  assert.ok(!medium.escalators.includes('+complexity'), 'medium must not add +complexity');
  assert.ok(!medium.escalators.includes('-complexity'), 'medium must not add -complexity');

  // null → 0 (no change, same as medium)
  const nullScore = computeTierWithPolicy({
    agent: 'coder', confidence: 0.8, prompt: 'implement', policy, complexityScore: null,
  });
  assert.equal(nullScore.tier, 2, 'null complexityScore must not change tier');
});
