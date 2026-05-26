'use strict';

/**
 * complexity-scorer.cjs — Embedding-based prompt complexity scorer.
 *
 * Scores a prompt against a reference set (simple/medium/complex) using
 * cosine similarity to embeddings from Xenova/all-MiniLM-L6-v2 (384-dim).
 *
 * Embedding backend: Option B — shells out to the claude-flow CLI
 *   `npx @claude-flow/cli@latest embeddings generate -t <text> -o array`
 *   This works offline (local ONNX model), requires no package.json or
 *   @xenova/transformers install, and the model is already cached on disk.
 *
 * Option C fallback: if the CLI is unreachable or returns no data, score()
 *   returns null and the router falls back to keyword-only tier computation.
 *
 * Enabling V1 embeddings in CI / production:
 *   Ensure `npx @claude-flow/cli@latest` resolves to ≥3.10.1 and the model
 *   cache exists at ~/.cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx/model.onnx
 *   (pre-populated by running `npx @claude-flow/cli@latest embeddings warmup`).
 *   Set COMPLEXITY_CLI_PATH env var to override the CLI invocation path.
 *
 * @module complexity-scorer
 */

const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
// FIX N-5: import canonical loadPolicy from router.js instead of a partial reimplementation.
// The canonical version validates schema (schemaVersion, required keys); this scorer only
// needs complexity.enabled so it stays backward compatible — both return null on failure.
const { loadPolicy } = require('./router.js');

const REFSET_PATH = path.join(__dirname, 'embeddings', 'complexity-refset.json');
// Precomputed reference-set vectors. When present, loadRefCache reads these from
// disk instead of shelling out 30x (~66s cold). Regenerate with buildRefVectors().
const REFVEC_PATH = path.join(__dirname, 'embeddings', 'complexity-refset-vectors.json');
const DEFAULT_CLI = process.env.COMPLEXITY_CLI_PATH || 'npx';
// `--prefer-offline` keeps npx on the local cache (no registry round-trip) so a
// single embed stays within the hook budget; it only hits the network if the
// package is genuinely missing.
const DEFAULT_CLI_ARGS = ['--prefer-offline', '@claude-flow/cli@latest', 'embeddings', 'generate', '-o', 'array', '-t'];

// Cached reference set embeddings (computed once per process lifetime)
let refCache = null;

/**
 * Compute cosine similarity between two equal-length vectors.
 *
 * @param {number[]} a
 * @param {number[]} b
 * @returns {number} similarity in [-1, 1]
 */
function cosine(a, b) {
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  const denom = Math.sqrt(normA) * Math.sqrt(normB);
  if (denom === 0) return 0;
  return dot / denom;
}

/**
 * Generate an embedding vector for a text string using the CLI backend.
 *
 * @param {string} text
 * @param {string} cliPath  - CLI executable (defaults to 'npx').
 * @returns {number[]|null} 384-dim vector, or null if backend is unreachable.
 */
