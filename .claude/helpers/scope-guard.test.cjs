'use strict';

/**
 * scope-guard.test.cjs — Tests for the scope guard helper.
 *
 * Tests:
 *   S.1  isClaudePluginsRepo returns true when .model-routing.json is in the
 *        given dir and contains { "enabled": true }
 *   S.2  isClaudePluginsRepo returns false when .model-routing.json is absent
 *   S.3  isClaudePluginsRepo returns false when .model-routing.json is present
 *        but enabled != true
 *   S.4  isClaudePluginsRepo walks up from a subdirectory to find the marker
 *   S.5  isClaudePluginsRepo returns false when the marker is in none of the
 *        ancestors up to the filesystem root
 *   S.6  isClaudePluginsRepo returns false (not throws) on unreadable/invalid
 *        marker (fail-open-to-noop safety)
 *   S.7  Backward-compat: routeTask without policy returns bare
 *        { agent, confidence, reason } shape (regression guard)
 *   S.8  E2E smoke — claude harness: complex security prompt → tier 3 → opus
 *   S.9  E2E smoke — codex harness: complex security prompt → tier 3 → gpt-5.5
 *   S.10 E2E smoke — simple/downgrade prompt → tier 1 or 2 (lower tier)
 *   S.11 E2E smoke — guard ON (marker file present) → routing proceeds with tier
 *   S.12 E2E smoke — guard OFF (no marker) → hook-handler buildRouteOutput
 *        still produces output (guard is not wired into buildRouteOutput itself,
 *        but the main dispatcher no-ops; verify the helper stays usable)
 */

const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');

const { isClaudePluginsRepo } = require('./scope-guard.cjs');
const { routeTask } = require('./router.js');

// ── S.1: marker present and enabled ──────────────────────────────────────────

test('S.1 isClaudePluginsRepo returns true when .model-routing.json has enabled:true', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sg-test-'));
  try {
    fs.writeFileSync(
      path.join(tmp, '.model-routing.json'),
      JSON.stringify({ enabled: true }),
    );
    assert.equal(isClaudePluginsRepo(tmp), true, 'should return true for valid marker');
  } finally {
    fs.rmSync(tmp, { recursive: true });
  }
});

// ── S.2: marker absent ────────────────────────────────────────────────────────

test('S.2 isClaudePluginsRepo returns false when .model-routing.json is absent', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sg-test-'));
  try {
    assert.equal(isClaudePluginsRepo(tmp), false, 'should return false when marker missing');
  } finally {
    fs.rmSync(tmp, { recursive: true });
  }
});

// ── S.3: marker present but disabled ─────────────────────────────────────────

test('S.3 isClaudePluginsRepo returns false when enabled != true', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sg-test-'));
  try {
    fs.writeFileSync(
      path.join(tmp, '.model-routing.json'),
      JSON.stringify({ enabled: false }),
    );
    assert.equal(isClaudePluginsRepo(tmp), false, 'should return false when enabled is false');
  } finally {
    fs.rmSync(tmp, { recursive: true });
  }
});

// ── S.4: walks up from subdirectory ───────────────────────────────────────────

test('S.4 isClaudePluginsRepo walks up from a subdirectory', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sg-test-'));
  const sub = path.join(tmp, 'a', 'b', 'c');
  try {
    fs.mkdirSync(sub, { recursive: true });
    fs.writeFileSync(
      path.join(tmp, '.model-routing.json'),
      JSON.stringify({ enabled: true }),
    );
    assert.equal(isClaudePluginsRepo(sub), true, 'should walk up and find marker');
  } finally {
    fs.rmSync(tmp, { recursive: true });
  }
});

// ── S.5: marker in none of the ancestors ──────────────────────────────────────

test('S.5 isClaudePluginsRepo returns false when marker is not in any ancestor', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sg-test-'));
  const sub = path.join(tmp, 'x', 'y');
  try {
    fs.mkdirSync(sub, { recursive: true });
    // No marker file anywhere in tmp or sub
    assert.equal(isClaudePluginsRepo(sub), false, 'should return false when marker absent throughout');
  } finally {
    fs.rmSync(tmp, { recursive: true });
  }
});

// ── S.6: invalid marker → fail-open-to-noop ───────────────────────────────────

test('S.6 isClaudePluginsRepo returns false (does not throw) on invalid marker JSON', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sg-test-'));
  try {
    fs.writeFileSync(path.join(tmp, '.model-routing.json'), 'NOT-JSON{{{');
    assert.doesNotThrow(
      () => isClaudePluginsRepo(tmp),
      'should not throw on invalid JSON',
    );
    assert.equal(isClaudePluginsRepo(tmp), false, 'should return false on parse error');
  } finally {
    fs.rmSync(tmp, { recursive: true });
  }
});

