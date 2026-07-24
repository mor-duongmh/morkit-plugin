#!/usr/bin/env bash
# test-r7-status.sh — tests for R7 (soft/back-compat task-level Status line)
# in scripts/validate-tasks.sh.
# Coverage: 3 cases — all-present, all-missing, mixed per-block detection.

set -uo pipefail

TEST_NAME="r7-status"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

VALIDATE="$TEST_PLUGIN_ROOT/scripts/validate-tasks.sh"

# Fixture A — every Task block has a valid Status line.
write_fixture_a() {
    local f="$1"
    cat > "$f" <<'EOF'
# foo — Implementation Tasks

> **For agentic workers:** REQUIRED SUB-SKILL: Use morkit:subagent-driven-development.

## Task 1: First

**Status:** pending

**Files:**

- Create: `a.txt`

- [ ] Step one
- [ ] Step two

## Task 2: Second

**Status:** done

**Files:**

- Modify: `b.txt`

- [ ] Step three
EOF
}

# Fixture B — identical, but no Status lines anywhere.
write_fixture_b() {
    local f="$1"
    cat > "$f" <<'EOF'
# foo — Implementation Tasks

> **For agentic workers:** REQUIRED SUB-SKILL: Use morkit:subagent-driven-development.

## Task 1: First

**Files:**

- Create: `a.txt`

- [ ] Step one
- [ ] Step two

## Task 2: Second

**Files:**

- Modify: `b.txt`

- [ ] Step three
EOF
}

# Fixture C — mixed: Task 1 has Status, Task 2 is missing it.
write_fixture_c() {
    local f="$1"
    cat > "$f" <<'EOF'
# foo — Implementation Tasks

> **For agentic workers:** REQUIRED SUB-SKILL: Use morkit:subagent-driven-development.

## Task 1: First

**Status:** pending

**Files:**

- Create: `a.txt`

- [ ] Step one
- [ ] Step two

## Task 2: Second

**Files:**

- Modify: `b.txt`

- [ ] Step three
EOF
}

# 1 — fixture A (Status present in all blocks): passes, no R7 warning
case_1() {
    local tmp; tmp="$(mktemp -d)"
    write_fixture_a "$tmp/tasks.md"
    local stderr; stderr=$(bash "$VALIDATE" "$tmp/tasks.md" 2>&1 >/dev/null)
    local rc=$?
    assert_equal "$rc" 0 "1 fixture A (Status present) exits 0"
    assert_not_contains "$stderr" "R7" "1 fixture A stderr has no R7 warning"
    rm -rf "$tmp"
}

# 2 — fixture B (Status missing everywhere): still passes (soft), R7 warning present
case_2() {
    local tmp; tmp="$(mktemp -d)"
    write_fixture_b "$tmp/tasks.md"
    local stderr; stderr=$(bash "$VALIDATE" "$tmp/tasks.md" 2>&1 >/dev/null)
    local rc=$?
    assert_equal "$rc" 0 "2 fixture B (Status missing) exits 0 (soft)"
    assert_contains "$stderr" "R7" "2 fixture B stderr contains R7 warning"
    rm -rf "$tmp"
}

# 3 — fixture C (mixed): passes, R7 warning names the missing block (Task 2)
case_3() {
    local tmp; tmp="$(mktemp -d)"
    write_fixture_c "$tmp/tasks.md"
    local stderr; stderr=$(bash "$VALIDATE" "$tmp/tasks.md" 2>&1 >/dev/null)
    local rc=$?
    assert_equal "$rc" 0 "3 fixture C (mixed) exits 0 (soft)"
    assert_contains "$stderr" "R7" "3 fixture C stderr contains R7 warning"
    assert_contains "$stderr" "Task 2" "3 fixture C warning names the missing block (Task 2)"
    rm -rf "$tmp"
}

case_1
case_2
case_3

exit_with_status
