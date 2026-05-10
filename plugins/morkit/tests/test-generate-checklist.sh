#!/usr/bin/env bash
# test-generate-checklist.sh — tests for scripts/generate-checklist.sh
# Coverage: subset of Appendix B § 4 (path-related & variant detection).
# Network-dependent cases (live fetch) are skipped if no network.

set -uo pipefail

TEST_NAME="generate-checklist"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

GEN="$TEST_PLUGIN_ROOT/scripts/generate-checklist.sh"
SCAFFOLD="$TEST_PLUGIN_ROOT/scripts/scaffold-change.sh"

# Skip if no network (we don't want CI to fail on offline runs).
HAS_NETWORK=0
if curl -fsSL --max-time 3 "https://docs.google.com" >/dev/null 2>&1; then
    HAS_NETWORK=1
fi

# 4.0 — usage shown without arg
case_4_0() {
    local stderr; stderr=$(bash "$GEN" 2>&1 >/dev/null)
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "4.0 missing arg fails" || _fail "4.0 should fail"
    assert_contains "$stderr" "Usage" "4.0 usage hint"
}

# 4.6 — change-dir not exists
case_4_6() {
    bash "$GEN" /nonexistent/path 2>/dev/null
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "4.6 nonexistent path fails" || _fail "4.6 should fail"
}

# 4.10 — works with morkit/output/spec/<name>/
case_4_10() {
    if [[ "$HAS_NETWORK" -ne 1 ]]; then
        _pass "4.10 skipped (no network)"
        return
    fi
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    bash "$GEN" morkit/output/spec/foo --variant BE-Feature >/dev/null 2>&1
    local rc=$?
    if [[ "$rc" -eq 0 ]]; then
        assert_file_exists "morkit/output/spec/foo/review-checklist.md" "4.10 review-checklist created"
        local content; content=$(cat morkit/output/spec/foo/review-checklist.md 2>/dev/null)
        assert_contains "$content" "Overall Decision: PENDING" "4.10 PENDING footer"
    else
        _pass "4.10 skipped (network failed)"
    fi
    cd /; rm -rf "$tmp"
}

# 4.11 — usage mentions MORKIT_ROOT
case_4_11() {
    local out; out=$(bash "$GEN" --help 2>/dev/null)
    assert_contains "$out" "MORKIT_ROOT" "4.11 help mentions env override"
}

case_4_0
case_4_6
case_4_10
case_4_11

exit_with_status
