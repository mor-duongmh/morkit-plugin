#!/usr/bin/env bash
# Sanity check that test-helper.sh assertions behave correctly.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helper.sh"

assert_equal "5.0.7" "5.0.7" "version equality"
assert_contains "hello world" "world" "substring"
echo "PASS: test-helper-sanity"
