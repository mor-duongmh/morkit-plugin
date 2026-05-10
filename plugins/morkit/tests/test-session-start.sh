#!/usr/bin/env bash
# test-session-start.sh — tests for hooks/session-start.sh
#
# Hook is now minimal: only delegates to first-run-tools.sh. Migration
# suggestion was removed in v1 (was in v0 design).

set -uo pipefail

TEST_NAME="session-start"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

HOOK="$TEST_PLUGIN_ROOT/hooks/session-start.sh"

# 8.1 — Hook exits 0 cleanly even when first-run-tools fails or absent
case_8_1() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$HOOK" >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "8.1 hook exits 0 on clean project"
    cd /; rm -rf "$tmp"
}

# 8.2 — Hook does NOT emit migration suggestion (removed in v1)
case_8_2() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p openspec/changes/foo
    local out; out=$(bash "$HOOK" 2>/dev/null)
    assert_not_contains "$out" "spec-migration-suggestion" "8.2 no migration suggestion (removed)"
    cd /; rm -rf "$tmp"
}

# 8.3 — Hook does NOT block session (always exit 0)
case_8_3() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p openspec/changes/foo
    bash "$HOOK" >/dev/null 2>&1
    assert_equal "$?" 0 "8.3 hook exits 0 even with legacy openspec residual"
    cd /; rm -rf "$tmp"
}

case_8_1
case_8_2
case_8_3

exit_with_status
