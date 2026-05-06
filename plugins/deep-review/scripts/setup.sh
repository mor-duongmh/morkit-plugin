#!/usr/bin/env bash
# Deep Review plugin: one-time setup. Idempotent via marker file.
set -e

MARKER_DIR="${HOME}/.claude/deep-review"
MARKER="${MARKER_DIR}/.setup-done"
mkdir -p "${MARKER_DIR}"

if [ -f "${MARKER}" ]; then
  exit 0
fi

echo "🔧 Deep Review: first-time setup..."

# 1. Ensure uv (provides uvx)
if ! command -v uvx >/dev/null 2>&1; then
  echo "  📦 Installing uv (provides uvx)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 || {
    echo "  ⚠️  uv install failed. Install manually: https://docs.astral.sh/uv/"
    exit 0
  }
  export PATH="${HOME}/.cargo/bin:${HOME}/.local/bin:${PATH}"
fi

# 2. Pre-cache code-review-graph (best-effort)
echo "  📥 Pre-caching code-review-graph..."
uvx --quiet code-review-graph --version >/dev/null 2>&1 || true

# 3. Optional dependency notes
command -v gh  >/dev/null 2>&1 || echo "  ℹ️  Recommended: install GitHub CLI (gh) for PR diff fetching."
command -v git >/dev/null 2>&1 || { echo "  ❌ git not found — required."; exit 0; }

# 4. Build graph for current repo if it is a git repo and graph not present
if [ -d ".git" ] && [ ! -d ".code-review-graph" ]; then
  echo "  📊 Building code graph for current repo (one-time)..."
  uvx --quiet code-review-graph build 2>&1 | tail -3 || \
    echo "  ℹ️  Graph not built now; will build on first /deep-review."
fi

touch "${MARKER}"
echo "✅ Deep Review ready. Try: /deep-review <PR-number-or-diff>"
