'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

// Each test uses a fresh temp file to avoid state bleed
function tmpPath() {
  return path.join(os.tmpdir(), `adaptive-test-${Date.now()}-${Math.random().toString(36).slice(2)}.json`);
}

const { recordOutcome, adaptiveAdjust } = require('./adaptive-store.cjs');

const POLICY = { enabled: true, minSamples: 8, hysteresis: 2 };

// ── Test 1: recordOutcome persists rows keyed by (agent, bucket) ──────────────
test('recordOutcome persists rows keyed by (agent, bucket)', () => {
  const statePath = tmpPath();
  try {
    recordOutcome('coder', 'simple', 2, 'success', statePath);
    recordOutcome('coder', 'simple', 2, 'retry', statePath);
    recordOutcome('coder', 'complex', 3, 'success', statePath);
    recordOutcome('tester', 'simple', 1, 'escalate', statePath);

    const raw = JSON.parse(fs.readFileSync(statePath, 'utf8'));

    // Key for coder+simple
    assert.ok('coder:simple' in raw, 'coder:simple key must exist');
    const cs = raw['coder:simple'];
    assert.equal(cs.success, 1, 'coder:simple success count must be 1');
    assert.equal(cs.retry, 1, 'coder:simple retry count must be 1');
    assert.equal(cs.escalate, 0, 'coder:simple escalate count must be 0');

    // Key for coder+complex
    assert.ok('coder:complex' in raw, 'coder:complex key must exist');
    const cc = raw['coder:complex'];
    assert.equal(cc.success, 1, 'coder:complex success must be 1');

    // Key for tester+simple
    assert.ok('tester:simple' in raw, 'tester:simple key must exist');
    assert.equal(raw['tester:simple'].escalate, 1, 'tester:simple escalate must be 1');
  } finally {
    try { fs.unlinkSync(statePath); } catch (_) {}
  }
});

// ── Test 2: adaptiveAdjust bumps tier +1 after ≥minSamples dominated by retry/escalate ──
test('adaptiveAdjust bumps tier +1 when ≥minSamples dominated by retry/escalate', () => {
  const statePath = tmpPath();
  try {
    // Record 8 retry outcomes for coder:medium (hits minSamples=8)
    for (let i = 0; i < 8; i++) {
      recordOutcome('coder', 'medium', 2, 'retry', statePath);
    }

    const adjusted = adaptiveAdjust('coder', 'medium', 2, POLICY, statePath);
    assert.equal(adjusted, 3, 'tier must bump from 2 to 3 after ≥minSamples retries');
  } finally {
    try { fs.unlinkSync(statePath); } catch (_) {}
  }
});

// ── Test 3: adaptiveAdjust does NOT bump when total < minSamples ──────────────
test('adaptiveAdjust does not bump tier when observations < minSamples', () => {
  const statePath = tmpPath();
  try {
    for (let i = 0; i < 7; i++) {
      recordOutcome('coder', 'medium', 2, 'retry', statePath);
    }

    const adjusted = adaptiveAdjust('coder', 'medium', 2, POLICY, statePath);
    assert.equal(adjusted, 2, 'tier must NOT bump when only 7 samples (below minSamples=8)');
  } finally {
    try { fs.unlinkSync(statePath); } catch (_) {}
  }
});

// ── Test 4: adaptiveAdjust does NOT bump when success dominates ───────────────
test('adaptiveAdjust does not bump tier when success dominates', () => {
  const statePath = tmpPath();
  try {
    // 8 successes, 1 retry — success dominates
    for (let i = 0; i < 8; i++) {
      recordOutcome('coder', 'medium', 2, 'success', statePath);
    }
    recordOutcome('coder', 'medium', 2, 'retry', statePath);

    const adjusted = adaptiveAdjust('coder', 'medium', 2, POLICY, statePath);
    assert.equal(adjusted, 2, 'tier must NOT bump when success dominates over retry/escalate');
  } finally {
    try { fs.unlinkSync(statePath); } catch (_) {}
  }
});