function generateEmbedding(text, cliPath) {
  const exe = cliPath || DEFAULT_CLI;
  const args = cliPath && cliPath !== 'npx'
    ? ['-o', 'array', '-t', text]  // custom CLI, no npx prefix
    : [...DEFAULT_CLI_ARGS, text];

  let result;
  try {
    result = spawnSync(exe, args, {
      encoding: 'utf8',
      timeout: 15000,
      maxBuffer: 2 * 1024 * 1024,
    });
  } catch (_err) {
    return null;
  }

  if (result.status !== 0 || !result.stdout) return null;

  // Strip ANSI escape codes and progress spinner lines; find the JSON array.
  const out = result.stdout.replace(/\x1b\[[0-9;]*m/g, '');
  const match = out.match(/\[[-\d.,\se+]+\]/);
  if (!match) return null;

  try {
    const vec = JSON.parse(match[0]);
    if (!Array.isArray(vec) || vec.length < 1) return null;
    return vec;
  } catch (_e) {
    return null;
  }
}

/**
 * Load and embed all reference prompts. Results are cached per process.
 *
 * @param {string} cliPath
 * @returns {{ simple: number[][], medium: number[][], complex: number[][] }|null}
 */
function loadRefCache(cliPath) {
  if (refCache) return refCache;

  // Fast path: precomputed vectors on disk (no shelling out).
  const precomputed = readPrecomputedVectors();
  if (precomputed) {
    refCache = precomputed;
    return refCache;
  }

  // Slow fallback: embed every reference prompt (cold ~66s). Kept for
  // resilience when the vectors file is absent or stale.
  let refset;
  try {
    refset = JSON.parse(fs.readFileSync(REFSET_PATH, 'utf8'));
  } catch (_e) {
    return null;
  }

  const buckets = {};
  for (const bucket of ['simple', 'medium', 'complex']) {
    const prompts = refset[bucket];
    if (!Array.isArray(prompts) || prompts.length === 0) return null;
    const vecs = [];
    for (const p of prompts) {
      const v = generateEmbedding(p, cliPath);
      if (!v) return null;
      vecs.push(v);
    }
    buckets[bucket] = vecs;
  }

  refCache = buckets;
  return refCache;
}

/**
 * Read precomputed reference vectors from REFVEC_PATH.
 *
 * @returns {{ simple: number[][], medium: number[][], complex: number[][] }|null}
 *   null when the file is absent, malformed, or any bucket is empty.
 */
function readPrecomputedVectors() {
  let data;
  try {
    data = JSON.parse(fs.readFileSync(REFVEC_PATH, 'utf8'));
  } catch (_e) {
    return null;
  }
  const buckets = {};
  for (const bucket of ['simple', 'medium', 'complex']) {
    const vecs = data && data[bucket];
    if (!Array.isArray(vecs) || vecs.length === 0) return null;
    for (const v of vecs) {
      if (!Array.isArray(v) || v.length < 1) return null;
    }
    buckets[bucket] = vecs;
  }
  return buckets;
}

/**
 * Build the precomputed reference-vectors file by embedding every prompt in the
 * reference set. Run once at build time (or after editing the ref set):
 *   node -e "require('./.claude/helpers/complexity-scorer.cjs').buildRefVectors()"
 *
 * @param {string} [cliPath] - Override CLI executable (for testing).
 * @returns {{ written: string, counts: object }} path written and per-bucket counts.
 * @throws if the ref set is unreadable or any embedding fails.
 */
function buildRefVectors(cliPath) {
  const refset = JSON.parse(fs.readFileSync(REFSET_PATH, 'utf8'));
  const out = {};
  const counts = {};
  for (const bucket of ['simple', 'medium', 'complex']) {
    const prompts = refset[bucket];
    if (!Array.isArray(prompts) || prompts.length === 0) {
      throw new Error(`ref set bucket "${bucket}" is empty or missing`);
    }
    out[bucket] = prompts.map((p) => {
      const v = generateEmbedding(p, cliPath);
      if (!v) throw new Error(`embedding failed for prompt: ${p}`);
      return v;
    });
    counts[bucket] = out[bucket].length;
  }
  fs.writeFileSync(REFVEC_PATH, JSON.stringify(out));
  return { written: REFVEC_PATH, counts };
}

/**
 * Score a prompt against the reference set.
 *
 * @param {string} prompt
 * @param {object} [opts]
 * @param {boolean} [opts.complexityEnabled] - Override policy.complexity.enabled check.
 *   Pass false to force null return regardless of backend.
 * @param {string}  [opts.cliPath] - Override CLI executable path (for testing).
 * @returns {{ bucket: "simple"|"medium"|"complex", confidence: number }|null}
 *   Returns null when:
 *   - complexity.enabled === false (policy or opts override)
 *   - embedding backend is unreachable
 */
function score(prompt, opts) {
  opts = opts || {};

  // Check complexityEnabled override
  if (opts.complexityEnabled === false) return null;

  // Check policy
  const policy = loadPolicy();
  if (policy && policy.complexity && policy.complexity.enabled === false) return null;

  const cliPath = opts.cliPath || null;

  // Load reference embeddings (cached after first successful call)
  const refs = loadRefCache(cliPath);
  if (!refs) return null;

  // Embed the input prompt
  const promptVec = generateEmbedding(prompt, cliPath);
  if (!promptVec) return null;

  // Compute mean cosine similarity to each bucket
  const bucketScores = {};
  for (const bucket of ['simple', 'medium', 'complex']) {
    const vecs = refs[bucket];
    let total = 0;
    for (const v of vecs) {
      total += cosine(promptVec, v);
    }
    bucketScores[bucket] = total / vecs.length;
  }

  // Pick the winning bucket
  let bestBucket = 'medium';
  let bestScore = -Infinity;
  for (const [bucket, s] of Object.entries(bucketScores)) {
    if (s > bestScore) {
      bestScore = s;
      bestBucket = bucket;
    }
  }

  // Confidence = margin of winning bucket over the second-best
  // Normalised to [0, 1] using the range of possible cosine values [0, 1] for
  // typical sentence embeddings: confidence = (best - second) / best
  const scores = Object.values(bucketScores).sort((a, b) => b - a);
  const margin = scores[0] - scores[1];
  // Normalise: margin is in [0, ~1]; divide by best score to get relative separation
  const confidence = bestScore > 0 ? Math.min(1, margin / bestScore) : 0;

  return { bucket: bestBucket, confidence };
}

/**
 * Pure helper: determine whether a scorer result meets the confidence minimum
 * required for "strict" enforcement (vs. warn-only).
 *
 * @param {number} confidence - From score() result.
 * @param {number} confidenceMin - From policy.complexity.confidenceMin.
 * @returns {boolean}
 */
function isStrictEligible(confidence, confidenceMin) {
  return confidence >= confidenceMin;
}

module.exports = { score, isStrictEligible, cosine, generateEmbedding, buildRefVectors, readPrecomputedVectors };
