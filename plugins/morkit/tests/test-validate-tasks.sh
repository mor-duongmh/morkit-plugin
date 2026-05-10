#!/usr/bin/env bash
# test-validate-tasks.sh — tests for scripts/validate-tasks.sh
# Coverage: 15 cases per Appendix B § 3 (rules R1-R6).

set -uo pipefail

TEST_NAME="validate-tasks"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

VALIDATE="$TEST_PLUGIN_ROOT/scripts/validate-tasks.sh"

# Helpers to write canonical fixtures
write_valid_minimal() {
    local f="$1"
    cat > "$f" <<'EOF'
# foo — Implementation Tasks

> **For agentic workers:** REQUIRED SUB-SKILL: Use morkit:subagent-driven-development.

## Task 1: First

**Files:**

- Create: `a.txt`

**Steps:**

- [ ] Step one
- [ ] Step two

## Task 2: Second

**Files:**

- Modify: `b.txt`

- [ ] Step three
EOF
}

write_valid_full() {
    local f="$1"
    cat > "$f" <<'EOF'
# foo

> **For agentic workers:** REQUIRED SUB-SKILL: morkit:executing-plans.

## Task 1: Setup

**Files:**

- Create: `setup.sh`

- [ ] Test
- [ ] Implement
- [ ] Refactor

## Task 2: Build

**Files:**

- Create: `build.sh`

- [x] Done
- [ ] Pending

## Task 3: Deploy

**Files:**

- Modify: `deploy.sh`

- [ ] Step
EOF
}

# 3.1 — valid full
case_3_1() {
    local tmp; tmp="$(mktemp -d)"
    write_valid_full "$tmp/tasks.md"
    bash "$VALIDATE" "$tmp/tasks.md" >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "3.1 valid full passes"
    rm -rf "$tmp"
}

# 3.2 — valid minimal
case_3_2() {
    local tmp; tmp="$(mktemp -d)"
    write_valid_minimal "$tmp/tasks.md"
    bash "$VALIDATE" "$tmp/tasks.md" >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "3.2 valid minimal passes"
    rm -rf "$tmp"
}

# 3.3 — R1 missing header
case_3_3() {
    local tmp; tmp="$(mktemp -d)"
    cat > "$tmp/tasks.md" <<'EOF'
# foo

## Task 1: x

**Files:**

- Create: `a`

- [ ] s
- [ ] s
- [ ] s
EOF
    local stderr; stderr=$(bash "$VALIDATE" "$tmp/tasks.md" 2>&1 >/dev/null)
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "3.3 R1 fails" || _fail "3.3 R1 should fail"
    assert_contains "$stderr" "R1" "3.3 stderr identifies R1"
    rm -rf "$tmp"
}

# 3.4 — R2 missing task
case_3_4() {
    local tmp; tmp="$(mktemp -d)"
    cat > "$tmp/tasks.md" <<'EOF'
# foo

> **For agentic workers:** REQUIRED SUB-SKILL: x

Just a paragraph, no tasks.

- [ ] orphan checkbox
- [ ] orphan
- [ ] orphan
EOF
    bash "$VALIDATE" "$tmp/tasks.md" 2>/dev/null
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "3.4 R2 fails" || _fail "3.4 R2 should fail"
    rm -rf "$tmp"
}

# 3.5 — R3 task without Files
case_3_5() {
    local tmp; tmp="$(mktemp -d)"
    cat > "$tmp/tasks.md" <<'EOF'
# foo

> **For agentic workers:** REQUIRED SUB-SKILL: x

## Task 1: alpha

- [ ] step
- [ ] step
- [ ] step
EOF
    local stderr; stderr=$(bash "$VALIDATE" "$tmp/tasks.md" 2>&1 >/dev/null)
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "3.5 R3 fails" || _fail "3.5 R3 should fail"
    assert_contains "$stderr" "R3" "3.5 stderr R3"
    rm -rf "$tmp"
}

# 3.6 — R4 task without checkbox
case_3_6() {
    local tmp; tmp="$(mktemp -d)"
    cat > "$tmp/tasks.md" <<'EOF'
# foo

> **For agentic workers:** REQUIRED SUB-SKILL: x

## Task 1: alpha

**Files:**

- Create: `a`

just text, no checkboxes here.

## Task 2: bravo

**Files:**

- Modify: `b`

- [ ] one
- [ ] two
- [ ] three
EOF
    bash "$VALIDATE" "$tmp/tasks.md" 2>/dev/null
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "3.6 R4 fails" || _fail "3.6 R4 should fail"
    rm -rf "$tmp"
}

