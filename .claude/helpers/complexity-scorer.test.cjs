'use strict';

/**
 * complexity-scorer.test.cjs
 *
 * By default the embedding-backend tests are SKIPPED so `node --test .claude/helpers/`
 * stays fast (< 1s) in CI and dev loops. The backend is the claude-flow CLI which
 * must shell out per embedding (~1.4s each, 30 ref prompts on first call).
 *
 * To run all tests including real embedding assertions:
 *   ENABLE_EMBEDDING_TESTS=1 node --test .claude/helpers/complexity-scorer.test.cjs
 */

const { test } = require('node:test');
const assert = require('node:assert/strict');

const { score, isStrictEligible, readPrecomputedVectors } = require('./complexity-scorer.cjs');

const EMBEDDING_TESTS = process.env.ENABLE_EMBEDDING_TESTS === '1';

// ── Precomputed vectors (A2): fast path, no shell-out ─────────────────────────
// loadRefCache reads these instead of embedding 30 ref prompts (~66s cold).
test('readPrecomputedVectors returns three buckets of equal-length 384-dim vectors', () => {
  const refs = readPrecomputedVectors();
  assert.ok(refs !== null, 'precomputed vectors file must exist and parse');
  for (const bucket of ['simple', 'medium', 'complex']) {
    assert.ok(Array.isArray(refs[bucket]) && refs[bucket].length === 10,
      `${bucket} must have 10 precomputed vectors, got ${refs[bucket] && refs[bucket].length}`);
    for (const v of refs[bucket]) {
      assert.equal(v.length, 384, `each ${bucket} vector must be 384-dim`);
      assert.ok(v.every((n) => typeof n === 'number'), `${bucket} vectors must be numeric`);
    }
  }
});

// ── Test 1: null-path when complexity.enabled=false ───────────────────────────
test('score() returns null when complexityEnabled opt is false', () => {
  const result = score('implement an endpoint', { complexityEnabled: false });
  assert.equal(result, null, 'must return null when complexity.enabled is false');
});

// ── Test 2: null-path when CLI backend is unreachable ─────────────────────────
// scorer must not throw; returns null gracefully (Option C fallback)
test('score() returns null gracefully when embedding backend is unavailable', () => {
  const result = score('implement an endpoint', { cliPath: '/nonexistent/path/to/cli' });
  assert.equal(result, null, 'must return null when embedding backend is unreachable');
});

// ── Test 3: isStrictEligible — pure confidence-threshold helper ───────────────
test('isStrictEligible returns true only when confidence meets or exceeds confidenceMin', () => {
  // exactly at threshold
  assert.equal(isStrictEligible(0.65, 0.65), true, 'at threshold must be strict-eligible');
  // above threshold
  assert.equal(isStrictEligible(0.9, 0.65), true, 'above threshold must be strict-eligible');
  // below threshold
  assert.equal(isStrictEligible(0.64, 0.65), false, 'below threshold must NOT be strict-eligible');
  assert.equal(isStrictEligible(0.0, 0.65), false, 'zero confidence is not strict-eligible');
  // different threshold
  assert.equal(isStrictEligible(0.5, 0.5), true, 'exactly at 0.5 threshold is strict-eligible');
  assert.equal(isStrictEligible(0.49, 0.5), false, 'below 0.5 threshold is not strict-eligible');
});

// ── Test 4 (embedding): return shape when backend IS available ────────────────
// Skipped unless ENABLE_EMBEDDING_TESTS=1
test('score() returns valid result shape when backend is available', { skip: !EMBEDDING_TESTS }, (t) => {
  if (!EMBEDDING_TESTS) return; // guard for clarity
  const result = score('fix a typo in the README');
  if (result === null) {
    t.diagnostic('WARNING: backend returned null despite ENABLE_EMBEDDING_TESTS=1');
    assert.equal(result, null);
    return;
  }
  assert.ok(
    ['simple', 'medium', 'complex'].includes(result.bucket),
    `bucket must be simple/medium/complex, got: ${result.bucket}`,
  );
  assert.ok(
    typeof result.confidence === 'number' && result.confidence >= 0 && result.confidence <= 1,
    `confidence must be a number in [0,1], got: ${result.confidence}`,
  );
});

// ── Test 5 (embedding): simple prompt → "simple" bucket ──────────────────────
test('score() classifies a clearly simple prompt correctly', { skip: !EMBEDDING_TESTS }, () => {
  const result = score('rename a variable to a more descriptive name');
  assert.ok(result !== null, 'must not return null when backend is available');
  assert.equal(result.bucket, 'simple', `simple prompt must map to simple bucket, got ${result.bucket}`);
});

// ── Test 6 (embedding): complex prompt → "complex" bucket ────────────────────
test('score() classifies a clearly complex prompt correctly', { skip: !EMBEDDING_TESTS }, () => {
  const result = score('design and implement a distributed event sourcing system with CQRS pattern');
  assert.ok(result !== null, 'must not return null when backend is available');
  assert.equal(result.bucket, 'complex', `complex prompt must map to complex bucket, got ${result.bucket}`);
});

// ── Test 7 (embedding): confidence reflects separation quality ────────────────
// A verbatim reference prompt should score higher confidence than an ambiguous one.
test('score() returns higher confidence for verbatim ref prompts than ambiguous ones', { skip: !EMBEDDING_TESTS }, () => {
  const verbatim = score('fix a typo in the README');
  const ambiguous = score('update the implementation');
  assert.ok(verbatim !== null, 'verbatim ref prompt must not return null');
  assert.ok(ambiguous !== null, 'ambiguous prompt must not return null');
  assert.ok(
    verbatim.confidence >= ambiguous.confidence,
    `verbatim confidence (${verbatim.confidence}) should be >= ambiguous (${ambiguous.confidence})`,
  );
});
