#!/usr/bin/env bash
# Run every test-*.sh in this directory.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

failed=0
total=0
for test in "$SCRIPT_DIR"/test-*.sh; do
    [[ -x "$test" ]] || continue
    total=$((total + 1))
    if ! "$test"; then
        failed=$((failed + 1))
    fi
done

echo
echo "Tests: $((total - failed))/$total passed"
[[ "$failed" -eq 0 ]]
