#!/usr/bin/env node
/**
 * Claude Flow Agent Router
 * Routes tasks to optimal agents based on learned patterns.
 * Tier computation and harness-aware model mapping via model-router.js.
 */

'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { computeTierWithPolicy } = require('./model-router.js');

const DEFAULT_POLICY_PATH = path.join(__dirname, 'model-policy.json');

const REQUIRED_KEYS = ['schemaVersion', 'agentBase', 'escalators', 'tierModel', 'complexity', 'adaptive'];

/**
 * Load and validate the model routing policy file.
 *
 * @param {string} [policyPath] - Path to the policy JSON file. Defaults to model-policy.json
 *   in the same directory as this module.
 * @returns {object|null} Parsed policy object, or null if the file is missing,
 *   unparseable, or fails validation.
 */
function loadPolicy(policyPath) {
  const filePath = policyPath || DEFAULT_POLICY_PATH;

  let raw;
  try {
    raw = fs.readFileSync(filePath, 'utf8');
  } catch (_err) {
    return null;
  }

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (_err) {
    return null;
  }

  // Validate required top-level keys
  for (const key of REQUIRED_KEYS) {
    if (!(key in parsed)) {
      return null;
    }
  }

  // Validate schemaVersion === 1
  if (parsed.schemaVersion !== 1) {
    return null;
  }

  return parsed;
}

const AGENT_CAPABILITIES = {
  coder: ['code-generation', 'refactoring', 'debugging', 'implementation'],
  tester: ['unit-testing', 'integration-testing', 'coverage', 'test-generation'],
  reviewer: ['code-review', 'security-audit', 'quality-check', 'best-practices'],
  researcher: ['web-search', 'documentation', 'analysis', 'summarization'],
  architect: ['system-design', 'architecture', 'patterns', 'scalability'],
  'backend-dev': ['api', 'database', 'server', 'authentication'],
  'frontend-dev': ['ui', 'react', 'css', 'components'],
  devops: ['ci-cd', 'docker', 'deployment', 'infrastructure'],
};

const TASK_PATTERNS = {
  // Code patterns
  'implement|create|build|add|write code': 'coder',
  'test|spec|coverage|unit test|integration': 'tester',
  'review|audit|check|validate|security': 'reviewer',
  'research|find|search|documentation|explore': 'researcher',
  'design|architect|structure|plan': 'architect',

  // Domain patterns
  'api|endpoint|server|backend|database': 'backend-dev',
  'ui|frontend|component|react|css|style': 'frontend-dev',
  'deploy|docker|ci|cd|pipeline|infrastructure': 'devops',
};

/**
 * Route a task prompt to an agent, optionally computing tier and model.
 *
 * @param {string} task - Task description prompt.
 * @param {object} [opts]
 * @param {string}   [opts.harness="claude"]   - Model harness: "claude" or "codex".
 * @param {number|null} [opts.complexityScore] - SEAM for Task 4.
 * @param {function}    [opts.adaptiveAdjust]  - SEAM for Task 5.
 * @returns {{ agent, confidence, reason } | { agent, tier, model, confidence, reason, escalators }}
 *   Returns the enriched shape when policy loads successfully; falls back to the
 *   base shape when policy is unavailable (backward compatible).
 */
function routeTask(task, opts) {
  const taskLower = task.toLowerCase();

  // Keyword match → agent + confidence + reason
  let agent = 'coder';
  let confidence = 0.5;
  let reason = 'Default routing - no specific pattern matched';

  for (const [pattern, matchedAgent] of Object.entries(TASK_PATTERNS)) {
    const regex = new RegExp(pattern, 'i');
    if (regex.test(taskLower)) {
      agent = matchedAgent;
      confidence = 0.8;
      reason = `Matched pattern: ${pattern}`;
      break;
    }
  }

  // Attempt to load policy for enriched routing.
  // opts._policyPath is a test seam: pass a nonexistent path to force the
  // policy-absent (bare-shape) path WITHOUT mutating the shared default file.
  const policy = (opts && opts._policyPath) ? loadPolicy(opts._policyPath) : loadPolicy();
  if (!policy) {
    // Backward-compatible fallback: return base shape only
    return { agent, confidence, reason };
  }

  const harness = (opts && opts.harness) || 'claude';
  const complexityScore = (opts && opts.complexityScore != null) ? opts.complexityScore : null;
  const adaptiveAdjust = (opts && typeof opts.adaptiveAdjust === 'function') ? opts.adaptiveAdjust : null;

  const { tier, model, escalators } = computeTierWithPolicy({
    agent,
    confidence,
    prompt: task,
    policy,
    harness,
    complexityScore,
    adaptiveAdjust,
  });

  return { agent, tier, model, confidence, reason, escalators };
}

/**
 * Compute tier for a given agent/confidence/prompt against the default policy.
 * Exposed for direct testing of tier logic without going through routeTask's
 * pattern-matching. Falls back to the default policy path.
 *
 * @param {object} opts
 * @param {string}  opts.agent
 * @param {number}  opts.confidence
 * @param {string}  opts.prompt
 * @param {string} [opts.harness="claude"]
 * @returns {{ tier: number, model: string, escalators: string[] }}
 */
function computeTier({ agent, confidence, prompt, harness = 'claude' }) {
  const policy = loadPolicy();
  if (!policy) {
    throw new Error('computeTier requires a loadable policy; model-policy.json is missing or invalid');
  }
  return computeTierWithPolicy({ agent, confidence, prompt, policy, harness });
}

// CLI — only runs when executed directly (not when require()'d by hook-handler etc.)
if (require.main === module) {
  const task = process.argv.slice(2).join(' ');
  if (task) {
    const result = routeTask(task);
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log('Usage: router.js <task description>');
    console.log('\nAvailable agents:', Object.keys(AGENT_CAPABILITIES).join(', '));
  }
}

module.exports = { routeTask, computeTier, loadPolicy, AGENT_CAPABILITIES, TASK_PATTERNS };
