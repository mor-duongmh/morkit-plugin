#!/usr/bin/env bash
# Deep Review plugin: one-time setup. Idempotent via marker file.
set -e

MARKER_DIR="${HOME}/.claude/morkit:deep-review"
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

# 4. Decide whether to build the graph for the current repo (non-interactive at SessionStart).
#    Use the shared graph-status helper to make a sized decision:
#      - small repos    → auto-build now
#      - larger repos   → defer to /morkit:deep-review which can prompt the user
#      - graph present  → skip
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATUS_OUT=$("${SCRIPT_DIR}/graph-status.sh" 2>/dev/null || true)

eval_kv() { echo "$STATUS_OUT" | awk -F= -v k="$1" '$1==k {print $2; exit}'; }

GIT_REPO=$(eval_kv git_repo)
GRAPH_PRESENT=$(eval_kv graph_present)
FILE_COUNT=$(eval_kv file_count)
EST_SEC=$(eval_kv estimated_build_seconds)
REC=$(eval_kv recommendation)

if [ "${GIT_REPO}" = "true" ]; then
  if [ "${GRAPH_PRESENT}" = "true" ]; then
    echo "  ✅ Graph already built for this repo (${FILE_COUNT} files indexed)."
  else
    case "${REC}" in
      auto-build)
        echo "  📊 Building code graph for this repo (${FILE_COUNT} files, ~${EST_SEC}s)..."
        uvx --quiet code-review-graph build 2>&1 | tail -3 || \
          echo "  ℹ️  Graph not built now; will retry on first /morkit:deep-review."
        ;;
      prompt-user|prompt-user-large)
        echo "  ⚠️  Repo is large (${FILE_COUNT} files, est. ~${EST_SEC}s build)."
        echo "     Skipping auto-build. /morkit:deep-review will ask before building."
        ;;
      *)
        echo "  ℹ️  Graph build deferred. Run /morkit:deep-review when ready."
        ;;
    esac
  fi
else
  echo "  ℹ️  Not in a git repo — graph build skipped. cd into a repo and run /morkit:deep-review."
fi

touch "${MARKER}"
echo "✅ Deep Review ready. Try: /morkit:deep-review <PR-number-or-diff>"
