#!/usr/bin/env bash
# test-migrate-from-openspec.sh — tests for scripts/migrate-from-openspec.sh
# Coverage: 8 cases per Appendix B § 6.

set -uo pipefail

TEST_NAME="migrate-from-openspec"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

MIG="$TEST_PLUGIN_ROOT/scripts/migrate-from-openspec.sh"

# 6.1 — single change migrate
case_6_1() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p openspec/changes/foo
    echo "# proposal" > openspec/changes/foo/proposal.md
    bash "$MIG" >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "6.1 exit 0"
    assert_dir_exists "morkit/output/spec/foo" "6.1 migrated"
    assert_file_exists "morkit/output/spec/foo/proposal.md" "6.1 content preserved"
    assert_file_exists "morkit/output/spec/.morkit" "6.1 marker created"
    assert_dir_not_exists "openspec/changes" "6.1 legacy gone"
    cd /; rm -rf "$tmp"
}

# 6.2 — preserve archive subfolder
case_6_2() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p openspec/changes/active
    mkdir -p openspec/changes/archive/old
    bash "$MIG" >/dev/null 2>&1
    assert_dir_exists "morkit/output/spec/active" "6.2 active migrated"
    assert_dir_exists "morkit/output/spec/archive/old" "6.2 archive migrated"
    cd /; rm -rf "$tmp"
}

# 6.3 — empty no-op
case_6_3() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$MIG" >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "6.3 exit 0"
    assert_dir_not_exists "morkit/output/spec" "6.3 nothing created"
    cd /; rm -rf "$tmp"
}

# 6.4 — no openspec at all → no-op
case_6_4() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    local out; out=$(bash "$MIG" 2>/dev/null)
    assert_contains "$out" "nothing to migrate" "6.4 quiet no-op message"
    cd /; rm -rf "$tmp"
}

# 6.5 — conflict (both populated) → refuse
case_6_5() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p openspec/changes/foo
    mkdir -p morkit/output/spec/bar
    bash "$MIG" 2>/dev/null
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "6.5 refuses conflict" || _fail "6.5 should refuse"
    assert_dir_exists "openspec/changes/foo" "6.5 source unchanged"
    cd /; rm -rf "$tmp"
}

# 6.6 — --dry-run no FS writes
case_6_6() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p openspec/changes/foo
    bash "$MIG" --dry-run >/dev/null 2>&1
    assert_dir_exists "openspec/changes/foo" "6.6 source untouched"
    assert_dir_not_exists "morkit/output/spec" "6.6 dest not created"
    cd /; rm -rf "$tmp"
}

# 6.7 — --keep-openspec preserves dir
case_6_7() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p openspec/changes/foo
    mkdir -p openspec/specs       # extra subfolder besides changes
    bash "$MIG" --keep-openspec >/dev/null 2>&1
    assert_dir_exists "openspec" "6.7 openspec preserved"
    assert_dir_exists "morkit/output/spec/foo" "6.7 migrated"
    cd /; rm -rf "$tmp"
}

# 6.8 — primary exists but empty (no content) → migrate succeeds
case_6_8() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p openspec/changes/foo
    mkdir -p morkit/output/spec        # empty primary
    bash "$MIG" >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "6.8 empty primary OK"
    assert_dir_exists "morkit/output/spec/foo" "6.8 migrated"
    cd /; rm -rf "$tmp"
}

case_6_1
case_6_2
case_6_3
case_6_4
case_6_5
case_6_6
case_6_7
case_6_8

exit_with_status
