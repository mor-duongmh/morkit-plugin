'use strict';

/**
 * hook-handler.test.cjs — Tests for hook-handler.cjs route handler and
 * pretooluse-agent-gate.cjs PreToolUse gate.
 *
 * Tests are written to exercise exported pure functions rather than spawning
 * subprocesses, keeping them fast and deterministic.
 */

const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const {
  buildRouteOutput,
  buildGateDecision,
} = require('./hook-handler.cjs');

const POLICY_PATH = path.join(__dirname, 'model-policy.json');
const policy = JSON.parse(require('node:fs').readFileSync(POLICY_PATH, 'utf8'));

// ── route handler output ──────────────────────────────────────────────────────

test('buildRouteOutput prints [ROUTING] line with agent, tier, model, conf', () => {
  // "implement" prompt → coder, tier 2, model "sonnet" on claude harness
  const output = buildRouteOutput('implement a new feature', { harness: 'claude' });
  assert.ok(
    output.includes('[ROUTING]'),
    `output must start with [ROUTING]; got: ${output}`,
  );
  assert.ok(output.includes('agent=coder'), `must include agent=coder; got: ${output}`);
  assert.ok(output.includes('tier=2'), `must include tier=2; got: ${output}`);
  assert.ok(output.includes('model=sonnet'), `must include model=sonnet; got: ${output}`);
  assert.match(output, /conf \d\.\d\d/, 'must include (conf X.XX)');
});

test('buildRouteOutput minimal line when policy is null (bare routeTask result)', () => {
  // Simulate no policy: provide a null-policy path so routeTask returns bare shape
  // We pass the result directly as the function accepts a pre-computed result too.
  const output = buildRouteOutput('implement a new feature', { harness: 'claude', _policyPath: '/nonexistent/path.json' });
  assert.ok(output.includes('[ROUTING]'), `must still emit [ROUTING]; got: ${output}`);
  assert.ok(output.includes('agent='), `must include agent=; got: ${output}`);
  // tier and model must NOT appear when policy is null
  assert.ok(!output.includes('tier='), `must NOT include tier= when policy null; got: ${output}`);
  assert.ok(!output.includes('model='), `must NOT include model= when policy null; got: ${output}`);
});

// ── pretooluse-agent-gate ─────────────────────────────────────────────────────

const { buildGateDecision: gateDecision } = require('../hooks/pretooluse-agent-gate.cjs');

test('gate DENIES Agent call when model mismatches policy and confidence >= confidenceMin', () => {
  // subagent_type "coder" → tier 2 → model "sonnet" on claude harness
  // Passing "opus" as the requested model → mismatch with high confidence
  const decision = gateDecision({
    subagent_type: 'coder',
    model: 'opus',          // WRONG: policy says "sonnet" for coder/tier-2
    prompt: 'implement a feature',
  }, { confidence: 0.9, policy });

  assert.equal(decision.action, 'deny', 'action must be "deny"');
  assert.ok(
    decision.output.hookSpecificOutput.permissionDecision === 'deny',
    'permissionDecision must be "deny"',
  );
  assert.ok(
    typeof decision.output.hookSpecificOutput.permissionDecisionReason === 'string',
    'permissionDecisionReason must be a string',
  );
  assert.ok(
    decision.output.hookSpecificOutput.permissionDecisionReason.includes('sonnet'),
    `deny reason must name the expected model "sonnet"; got: ${decision.output.hookSpecificOutput.permissionDecisionReason}`,
  );
});

test('gate ALLOWS when model matches the policy model', () => {
  // coder → tier 2 → "sonnet"; passing "sonnet" → allow
  const decision = gateDecision({
    subagent_type: 'coder',
    model: 'sonnet',
    prompt: 'implement a feature',
  }, { confidence: 0.9, policy });

  assert.equal(decision.action, 'allow', 'action must be "allow" when model matches');
});

test('gate ALLOWS when model is missing (not specified)', () => {
  // No model field → allow (no enforcement needed)
  const decision = gateDecision({
    subagent_type: 'coder',
    prompt: 'implement a feature',
    // no model field
  }, { confidence: 0.9, policy });

  assert.equal(decision.action, 'allow', 'action must be "allow" when model is absent');
});

test('gate ALLOWS (warn only) when confidence is below confidenceMin even on mismatch', () => {
  // confidence 0.4 < confidenceMin 0.65 → do not deny, warn only
  const decision = gateDecision({
    subagent_type: 'coder',
    model: 'opus',         // mismatch, but low confidence
    prompt: 'implement a feature',
  }, { confidence: 0.4, policy });

  assert.equal(decision.action, 'allow', 'must be "allow" (not deny) when confidence below minimum');
  // Optionally includes a systemMessage warning
  if (decision.output && decision.output.systemMessage) {
    assert.equal(typeof decision.output.systemMessage, 'string', 'systemMessage must be string if present');
  }
});

test('gate ALLOWS (fail-open) when an internal error occurs', () => {
  // Pass null policy to trigger an internal error path
  const decision = gateDecision({
    subagent_type: 'coder',
    model: 'opus',
    prompt: 'implement a feature',
  }, { confidence: 0.9, policy: null });

  assert.equal(decision.action, 'allow', 'gate must fail open on internal error');
});