// ── Test 5: hysteresis prevents re-bump within hysteresis window ──────────────
test('hysteresis prevents re-bump within hysteresis observation-window of last bump', () => {
  const statePath = tmpPath();
  try {
    // Trigger first bump: 8 retries
    for (let i = 0; i < 8; i++) {
      recordOutcome('coder', 'medium', 2, 'retry', statePath);
    }

    // First call: should bump
    const first = adaptiveAdjust('coder', 'medium', 2, POLICY, statePath);
    assert.equal(first, 3, 'first adaptiveAdjust must bump to 3');

    // Record the bump by calling recordOutcome to advance observation count
    // Within hysteresis window (2 observations) — should NOT bump again
    recordOutcome('coder', 'medium', 3, 'retry', statePath);
    const second = adaptiveAdjust('coder', 'medium', 2, POLICY, statePath);
    assert.equal(second, 2, 'second adaptiveAdjust must NOT re-bump within hysteresis window');

    // After hysteresis window (2 more observations) — bump eligible again
    recordOutcome('coder', 'medium', 3, 'retry', statePath);
    const third = adaptiveAdjust('coder', 'medium', 2, POLICY, statePath);
    assert.equal(third, 3, 'adaptiveAdjust must be eligible to bump again after hysteresis window');
  } finally {
    try { fs.unlinkSync(statePath); } catch (_) {}
  }
});

// ── Test 6: tier is clamped at 3 (never exceeds max) ─────────────────────────
test('adaptiveAdjust clamps bumped tier at 3', () => {
  const statePath = tmpPath();
  try {
    for (let i = 0; i < 8; i++) {
      recordOutcome('architect', 'complex', 3, 'retry', statePath);
    }

    const adjusted = adaptiveAdjust('architect', 'complex', 3, POLICY, statePath);
    assert.equal(adjusted, 3, 'tier must be clamped at 3 even when bump would exceed it');
  } finally {
    try { fs.unlinkSync(statePath); } catch (_) {}
  }
});

// ── Test 7: null bucket falls back to "default" key ──────────────────────────
test('recordOutcome uses "default" bucket when bucket arg is null', () => {
  const statePath = tmpPath();
  try {
    recordOutcome('coder', null, 2, 'success', statePath);
    const raw = JSON.parse(fs.readFileSync(statePath, 'utf8'));
    assert.ok('coder:default' in raw, 'null bucket must be stored under "default" key');
    assert.equal(raw['coder:default'].success, 1);
  } finally {
    try { fs.unlinkSync(statePath); } catch (_) {}
  }
});

// ── Test 8: hook-handler record-outcome handler is present and callable ───────
test('hook-handler exports a record-outcome handler that calls recordOutcome', () => {
  const handler = require('./hook-handler.cjs');
  assert.equal(typeof handler, 'object', 'hook-handler must export an object');
  assert.equal(
    typeof handler['record-outcome'],
    'function',
    'hook-handler must export a "record-outcome" function',
  );

  // Call it with valid JSON input; must not throw
  const statePath = tmpPath();
  try {
    const input = JSON.stringify({
      agent: 'coder',
      bucket: 'medium',
      tier: 2,
      outcome: 'success',
      statePath,
    });
    // Should return without throwing (defensive — never throws)
    const result = handler['record-outcome'](input);
    // Return value is unspecified; just confirm it doesn't throw
    void result;

    const raw = JSON.parse(fs.readFileSync(statePath, 'utf8'));
    assert.ok('coder:medium' in raw, 'handler must have written coder:medium record');
  } finally {
    try { fs.unlinkSync(statePath); } catch (_) {}
  }
});

// ── Test 9: adaptiveAdjust returns unchanged tier when no state file exists ───
test('adaptiveAdjust returns unchanged tier when state file does not exist', () => {
  const statePath = tmpPath(); // file won't be created
  const result = adaptiveAdjust('coder', 'medium', 2, POLICY, statePath);
  assert.equal(result, 2, 'must return original tier when no state exists');
});

// ── Test 10: Codex-style outcome (Stop event) recorded via hook-handler ───────
test('hook-handler record-outcome handles Codex Stop event shape', () => {
  const handler = require('./hook-handler.cjs');
  const statePath = tmpPath();
  try {
    // Codex emits Stop/PostToolUse; simulate a Stop payload
    const input = JSON.stringify({
      event: 'Stop',
      agent: 'coder',
      bucket: 'complex',
      tier: 3,
      outcome: 'escalate',
      statePath,
    });
    handler['record-outcome'](input);

    const raw = JSON.parse(fs.readFileSync(statePath, 'utf8'));
    assert.ok('coder:complex' in raw, 'Stop event must record coder:complex');
    assert.equal(raw['coder:complex'].escalate, 1, 'escalate count must be 1');
  } finally {
    try { fs.unlinkSync(statePath); } catch (_) {}
  }
});

