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

// ── A1: complexity scoring gated to uncertain prompts only ────────────────────

test('buildRouteOutput does NOT score when liveInHook is OFF, even for an uncertain prompt', () => {
  let calls = 0;
  const spy = () => { calls += 1; return { bucket: 'complex', confidence: 0.9 }; };
  // "ponder the meaning of existence" matches no task pattern → confidence 0.5 (uncertain)
  const output = buildRouteOutput('ponder the meaning of existence', {
    harness: 'claude', _liveInHook: false, _score: spy,
  });
  assert.equal(calls, 0, 'scorer must NOT be called when liveInHook is OFF');
  assert.ok(!output.includes('complexity'), `no complexity escalator expected; got: ${output}`);
});

test('buildRouteOutput scores an UNCERTAIN prompt when liveInHook is ON (escalate-only)', () => {
  let calls = 0;
  const spy = (p) => { calls += 1; assert.equal(typeof p, 'string'); return { bucket: 'complex', confidence: 0.9 }; };
  const output = buildRouteOutput('ponder the meaning of existence', {
    harness: 'claude', _liveInHook: true, _score: spy,
  });
  assert.equal(calls, 1, 'scorer must be called exactly once on an uncertain prompt');
  assert.ok(output.includes('+complexity'), `complex bucket must add +complexity escalator; got: ${output}`);
});

test('buildRouteOutput does NOT score a CONFIDENT (keyword-matched) prompt even when liveInHook is ON', () => {
  let calls = 0;
  const spy = () => { calls += 1; return { bucket: 'complex', confidence: 0.9 }; };
  // "implement a new feature" matches the coder pattern → confidence 0.8 (≥ threshold)
  const output = buildRouteOutput('implement a new feature', {
    harness: 'claude', _liveInHook: true, _score: spy,
  });
  assert.equal(calls, 0, 'scorer must NOT be called when keyword routing is confident');
  assert.ok(!output.includes('complexity'), `no complexity escalator on confident route; got: ${output}`);
});

// ── pretooluse-agent-gate ─────────────────────────────────────────────────────

const { buildGateDecision: gateDecision } = require('../hooks/pretooluse-agent-gate.cjs');

test('gate DENIES an UNDER-POWERED spawn (haiku where policy floor is sonnet) at high confidence', () => {
  // coder + "implement a feature" → tier 2 (sonnet) floor, confidence 0.8 (>= 0.65).
  // Spawning "haiku" (tier 1) is below the floor → DENY.
  const decision = gateDecision({
    subagent_type: 'coder',
    model: 'haiku',         // tier 1 < expected tier 2
    prompt: 'implement a feature',
  }, { policy });

  assert.equal(decision.action, 'deny', 'action must be "deny" for under-powered spawn');
  assert.equal(
    decision.output.hookSpecificOutput.permissionDecision,
    'deny',
    'permissionDecision must be "deny"',
  );
  assert.ok(
    typeof decision.output.hookSpecificOutput.permissionDecisionReason === 'string',
    'permissionDecisionReason must be a string',
  );
  assert.ok(
    decision.output.hookSpecificOutput.permissionDecisionReason.includes('sonnet'),
    `deny reason must name the expected floor model "sonnet"; got: ${decision.output.hookSpecificOutput.permissionDecisionReason}`,
  );
});

test('gate ALLOWS an ESCALATED spawn (opus for a "security" coder task)', () => {
  // coder + "security" task → router escalates to tier 3 (opus). Spawning opus
  // matches the escalated floor → ALLOW. This is the false-positive the floor
  // semantics fix: the OLD base-match logic would have denied this.
  const decision = gateDecision({
    subagent_type: 'coder',
    model: 'opus',          // tier 3 == escalated floor tier 3
    prompt: 'add security auth to the login module',
  }, { policy });

  assert.equal(decision.action, 'allow', 'escalated spawn matching the escalated floor must be ALLOWED');
});

test('gate ALLOWS an OVER-POWERED spawn (opus for a plain tier-2 coder task)', () => {
  // coder + plain task → tier 2 floor. Spawning opus (tier 3) is MORE capable
  // than the floor → ALLOW (operator may choose to spend more).
  const decision = gateDecision({
    subagent_type: 'coder',
    model: 'opus',          // tier 3 > expected tier 2
    prompt: 'implement a feature',
  }, { policy });

  assert.equal(decision.action, 'allow', 'over-powered spawn must be ALLOWED (>= floor)');
});

test('gate ALLOWS when spawned model exactly matches the floor', () => {
  // coder → tier 2 → "sonnet"; spawning "sonnet" → allow
  const decision = gateDecision({
    subagent_type: 'coder',
    model: 'sonnet',
    prompt: 'implement a feature',
  }, { policy });

  assert.equal(decision.action, 'allow', 'action must be "allow" when model equals floor');
});

test('gate ALLOWS when model is missing (not specified)', () => {
  // No model field → allow (no enforcement needed)
  const decision = gateDecision({
    subagent_type: 'coder',
    prompt: 'implement a feature',
    // no model field
  }, { policy });

  assert.equal(decision.action, 'allow', 'action must be "allow" when model is absent');
});

test('gate ALLOWS (warn only) when confidence is below confidenceMin even when under-powered', () => {
  // confidence override 0.4 < confidenceMin 0.65 → do not deny, warn only.
  const decision = gateDecision({
    subagent_type: 'coder',
    model: 'haiku',         // under-powered, but low confidence
    prompt: 'implement a feature',
  }, { confidence: 0.4, policy });

  assert.equal(decision.action, 'allow', 'must be "allow" (not deny) when confidence below minimum');
  assert.ok(decision.output && typeof decision.output.systemMessage === 'string',
    'must include a systemMessage warning per strictBelowMinFallback "warn"');
});

test('gate ALLOWS (fail-open) when an internal error occurs', () => {
  // Pass null policy to trigger the fail-open path
  const decision = gateDecision({
    subagent_type: 'coder',
    model: 'haiku',
    prompt: 'implement a feature',
  }, { policy: null });

  assert.equal(decision.action, 'allow', 'gate must fail open on internal error');
});
