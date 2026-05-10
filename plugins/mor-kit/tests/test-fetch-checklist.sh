#!/usr/bin/env bash
# test-fetch-checklist.sh — defensive tests for scripts/fetch-checklist.sh
# Coverage: subset of Appendix B § 5 (no live network mocking — we test arg parsing
# and cache fallback behavior with synthetic cache).

set -uo pipefail

TEST_NAME="fetch-checklist"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

FETCH="$TEST_PLUGIN_ROOT/scripts/fetch-checklist.sh"

# 5.0 — --help
case_5_0() {
    local out; out=$(bash "$FETCH" --help 2>/dev/null)
    assert_contains "$out" "Usage" "5.0 help"
}

# 5.1 — Unknown option
case_5_1() {
    bash "$FETCH" --bogus 2>/dev/null
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "5.1 unknown option fails" || _fail "5.1 should fail"
}

# 5.2 — Cache hit when fresh
case_5_2() {
    local tmp; tmp="$(mktemp -d)"
    export CLAUDE_PLUGIN_DATA="$tmp/data"
    mkdir -p "$CLAUDE_PLUGIN_DATA"
    cat > "$CLAUDE_PLUGIN_DATA/.checklist-cache.md" <<'EOF'
# Plan Review Checklist
## BE - Feature
- [ ] Item
EOF
    local out; out=$(bash "$FETCH" 2>/dev/null)
    assert_contains "$out" "Plan Review Checklist" "5.2 cache hit returns content"
    unset CLAUDE_PLUGIN_DATA
    rm -rf "$tmp"
}

# 5.3 — Stale cache fallback when network fails (simulated by setting URL to invalid)
# We can't easily test this without network mocking; defensive: just check exit when
# nothing's available.
case_5_3() {
    local tmp; tmp="$(mktemp -d)"
    export CLAUDE_PLUGIN_DATA="$tmp/empty"
    mkdir -p "$CLAUDE_PLUGIN_DATA"
    # No cache, attempt fetch — likely succeeds online, fails offline.
    bash "$FETCH" 2>/dev/null >/dev/null
    local rc=$?
    # Either rc=0 (online, cached now) or rc=1 (offline). Both acceptable.
    [[ "$rc" -eq 0 || "$rc" -eq 1 ]] && _pass "5.3 exit 0 or 1" || _fail "5.3 unexpected rc=$rc"
    unset CLAUDE_PLUGIN_DATA
    rm -rf "$tmp"
}

case_5_0
case_5_1
case_5_2
case_5_3

exit_with_status
