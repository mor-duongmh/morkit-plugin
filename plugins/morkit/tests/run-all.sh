#!/usr/bin/env bash
# run-all.sh — discover and run every test-*.sh under this directory.
# Each test runs once in a subshell; final exit non-zero if any test failed.

set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

shopt -s nullglob
TESTS=( test-*.sh integration/test-*.sh )
shopt -u nullglob

if [[ "${#TESTS[@]}" -eq 0 ]]; then
    echo "No test files found."
    exit 1
fi

PASS=0
FAIL=0
FAILED_FILES=()

for t in "${TESTS[@]}"; do
    [[ -f "$t" ]] || continue
    # Capture combined output AND exit code in one pass via PIPESTATUS.
    output="$(bash "$t" 2>&1)"
    rc=$?
    # Print last line (test summary) regardless of pass/fail
    printf '%s\n' "$output" | tail -1
    if [[ "$rc" -eq 0 ]]; then
        PASS=$((PASS + 1))
    else
        FAIL=$((FAIL + 1))
        FAILED_FILES+=("$t")
        # On failure, echo the full output so CI logs show details
        echo "  --- output ---"
        printf '%s\n' "$output" | sed 's/^/    /'
        echo "  --- end output ---"
    fi
done

TOTAL=$((PASS + FAIL))
echo ""
echo "================================================"
echo "Test summary: $PASS/$TOTAL test files passed"
if [[ "$FAIL" -gt 0 ]]; then
    echo "Failed:"
    for f in "${FAILED_FILES[@]}"; do
        echo "  - $f"
    done
    exit 1
fi
echo "================================================"
