#!/usr/bin/env bash
# test-pre-tool-gate.sh — tests for hooks/pre-tool-checklist-gate.sh
# Coverage: 17 cases per Appendix B § 7.

set -uo pipefail

TEST_NAME="pre-tool-gate"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

GATE="$TEST_PLUGIN_ROOT/hooks/pre-tool-checklist-gate.sh"
SCAFFOLD="$TEST_PLUGIN_ROOT/scripts/scaffold-change.sh"

# Helper: feed JSON to gate, return exit code
run_gate() {
    local input="$1"
    printf '%s' "$input" | bash "$GATE" >/dev/null 2>&1
}

run_gate_stderr() {
    local input="$1"
    printf '%s' "$input" | bash "$GATE" 2>&1 >/dev/null
}

# Setup: scaffold a change and approve its checklist
setup_approved_change() {
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    cat > mor-kit/changes/foo/review-checklist.md <<'EOF'
# Review Checklist
- [x] Items
Overall Decision: OK
EOF
}

setup_pending_change() {
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    cat > mor-kit/changes/foo/review-checklist.md <<'EOF'
# Review Checklist
- [ ] Items
Overall Decision: PENDING
EOF
}

setup_no_checklist() {
    bash "$SCAFFOLD" foo >/dev/null 2>&1
}

# 7.1 — superpowers:executing-plans + OK
case_7_1() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_approved_change
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"superpowers:executing-plans"}}'
    assert_equal "$?" 0 "7.1 superpowers:executing-plans allowed when OK"
    cd /; rm -rf "$tmp"
}

# 7.2 — old skill name spec:apply still works (transition)
case_7_2() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_approved_change
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"openspec-apply-change"}}'
    assert_equal "$?" 0 "7.2 legacy openspec-apply-change allowed"
    cd /; rm -rf "$tmp"
}

# 7.3 — superpowers:executing-plans
case_7_3() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_approved_change
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"superpowers:executing-plans"}}'
    assert_equal "$?" 0 "7.3 executing-plans allowed when OK"
    cd /; rm -rf "$tmp"
}

# 7.4 — PENDING blocks
case_7_4() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_pending_change
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"superpowers:executing-plans"}}'
    [[ "$?" -ne 0 ]] && _pass "7.4 PENDING blocks" || _fail "7.4 should block"
    cd /; rm -rf "$tmp"
}

# 7.5 — missing checklist blocks
case_7_5() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_no_checklist
    local stderr
    stderr=$(run_gate_stderr '{"tool_name":"Skill","tool_input":{"skill":"superpowers:executing-plans"}}')
    assert_contains "$stderr" "missing" "7.5 stderr mentions missing"
    cd /; rm -rf "$tmp"
}

# 7.6 — non-Skill tool fail-open
case_7_6() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_pending_change
    run_gate '{"tool_name":"Bash","tool_input":{"command":"ls"}}'
    assert_equal "$?" 0 "7.6 Bash tool fail-open"
    cd /; rm -rf "$tmp"
}

# 7.7 — unrelated skill fail-open
case_7_7() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_pending_change
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"mor-kit:propose"}}'
    assert_equal "$?" 0 "7.7 unrelated skill fail-open"
    cd /; rm -rf "$tmp"
}

# 7.8 — no mor-kit/changes folder fail-open
case_7_8() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"superpowers:executing-plans"}}'
    assert_equal "$?" 0 "7.8 no folder fail-open"
    cd /; rm -rf "$tmp"
}

# 7.9 — empty stdin fail-open
case_7_9() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    : | bash "$GATE" >/dev/null 2>&1
    assert_equal "$?" 0 "7.9 empty stdin fail-open"
    cd /; rm -rf "$tmp"
}

# 7.10 — malformed JSON fail-open
case_7_10() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    echo "not json" | bash "$GATE" >/dev/null 2>&1
    assert_equal "$?" 0 "7.10 malformed JSON fail-open"
    cd /; rm -rf "$tmp"
}