# 3.7 — R5 < 3 checkboxes total
case_3_7() {
    local tmp; tmp="$(mktemp -d)"
    cat > "$tmp/tasks.md" <<'EOF'
# foo

> **For agentic workers:** REQUIRED SUB-SKILL: x

## Task 1: alpha

**Files:**

- Create: `a`

- [ ] only one
EOF
    bash "$VALIDATE" "$tmp/tasks.md" 2>/dev/null
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "3.7 R5 fails" || _fail "3.7 R5 should fail"
    rm -rf "$tmp"
}

# 3.8 — partial done OK
case_3_8() {
    local tmp; tmp="$(mktemp -d)"
    cat > "$tmp/tasks.md" <<'EOF'
# foo

> **For agentic workers:** REQUIRED SUB-SKILL: x

## Task 1: alpha

**Files:**

- Create: `a`

- [x] done
- [ ] pending
- [x] done2
- [ ] pending2
EOF
    bash "$VALIDATE" "$tmp/tasks.md" >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "3.8 partial done passes"
    rm -rf "$tmp"
}

# 3.9 — nested checkboxes count
case_3_9() {
    local tmp; tmp="$(mktemp -d)"
    cat > "$tmp/tasks.md" <<'EOF'
# foo

> **For agentic workers:** REQUIRED SUB-SKILL: x

## Task 1: alpha

**Files:**

- Create: `a`

- [ ] outer
  - [ ] inner1
  - [ ] inner2
EOF
    bash "$VALIDATE" "$tmp/tasks.md" >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "3.9 nested count toward total"
    rm -rf "$tmp"
}

# 3.10 — CRLF line endings tolerated
case_3_10() {
    local tmp; tmp="$(mktemp -d)"
    write_valid_minimal "$tmp/tasks.md"
    # Convert to CRLF
    awk 'sub("$","\r")' "$tmp/tasks.md" > "$tmp/tasks-crlf.md"
    bash "$VALIDATE" "$tmp/tasks-crlf.md" >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "3.10 CRLF tolerated"
    rm -rf "$tmp"
}

# 3.11 — Unicode (Vietnamese) in task names
case_3_11() {
    local tmp; tmp="$(mktemp -d)"
    cat > "$tmp/tasks.md" <<'EOF'
# foo

> **For agentic workers:** REQUIRED SUB-SKILL: x

## Task 1: Tạo schema

**Files:**

- Create: `a`

- [ ] Bước một
- [ ] Bước hai
- [ ] Bước ba
EOF
    bash "$VALIDATE" "$tmp/tasks.md" >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "3.11 unicode UTF-8 OK"
    rm -rf "$tmp"
}

# 3.12 — large file < 1s (just smoke test exit 0)
case_3_12() {
    local tmp; tmp="$(mktemp -d)"
    {
        echo "# big"
        echo "> **For agentic workers:** REQUIRED SUB-SKILL: x"
        echo "## Task 1: big"
        echo "**Files:**"
        echo "- Create: a"
        for i in $(seq 1 1000); do
            echo "- [ ] step $i"
        done
    } > "$tmp/tasks.md"
    local start=$(date +%s)
    bash "$VALIDATE" "$tmp/tasks.md" >/dev/null 2>&1
    local rc=$?
    local elapsed=$(( $(date +%s) - start ))
    assert_equal "$rc" 0 "3.12 large file passes"
    [[ "$elapsed" -le 3 ]] && _pass "3.12 < 3s ($elapsed s)" || _fail "3.12 too slow ($elapsed s)"
    rm -rf "$tmp"
}

# 3.13 — --explain
case_3_13() {
    local out; out=$(bash "$VALIDATE" --explain 2>/dev/null)
    assert_contains "$out" "R1" "3.13 explain mentions R1"
    assert_contains "$out" "R6" "3.13 explain mentions R6"
}

# 3.14 — --rule R3 only
case_3_14() {
    local tmp; tmp="$(mktemp -d)"
    cat > "$tmp/tasks.md" <<'EOF'
just a paragraph
- [ ] a
- [ ] b
- [ ] c
EOF
    # Missing R1, R2, R3, R4 — full validate fails
    bash "$VALIDATE" "$tmp/tasks.md" 2>/dev/null
    local full_rc=$?
    [[ "$full_rc" -ne 0 ]] && _pass "3.14 full fails" || _fail "3.14 expected full fail"
    # Only check R5 — should pass (3 checkboxes)
    bash "$VALIDATE" --rule R5 "$tmp/tasks.md" 2>/dev/null
    local r5_rc=$?
    assert_equal "$r5_rc" 0 "3.14 --rule R5 only passes"
    rm -rf "$tmp"
}

# 3.15 — file not found
case_3_15() {
    bash "$VALIDATE" "/nonexistent/tasks.md" 2>/dev/null
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "3.15 nonexistent fails" || _fail "3.15 should fail"
}

case_3_1
case_3_2
case_3_3
case_3_4
case_3_5
case_3_6
case_3_7
case_3_8
case_3_9
case_3_10
case_3_11
case_3_12
case_3_13
case_3_14
case_3_15

exit_with_status
