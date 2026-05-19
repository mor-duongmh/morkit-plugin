#!/usr/bin/env bash
# test-pre-tool-gate.sh — tests for hooks/pre-tool-checklist-gate.sh
# Coverage: 17 base cases per Appendix B § 7, plus Codex multi-tool matcher cases.

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
    cat > morkit/output/spec/foo/review-checklist.md <<'EOF'
# Review Checklist
- [x] Items
Overall Decision: OK
EOF
}

setup_pending_change() {
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    cat > morkit/output/spec/foo/review-checklist.md <<'EOF'
# Review Checklist
- [ ] Items
Overall Decision: PENDING
EOF
}

setup_no_checklist() {
    bash "$SCAFFOLD" foo >/dev/null 2>&1
}

# 7.1 — morkit:executing-plans + OK
case_7_1() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_approved_change
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}'
    assert_equal "$?" 0 "7.1 morkit:executing-plans allowed when OK"
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

# 7.3 — morkit:executing-plans
case_7_3() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_approved_change
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}'
    assert_equal "$?" 0 "7.3 executing-plans allowed when OK"
    cd /; rm -rf "$tmp"
}

# 7.4 — PENDING blocks
case_7_4() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_pending_change
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}'
    [[ "$?" -ne 0 ]] && _pass "7.4 PENDING blocks" || _fail "7.4 should block"
    cd /; rm -rf "$tmp"
}

# 7.5 — missing checklist blocks
case_7_5() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_no_checklist
    local stderr
    stderr=$(run_gate_stderr '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}')
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
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"morkit:propose"}}'
    assert_equal "$?" 0 "7.7 unrelated skill fail-open"
    cd /; rm -rf "$tmp"
}

# 7.8 — no morkit/output/spec folder fail-open
case_7_8() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}'
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
    cat > morkit/output/spec/old/review-checklist.md <<'EOF'
Overall Decision: OK
EOF
    sleep 1
    bash "$SCAFFOLD" newest >/dev/null 2>&1
    cat > morkit/output/spec/newest/review-checklist.md <<'EOF'
Overall Decision: PENDING
EOF
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}'
    [[ "$?" -ne 0 ]] && _pass "7.11 newest used (PENDING blocks)" || _fail "7.11 should use newest"
    cd /; rm -rf "$tmp"
}

# 7.12 — archive subfolder skipped
case_7_12() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    mkdir -p morkit/output/spec/archive
    mv morkit/output/spec/foo morkit/output/spec/archive/foo
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}'
    assert_equal "$?" 0 "7.12 only archive present → fail-open"
    cd /; rm -rf "$tmp"
}

# 7.13 — trailing whitespace tolerated in OK marker
case_7_13() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    printf "Overall Decision: OK   \n" > morkit/output/spec/foo/review-checklist.md
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}'
    assert_equal "$?" 0 "7.13 trailing whitespace OK"
    cd /; rm -rf "$tmp"
}

# 7.14 — MORKIT_ROOT override
case_7_14() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    MORKIT_ROOT=mor/changes bash "$SCAFFOLD" foo >/dev/null 2>&1
    cat > mor/changes/foo/review-checklist.md <<'EOF'
Overall Decision: OK
EOF
    MORKIT_ROOT=mor/changes printf '%s' '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}' \
        | MORKIT_ROOT=mor/changes bash "$GATE" >/dev/null 2>&1
    assert_equal "$?" 0 "7.14 MORKIT_ROOT honored"
    cd /; rm -rf "$tmp"
}

# 7.15 — dual-read: legacy openspec/changes/ if no morkit/output/spec
case_7_15() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p openspec/changes/foo
    cat > openspec/changes/foo/review-checklist.md <<'EOF'
Overall Decision: OK
EOF
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}'
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
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}'
    [[ "$?" -ne 0 ]] && _pass "7.16 dual-read PENDING blocks" || _fail "7.16 should block"
    cd /; rm -rf "$tmp"
}

# 7.17 — subagent-driven-development gated
case_7_17() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_pending_change
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"morkit:subagent-driven-development"}}'
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
    run_gate '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}'
    assert_equal "$?" 0 "7.18 space-path: gate allows OK"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Codex multi-tool matcher cases (apply_patch / Edit / Write)
# Codex CLI has no `Skill` tool; gate keys off MORKIT_CURRENT_CHANGE env var.
# ---------------------------------------------------------------------------

# 7.19 — apply_patch + MORKIT_CURRENT_CHANGE unset → fail-open
case_7_19() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_pending_change
    # Explicitly clear env var so a leaked value can't pass the gate
    unset MORKIT_CURRENT_CHANGE
    printf '%s' '{"tool_name":"apply_patch","tool_input":{}}' \
        | bash "$GATE" >/dev/null 2>&1
    assert_equal "$?" 0 "7.19 apply_patch + no env → fail-open"
    cd /; rm -rf "$tmp"
}