# 7.11 — multiple changes, only newest checked
case_7_11() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" old >/dev/null 2>&1
    cat > mor-kit/changes/old/review-checklist.md <<'EOF'
Overall Decision: OK
EOF
    sleep 1
    bash "$SCAFFOLD" newest >/dev/null 2>&1
    cat > mor-kit/changes/newest/review-checklist.md <<'EOF'
Overall Decision: PENDING
EOF
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"superpowers:executing-plans"}}'
    [[ "$?" -ne 0 ]] && _pass "7.11 newest used (PENDING blocks)" || _fail "7.11 should use newest"
    cd /; rm -rf "$tmp"
}

# 7.12 — archive subfolder skipped
case_7_12() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    mkdir -p mor-kit/changes/archive
    mv mor-kit/changes/foo mor-kit/changes/archive/foo
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"superpowers:executing-plans"}}'
    assert_equal "$?" 0 "7.12 only archive present → fail-open"
    cd /; rm -rf "$tmp"
}

# 7.13 — trailing whitespace tolerated in OK marker
case_7_13() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    printf "Overall Decision: OK   \n" > mor-kit/changes/foo/review-checklist.md
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"superpowers:executing-plans"}}'
    assert_equal "$?" 0 "7.13 trailing whitespace OK"
    cd /; rm -rf "$tmp"
}

# 7.14 — MOR_KIT_ROOT override
case_7_14() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    MOR_KIT_ROOT=mor/changes bash "$SCAFFOLD" foo >/dev/null 2>&1
    cat > mor/changes/foo/review-checklist.md <<'EOF'
Overall Decision: OK
EOF
    MOR_KIT_ROOT=mor/changes printf '%s' '{"tool_name":"Skill","tool_input":{"skill":"superpowers:executing-plans"}}' \
        | MOR_KIT_ROOT=mor/changes bash "$GATE" >/dev/null 2>&1
    assert_equal "$?" 0 "7.14 MOR_KIT_ROOT honored"
    cd /; rm -rf "$tmp"
}

# 7.15 — dual-read: legacy openspec/changes/ if no mor-kit/changes
case_7_15() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p openspec/changes/foo
    cat > openspec/changes/foo/review-checklist.md <<'EOF'
Overall Decision: OK
EOF
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"superpowers:executing-plans"}}'
    assert_equal "$?" 0 "7.15 dual-read legacy openspec OK"
    cd /; rm -rf "$tmp"
}

# 7.16 — dual-read: legacy openspec PENDING blocks
case_7_16() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p openspec/changes/foo
    cat > openspec/changes/foo/review-checklist.md <<'EOF'
Overall Decision: PENDING
EOF
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"superpowers:executing-plans"}}'
    [[ "$?" -ne 0 ]] && _pass "7.16 dual-read PENDING blocks" || _fail "7.16 should block"
    cd /; rm -rf "$tmp"
}

# 7.17 — subagent-driven-development gated
case_7_17() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_pending_change
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"superpowers:subagent-driven-development"}}'
    [[ "$?" -ne 0 ]] && _pass "7.17 subagent-driven-development blocked" || _fail "7.17 should block"
    cd /; rm -rf "$tmp"
}

# 7.18 — path with space (cross-platform safety)
case_7_18() {
    local tmp; tmp="$(mktemp -d)"
    local space_dir="$tmp/with space/proj"
    mkdir -p "$space_dir"
    cd "$space_dir" || return
    setup_approved_change
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"superpowers:executing-plans"}}'
    assert_equal "$?" 0 "7.18 space-path: gate allows OK"
    cd /; rm -rf "$tmp"
}

case_7_1
case_7_2
case_7_3
case_7_4
case_7_5
case_7_6
case_7_7
case_7_8
case_7_9
case_7_10
case_7_11
case_7_12
case_7_13
case_7_14
case_7_15
case_7_16
case_7_17
case_7_18

exit_with_status
