#!/usr/bin/env bash
# Deep Review: graph status + build-time estimate.
# Output (stdout) is structured key=value lines for easy parsing by the SKILL:
#   git_repo=true|false
#   graph_present=true|false
#   file_count=<N>
#   estimated_build_seconds=<N>
#   recommendation=<auto-build|prompt-user|skip|not-applicable>
#
# Heuristics (from code-review-graph benchmarks):
#   ~10s for 500 files → ~0.02s per file
#   Non-linear due to edges → use 0.025s/file + 5s overhead, cap at file count.

set -u

print_kv() { printf "%s=%s\n" "$1" "$2"; }

# 1. Git repo?
if [ ! -d ".git" ]; then
  print_kv git_repo false
  print_kv graph_present false
  print_kv file_count 0
  print_kv estimated_build_seconds 0
  print_kv recommendation not-applicable
  exit 0
fi
print_kv git_repo true

# 2. Graph present?
if [ -d ".code-review-graph" ]; then
  print_kv graph_present true
  print_kv recommendation skip
  # File count is informational only when graph already present.
  N=$(git ls-files 2>/dev/null | wc -l | tr -d ' ')
  print_kv file_count "${N:-0}"
  print_kv estimated_build_seconds 0
  exit 0
fi
print_kv graph_present false

# 3. File count
N=$(git ls-files 2>/dev/null | wc -l | tr -d ' ')
N=${N:-0}
print_kv file_count "$N"

# 4. Estimate build time (in seconds, integer)
#    Formula: 5 + ceil(N * 0.025), with a floor of 3.
EST=$(awk -v n="$N" 'BEGIN { v = 5 + (n * 0.025); if (v < 3) v = 3; printf "%d\n", (v == int(v) ? v : int(v)+1) }')
print_kv estimated_build_seconds "$EST"

# 5. Recommendation
#    < 1500 files (≈ < 45s) → auto-build silently
#    1500–8000 files (≈ 45s–3.5min) → prompt user
#    > 8000 files → prompt user with strong warning
if   [ "$N" -lt 1500 ]; then
  print_kv recommendation auto-build
elif [ "$N" -lt 8000 ]; then
  print_kv recommendation prompt-user
else
  print_kv recommendation prompt-user-large
fi