# 7.20 — apply_patch + MORKIT_CURRENT_CHANGE=foo + OK → allowed
case_7_20() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_approved_change
    MORKIT_CURRENT_CHANGE=foo printf '%s' '{"tool_name":"apply_patch","tool_input":{}}' \
        | MORKIT_CURRENT_CHANGE=foo bash "$GATE" >/dev/null 2>&1
    assert_equal "$?" 0 "7.20 apply_patch + OK checklist → allowed"
    cd /; rm -rf "$tmp"
}

# 7.21 — apply_patch + MORKIT_CURRENT_CHANGE=foo + PENDING → blocks
case_7_21() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_pending_change
    MORKIT_CURRENT_CHANGE=foo printf '%s' '{"tool_name":"apply_patch","tool_input":{}}' \
        | MORKIT_CURRENT_CHANGE=foo bash "$GATE" >/dev/null 2>&1
    [[ "$?" -ne 0 ]] && _pass "7.21 apply_patch + PENDING → blocks" || _fail "7.21 should block"
    cd /; rm -rf "$tmp"
}

# 7.22 — Edit + MORKIT_CURRENT_CHANGE=foo + missing checklist → blocks with helpful msg
case_7_22() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_no_checklist
    local stderr
    stderr=$(MORKIT_CURRENT_CHANGE=foo printf '%s' '{"tool_name":"Edit","tool_input":{}}' \
        | MORKIT_CURRENT_CHANGE=foo bash "$GATE" 2>&1 >/dev/null)
    assert_contains "$stderr" "missing" "7.22 Edit + missing checklist → stderr mentions missing"
    cd /; rm -rf "$tmp"
}

# 7.23 — Write + MORKIT_CURRENT_CHANGE points to nonexistent change → fail-open
case_7_23() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_approved_change
    MORKIT_CURRENT_CHANGE=does-not-exist printf '%s' '{"tool_name":"Write","tool_input":{}}' \
        | MORKIT_CURRENT_CHANGE=does-not-exist bash "$GATE" >/dev/null 2>&1
    assert_equal "$?" 0 "7.23 Write + nonexistent change → fail-open"
    cd /; rm -rf "$tmp"
}

# 7.24 — Skill path takes precedence even when MORKIT_CURRENT_CHANGE is set
case_7_24() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_pending_change
    # Skill tool + env var set → Skill path runs (gate-relevant skill blocks on PENDING)
    MORKIT_CURRENT_CHANGE=foo printf '%s' '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}' \
        | MORKIT_CURRENT_CHANGE=foo bash "$GATE" >/dev/null 2>&1
    [[ "$?" -ne 0 ]] && _pass "7.24 Skill path precedence over env" || _fail "7.24 should block via Skill path"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Codex env-var validation cases — prevent path traversal + archive bypass.
# MORKIT_CURRENT_CHANGE must be a single innocuous change name.
# ---------------------------------------------------------------------------

# 7.25 — Path traversal: MORKIT_CURRENT_CHANGE=archive/old-change → fail-open with WARN
case_7_25() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    # Approved active change (would falsely allow if path traversal worked)
    setup_approved_change
    # Approved change buried in archive subfolder (the bypass target)
    mkdir -p morkit/output/spec/archive/old-change
    cat > morkit/output/spec/archive/old-change/review-checklist.md <<'EOF'
Overall Decision: OK
EOF
    local stderr
    stderr=$(MORKIT_CURRENT_CHANGE='archive/old-change' printf '%s' '{"tool_name":"apply_patch","tool_input":{}}' \
        | MORKIT_CURRENT_CHANGE='archive/old-change' bash "$GATE" 2>&1 >/dev/null)
    local rc=$?
    assert_equal "$rc" 0 "7.25 path traversal → fail-open"
    assert_contains "$stderr" "MORKIT_CURRENT_CHANGE must be a single change name" "7.25 stderr explains validation"
    cd /; rm -rf "$tmp"
}

# 7.26 — Literal "archive" blocked
case_7_26() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p morkit/output/spec/archive
    cat > morkit/output/spec/archive/review-checklist.md <<'EOF'
Overall Decision: OK
EOF
    MORKIT_CURRENT_CHANGE='archive' printf '%s' '{"tool_name":"Edit","tool_input":{}}' \
        | MORKIT_CURRENT_CHANGE='archive' bash "$GATE" >/dev/null 2>&1
    assert_equal "$?" 0 "7.26 literal 'archive' → fail-open"
    cd /; rm -rf "$tmp"
}

# 7.27 — Special chars (shell metacharacters) blocked
case_7_27() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    setup_approved_change
    local stderr
    stderr=$(MORKIT_CURRENT_CHANGE='foo bar; rm -rf /' printf '%s' '{"tool_name":"Write","tool_input":{}}' \
        | MORKIT_CURRENT_CHANGE='foo bar; rm -rf /' bash "$GATE" 2>&1 >/dev/null)
    local rc=$?
    assert_equal "$rc" 0 "7.27 special chars → fail-open"
    assert_contains "$stderr" "MORKIT_CURRENT_CHANGE must be a single change name" "7.27 stderr explains validation"
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
case_7_19
case_7_20
case_7_21
case_7_22
case_7_23
case_7_24
case_7_25
case_7_26
case_7_27

exit_with_status
