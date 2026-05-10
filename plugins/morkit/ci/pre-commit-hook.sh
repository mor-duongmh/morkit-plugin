#!/usr/bin/env bash
# Optional: install as .git/hooks/pre-commit to run deep-review on staged diff.
# This hook is OPT-IN and only warns; it never blocks the commit.
set -e

if ! command -v claude >/dev/null 2>&1; then
  exit 0
fi

DIFF=$(git diff --cached)
if [ -z "$DIFF" ]; then
  exit 0
fi

echo "🔍 Running deep-review on staged changes (warn-only)..."
echo "$DIFF" | claude --print "/morkit:deep-review --diff" || true
