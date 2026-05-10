#!/usr/bin/env bash
# test-scaffold-change.sh — tests for scripts/scaffold-change.sh
#
# Coverage: 15 cases (P/N/E/X tiers) per Appendix B § 1.

set -uo pipefail

TEST_NAME="scaffold-change"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=test-helper.sh
. "$HELPER_DIR/test-helper.sh"

SCAFFOLD="$TEST_PLUGIN_ROOT/scripts/scaffold-change.sh"

# ---------------------------------------------------------------------------
# Setup: fresh sandbox per test via subshell
# ---------------------------------------------------------------------------
run_in_sandbox() {
    (
        local tmp
        tmp="$(mktemp -d)"
        cd "$tmp" || exit 1
        "$@"
        local rc=$?
        cd /
        rm -rf "$tmp"
        exit $rc
    )
}

# ---------------------------------------------------------------------------
# Case 1.1 — happy path
# ---------------------------------------------------------------------------
case_1_1() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    bash "$SCAFFOLD" add-csv-export >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "1.1 exit 0"
    assert_dir_exists "morkit/output/spec/add-csv-export" "1.1 dir created"
    assert_file_exists "morkit/output/spec/add-csv-export/proposal.md" "1.1 proposal"
    assert_file_exists "morkit/output/spec/add-csv-export/design.md" "1.1 design"
    assert_file_exists "morkit/output/spec/add-csv-export/tasks.md" "1.1 tasks"
    assert_file_exists "morkit/output/spec/add-csv-export/.meta.json" "1.1 meta"
    assert_file_exists "morkit/output/spec/.morkit" "1.1 marker"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.2 — meta.json content
# ---------------------------------------------------------------------------
case_1_2() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    bash "$SCAFFOLD" add-csv-export >/dev/null 2>&1
    local meta; meta=$(cat morkit/output/spec/add-csv-export/.meta.json 2>/dev/null)
    assert_json_path "$meta" '.name' 'add-csv-export' "1.2 meta.name"
    assert_json_path "$meta" '.schema_version' '1' "1.2 meta.schema_version"
    local created; created=$(printf '%s' "$meta" | jq -r '.created_at' 2>/dev/null)
    [[ "$created" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]] && _pass "1.2 created_at ISO 8601" || _fail "1.2 created_at format: $created"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.3 — templates rendered
# ---------------------------------------------------------------------------
case_1_3() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    bash "$SCAFFOLD" add-csv-export >/dev/null 2>&1
    local proposal tasks design
    proposal=$(cat morkit/output/spec/add-csv-export/proposal.md)
    tasks=$(cat morkit/output/spec/add-csv-export/tasks.md)
    design=$(cat morkit/output/spec/add-csv-export/design.md)
    assert_contains "$proposal" "# add-csv-export" "1.3 proposal title"
    assert_contains "$tasks" "REQUIRED SUB-SKILL" "1.3 tasks header"
    assert_contains "$design" "## Tech Stack" "1.3 design tech stack"
    assert_not_contains "$proposal" "{{NAME}}" "1.3 proposal placeholder replaced"
    assert_not_contains "$tasks" "{{NAME}}" "1.3 tasks placeholder replaced"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.4 — invalid name (space)
# ---------------------------------------------------------------------------
case_1_4() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    local stderr
    stderr=$(bash "$SCAFFOLD" "my feature" 2>&1 >/dev/null)
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "1.4 exit non-zero (rc=$rc)" || _fail "1.4 expected non-zero exit"
    assert_contains "$stderr" "kebab-case" "1.4 stderr mentions kebab"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.5 — invalid name (uppercase)
# ---------------------------------------------------------------------------
case_1_5() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    bash "$SCAFFOLD" "AddFeature" 2>/dev/null
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "1.5 reject uppercase" || _fail "1.5 expected non-zero"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.6 — invalid name (leading digit)
# ---------------------------------------------------------------------------
case_1_6() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    bash "$SCAFFOLD" "1st-feature" 2>/dev/null
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "1.6 reject leading digit" || _fail "1.6 expected non-zero"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.7 — empty name
# ---------------------------------------------------------------------------
case_1_7() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    local stderr
    stderr=$(bash "$SCAFFOLD" "" 2>&1 >/dev/null)
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "1.7 reject empty" || _fail "1.7 expected non-zero"
    assert_contains "$stderr" "Usage" "1.7 stderr usage hint"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.8 — reserved name 'archive'