// ── Test 11: FIX I-2 — record-outcome resolves agent from tool_input.subagent_type ──
// Real Claude PostToolUse payloads carry the agent in tool_input.subagent_type.
test('record-outcome resolves agent from tool_input.subagent_type (real Claude PostToolUse shape)', () => {
  const handler = require('./hook-handler.cjs');
  const statePath = tmpPath();
  try {
    const input = JSON.stringify({
      tool_name: 'Agent',
      tool_input: { subagent_type: 'coder' },
      bucket: 'medium',
      tier: 2,
      outcome: 'success',
      statePath,
    });
    handler['record-outcome'](input);

    const raw = JSON.parse(fs.readFileSync(statePath, 'utf8'));
    assert.ok('coder:medium' in raw, 'agent resolved from tool_input.subagent_type must write coder:medium');
    assert.equal(raw['coder:medium'].success, 1, 'success count must be 1');
  } finally {
    try { fs.unlinkSync(statePath); } catch (_) {}
  }
});

// ── Test 12: FIX I-3 — record-outcome falls back to decision cache for agent/tier ──
// When the payload lacks agent and tier, handleRecordOutcome must read the cache.
test('record-outcome falls back to decision cache when payload lacks agent and tier', () => {
  const handler = require('./hook-handler.cjs');
  const { buildRouteOutput } = handler;
  const statePath = tmpPath();
  try {
    // Step 1: trigger a route to populate the decision cache
    buildRouteOutput('implement a feature', { harness: 'claude' });

    // Step 2: send a record-outcome payload WITHOUT agent or tier (Stop-like payload)
    const input = JSON.stringify({
      event: 'Stop',
      outcome: 'success',
      statePath,
      // no agent, no tier — must fall back to cache
    });
    handler['record-outcome'](input);

    const raw = JSON.parse(fs.readFileSync(statePath, 'utf8'));
    // The cache was populated by buildRouteOutput → coder (implement = coder agent)
    const keys = Object.keys(raw);
    assert.ok(keys.length > 0, 'decision cache fallback must have written at least one record');
    // The key must contain "coder" since "implement" routes to coder
    const coderKey = keys.find(k => k.startsWith('coder:'));
    assert.ok(coderKey, `must have a coder: key via cache fallback; keys were: ${keys.join(', ')}`);
  } finally {
    try { fs.unlinkSync(statePath); } catch (_) {}
  }
});

// ── Test 13: FIX I-1 — routeTask with seeded adaptive state returns bumped tier ──
// With a state where (coder, null) is retry-dominated past minSamples, routeTask
// with adaptiveAdjust returns a bumped tier vs the same call without the store.
test('routeTask with adaptiveAdjust wired returns bumped tier when store is retry-dominated', () => {
  const { routeTask } = require('./router.js');
  const { adaptiveAdjust: storeAdj } = require('./adaptive-store.cjs');
  const statePath = tmpPath();

  try {
    // Seed 8 retry outcomes for coder:null (null bucket → 'default' key)
    for (let i = 0; i < 8; i++) {
      recordOutcome('coder', null, 2, 'retry', statePath);
    }

    // Create an adaptiveAdjust bound to the temp state file
    const boundAdj = (agent, bucket, tier, policy) => storeAdj(agent, bucket, tier, policy, statePath);

    const withStore = routeTask('implement a feature', { harness: 'claude', adaptiveAdjust: boundAdj });
    const withoutStore = routeTask('implement a feature', { harness: 'claude' });

    // Both must have tier present
    assert.equal(typeof withStore.tier, 'number', 'withStore.tier must be a number');
    assert.equal(typeof withoutStore.tier, 'number', 'withoutStore.tier must be a number');

    // The store-wired call must produce a higher (bumped) tier
    assert.ok(
      withStore.tier > withoutStore.tier,
      `adaptive store must bump tier: got ${withStore.tier} (with store) vs ${withoutStore.tier} (without)`,
    );
    assert.equal(withStore.tier, withoutStore.tier + 1, 'bump must be exactly +1');
  } finally {
    try { fs.unlinkSync(statePath); } catch (_) {}
  }
});