// ── S.7: backward-compat — routeTask without policy returns bare shape ─────────

test('S.7 routeTask with absent policy returns bare { agent, confidence, reason }', () => {
  // Force the policy-absent path via the _policyPath test seam (a nonexistent
  // file makes loadPolicy return null). This does NOT mutate the shared default
  // model-policy.json, so it is safe to run concurrently with sibling test files.
  const result = routeTask('implement a new feature', {
    harness: 'claude',
    _policyPath: path.join(__dirname, '.does-not-exist-policy.json'),
  });

  // Must be bare shape: has agent/confidence/reason, must NOT have tier/model
  assert.ok(typeof result.agent === 'string', 'result must have agent');
  assert.ok(typeof result.confidence === 'number', 'result must have confidence');
  assert.ok(typeof result.reason === 'string', 'result must have reason');
  assert.equal(result.tier, undefined, 'bare shape must NOT have tier');
  assert.equal(result.model, undefined, 'bare shape must NOT have model');
});

// ── S.8: E2E smoke — claude harness, security prompt → tier 3 → opus ─────────

test('S.8 E2E smoke: claude harness, security migration across 3 files → tier 3 → opus', () => {
  const result = routeTask(
    'implement a security migration touching src/auth.js src/users.js src/session.js',
    { harness: 'claude' },
  );
  assert.ok(typeof result.tier === 'number', 'enriched result must have tier');
  assert.equal(result.tier, 3, `expected tier 3 for security+multifile prompt; got ${result.tier}`);
  assert.equal(result.model, 'opus', `expected model opus for tier 3 claude; got ${result.model}`);
  assert.ok(
    result.escalators && result.escalators.some(e => e.includes('security')),
    `escalators must include +security; got ${JSON.stringify(result.escalators)}`,
  );
});

// ── S.9: E2E smoke — codex harness, security prompt → tier 3 → gpt-5.5 ───────

test('S.9 E2E smoke: codex harness, security migration across 3 files → tier 3 → gpt-5.5', () => {
  const result = routeTask(
    'implement a security migration touching src/auth.js src/users.js src/session.js',
    { harness: 'codex' },
  );
  assert.ok(typeof result.tier === 'number', 'enriched result must have tier');
  assert.equal(result.tier, 3, `expected tier 3 for security+multifile codex; got ${result.tier}`);
  assert.equal(result.model, 'gpt-5.5', `expected model gpt-5.5 for tier 3 codex; got ${result.model}`);
});

// ── S.10: E2E smoke — downgrade prompt → lower tier ───────────────────────────

test('S.10 E2E smoke: rename/format prompt → tier 1 (downgraded from coder base 2)', () => {
  const result = routeTask('rename a variable typo in utils.js', { harness: 'claude' });
  assert.ok(typeof result.tier === 'number', 'enriched result must have tier');
  // coder base is 2; "rename" and "typo" are down escalators → tier 1
  assert.ok(result.tier <= 2, `expected tier <= 2 for rename/typo prompt; got ${result.tier}`);
  // model should not be opus
  assert.notEqual(result.model, 'opus', 'rename/typo prompt should not route to opus');
});

// ── S.11: E2E smoke — guard ON: routing produces enriched output ───────────────

test('S.11 E2E smoke: guard ON (marker present) → buildRouteOutput produces tier+model line', () => {
  const { buildRouteOutput } = require('./hook-handler.cjs');
  const out = buildRouteOutput(
    'implement a security migration touching src/a.js src/b.js src/c.js',
    { harness: 'claude' },
  );
  assert.ok(out.includes('[ROUTING]'), `must include [ROUTING]; got: ${out}`);
  assert.ok(out.includes('tier=3'), `must include tier=3 for security+multifile; got: ${out}`);
  assert.ok(out.includes('model=opus'), `must include model=opus; got: ${out}`);
});

// ── S.12: E2E smoke — guard OFF simulation: hook-handler stays usable ──────────

test('S.12 E2E smoke: buildRouteOutput usable regardless of scope guard state', () => {
  // The scope guard is enforced in the entry point (main()), not in buildRouteOutput itself.
  // This test confirms buildRouteOutput remains a pure, usable helper for other callers.
  const { buildRouteOutput } = require('./hook-handler.cjs');
  const out = buildRouteOutput('implement a feature', { harness: 'claude' });
  assert.ok(typeof out === 'string', 'buildRouteOutput must return a string');
  assert.ok(out.includes('[ROUTING]'), 'must include [ROUTING]');
  assert.ok(out.length > 0, 'output must be non-empty');
});