# ---------------------------------------------------------------------------
case_1_8() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    local stderr
    stderr=$(bash "$SCAFFOLD" archive 2>&1 >/dev/null)
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "1.8 reject reserved" || _fail "1.8 expected non-zero"
    assert_contains "$stderr" "reserved" "1.8 stderr mentions reserved"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.9 — already exists, no --force
# ---------------------------------------------------------------------------
case_1_9() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    local stderr
    stderr=$(bash "$SCAFFOLD" foo 2>&1 >/dev/null)
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "1.9 reject duplicate" || _fail "1.9 expected non-zero"
    assert_contains "$stderr" "already exists" "1.9 stderr mentions exists"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.10 — RSpec coexistence: pre-existing spec/ dir untouched
# ---------------------------------------------------------------------------
case_1_10() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    mkdir -p spec/models
    echo "# RSpec test" > spec/models/user_spec.rb
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "1.10 scaffold succeeds"
    assert_file_exists "spec/models/user_spec.rb" "1.10 RSpec untouched"
    assert_dir_exists "morkit/output/spec/foo" "1.10 plugin folder created"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.11 — MORKIT_ROOT env override
# ---------------------------------------------------------------------------
case_1_11() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    MORKIT_ROOT=mor/changes bash "$SCAFFOLD" foo >/dev/null 2>&1
    assert_dir_exists "mor/changes/foo" "1.11 honored MORKIT_ROOT"
    assert_dir_not_exists "morkit/output/spec/foo" "1.11 default path skipped"
    assert_file_exists "mor/changes/.morkit" "1.11 marker in custom path"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.12 — CLAUDE_PLUGIN_ROOT fallback (unset env)
# ---------------------------------------------------------------------------
case_1_12() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    env -u CLAUDE_PLUGIN_ROOT bash "$SCAFFOLD" foo >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "1.12 fallback resolves plugin root"
    assert_file_exists "morkit/output/spec/foo/proposal.md" "1.12 templates rendered"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.13 — atomic creation: existing partial folder is detected
# We simulate by pre-creating the target dir.
# ---------------------------------------------------------------------------
case_1_13() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    mkdir -p morkit/output/spec/foo
    bash "$SCAFFOLD" foo 2>/dev/null
    local rc=$?
    [[ "$rc" -ne 0 ]] && _pass "1.13 atomic refuses partial" || _fail "1.13 expected non-zero on existing dir"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.14 — macOS / Linux date both produce ISO 8601 (cross-platform smoke)
# ---------------------------------------------------------------------------
case_1_14() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    local meta_at; meta_at=$(jq -r '.created_at' morkit/output/spec/foo/.meta.json 2>/dev/null)
    [[ "$meta_at" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]] && _pass "1.14 ISO 8601 platform-agnostic" || _fail "1.14 bad timestamp: $meta_at"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 1.15 — --force overrides existing dir
# ---------------------------------------------------------------------------
case_1_15() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    echo "manual edit" > morkit/output/spec/foo/proposal.md
    bash "$SCAFFOLD" --force foo >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "1.15 --force succeeds"
    local proposal; proposal=$(cat morkit/output/spec/foo/proposal.md)
    assert_contains "$proposal" "# foo" "1.15 file replaced"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Case 1.16 — path with space (cross-platform safety)
# ---------------------------------------------------------------------------
case_1_16() {
    local tmp; tmp="$(mktemp -d)"
    local space_dir="$tmp/with space/sub"
    mkdir -p "$space_dir"
    cd "$space_dir" || return 1
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" 0 "1.16 scaffold succeeds in space-path"
    assert_dir_exists "morkit/output/spec/foo" "1.16 dir created"
    cd /; rm -rf "$tmp"
}

case_1_1
case_1_2
case_1_3
case_1_4
case_1_5
case_1_6
case_1_7
case_1_8
case_1_9
case_1_10
case_1_11
case_1_12
case_1_13
case_1_14
case_1_15
case_1_16

exit_with_status
