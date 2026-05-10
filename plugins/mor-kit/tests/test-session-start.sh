#!/usr/bin/env bash
# test-session-start.sh — tests for hooks/session-start.sh
# Coverage: 5 cases per Appendix B § 8.

set -uo pipefail

TEST_NAME="session-start"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

HOOK="$TEST_PLUGIN_ROOT/hooks/session-start.sh"

# 8.1 — legacy openspec/changes/ residual → suggest migration
case_8_1() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p openspec/changes/foo
    local out; out=$(bash "$HOOK" 2>/dev/null)
    assert_contains "$out" "spec-migration-suggestion" "8.1 emits migration suggestion"
    cd /; rm -rf "$tmp"
}

# 8.2 — already migrated (mor-kit/changes/ exists) → quiet
case_8_2() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p mor-kit/changes/foo
    mkdir -p openspec/changes/foo  # both — should NOT suggest because primary exists
    local out; out=$(bash "$HOOK" 2>/dev/null)
    assert_not_contains "$out" "spec-migration-suggestion" "8.2 quiet when migrated"
    cd /; rm -rf "$tmp"
}

# 8.3 — clean project (neither folder) → quiet
case_8_3() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    local out; out=$(bash "$HOOK" 2>/dev/null)
    assert_not_contains "$out" "spec-migration-suggestion" "8.3 quiet on clean"
    cd /; rm -rf "$tmp"
}

# 8.4 — RSpec project (spec/ but no mor-kit/changes/) → quiet
case_8_4() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p spec/models
    echo "# rspec" > spec/models/x_spec.rb
    local out; out=$(bash "$HOOK" 2>/dev/null)
    assert_not_contains "$out" "spec-migration-suggestion" "8.4 RSpec coexistence quiet"
    cd /; rm -rf "$tmp"
}

# 8.5 — skip marker mutes
case_8_5() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p openspec/changes/foo
    touch openspec/.spec-migration-skip
    local out; out=$(bash "$HOOK" 2>/dev/null)
    assert_not_contains "$out" "spec-migration-suggestion" "8.5 skip marker mutes"
    cd /; rm -rf "$tmp"
}

case_8_1
case_8_2
case_8_3
case_8_4
case_8_5

exit_with_status
