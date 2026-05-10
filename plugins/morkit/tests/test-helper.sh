#!/usr/bin/env bash
# test-helper.sh — assertion helpers for morkit plugin tests.
# Sourced by every test-*.sh.
#
# Conventions:
#   - Each test-*.sh declares TEST_NAME and increments TEST_PASSED / TEST_FAILED
#     via the assert_* helpers.
#   - Tests run inside isolated_tmpdir() so cwd-side effects are sandboxed.
#   - Each test calls test_summary at the end and exit_with_status to set
#     correct exit code.

set -uo pipefail

[[ -n "${SPEC_TEST_HELPER_LOADED:-}" ]] && return 0
SPEC_TEST_HELPER_LOADED=1

TEST_PASSED=0
TEST_FAILED=0
TEST_NAME="${TEST_NAME:-unnamed}"

# ---------------------------------------------------------------------------
# Locate plugin root for tests (one dir up from tests/)
# ---------------------------------------------------------------------------
TEST_PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$TEST_PLUGIN_ROOT}"

# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
_pass() {
    TEST_PASSED=$((TEST_PASSED + 1))
    [[ -n "${TEST_VERBOSE:-}" ]] && echo "  ✓ $1"
    return 0
}

_fail() {
    TEST_FAILED=$((TEST_FAILED + 1))
    echo "  ✗ FAIL: $1" >&2
    return 0
}

# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------
assert_equal() {
    local actual="$1"
    local expected="$2"
    local msg="${3:-equal}"
    if [[ "$actual" == "$expected" ]]; then
        _pass "$msg"
    else
        _fail "$msg — expected '$expected', got '$actual'"
    fi
}

assert_not_equal() {
    local actual="$1"
    local unexpected="$2"
    local msg="${3:-not equal}"
    if [[ "$actual" != "$unexpected" ]]; then
        _pass "$msg"
    else
        _fail "$msg — got unexpected '$actual'"
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local msg="${3:-contains}"
    if [[ "$haystack" == *"$needle"* ]]; then
        _pass "$msg"
    else
        _fail "$msg — '$needle' not found in '$haystack'"
    fi
}

assert_not_contains() {
    local haystack="$1"
    local needle="$2"
    local msg="${3:-not contains}"
    if [[ "$haystack" != *"$needle"* ]]; then
        _pass "$msg"
    else
        _fail "$msg — '$needle' unexpectedly found"
    fi
}

assert_file_exists() {
    local f="$1"
    local msg="${2:-file exists: $f}"
    if [[ -f "$f" ]]; then
        _pass "$msg"
    else
        _fail "$msg — file missing: $f"
    fi
}

assert_file_not_exists() {
    local f="$1"
    local msg="${2:-file not exists: $f}"
    if [[ ! -f "$f" ]]; then
        _pass "$msg"
    else
        _fail "$msg — file unexpectedly exists: $f"
    fi
}

assert_dir_exists() {
    local d="$1"
    local msg="${2:-dir exists: $d}"
    if [[ -d "$d" ]]; then
        _pass "$msg"
    else
        _fail "$msg — dir missing: $d"
    fi
}

assert_dir_not_exists() {
    local d="$1"
    local msg="${2:-dir not exists: $d}"
    if [[ ! -d "$d" ]]; then
        _pass "$msg"
    else
        _fail "$msg — dir unexpectedly exists: $d"
    fi
}

# Run a command; assert exit code matches expected.
# Usage: assert_exit_code 0 "cmd" "msg"  OR  assert_exit_code "ne0" "cmd" "msg"
assert_exit_code() {
    local expected="$1"
    local cmd="$2"
    local msg="${3:-exit code}"
    local actual
    eval "$cmd" >/dev/null 2>&1
    actual=$?
    if [[ "$expected" == "ne0" ]]; then
        if [[ "$actual" -ne 0 ]]; then _pass "$msg (exit $actual)"; else _fail "$msg — expected non-zero, got $actual"; fi
    else
        if [[ "$actual" -eq "$expected" ]]; then _pass "$msg (exit $actual)"; else _fail "$msg — expected $expected, got $actual"; fi
    fi
}

# Capture stderr from a command, assert it contains a pattern.
assert_stderr_contains() {
    local cmd="$1"
    local pattern="$2"
    local msg="${3:-stderr contains}"
    local stderr
    stderr=$(eval "$cmd" 2>&1 >/dev/null || true)
    if [[ "$stderr" == *"$pattern"* ]]; then
        _pass "$msg"
    else
        _fail "$msg — pattern '$pattern' not in stderr: $stderr"
    fi
}

# Capture stdout from a command, assert it contains a pattern.
assert_stdout_contains() {
    local cmd="$1"
    local pattern="$2"
    local msg="${3:-stdout contains}"
    local stdout
    stdout=$(eval "$cmd" 2>/dev/null || true)
    if [[ "$stdout" == *"$pattern"* ]]; then
        _pass "$msg"
    else
        _fail "$msg — pattern '$pattern' not in stdout: $stdout"
    fi
}

# JSON path check via jq.
# Usage: assert_json_path '<json>' '.path.to' 'expected' 'msg'
assert_json_path() {
    local json="$1"
    local path="$2"
    local expected="$3"
    local msg="${4:-json path}"
    if ! command -v jq >/dev/null 2>&1; then
        _fail "$msg — jq missing"
        return
    fi
    local actual
    actual=$(printf '%s' "$json" | jq -r "$path" 2>/dev/null || echo '__ERR__')
    if [[ "$actual" == "$expected" ]]; then
        _pass "$msg"
    else
        _fail "$msg — jq '$path' expected '$expected', got '$actual'"
    fi
}

# ---------------------------------------------------------------------------
# Sandbox
# ---------------------------------------------------------------------------
isolated_tmpdir() {
    local tmp
    tmp="$(mktemp -d)" || return 1
    cd "$tmp" || return 1
    # Cleanup on exit
    # shellcheck disable=SC2064
    trap "rm -rf '$tmp'" EXIT
    echo "$tmp"
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
test_summary() {
    local total=$((TEST_PASSED + TEST_FAILED))
    if [[ "$TEST_FAILED" -eq 0 ]]; then
        echo "✓ $TEST_NAME — $TEST_PASSED/$total passed"
    else
        echo "✗ $TEST_NAME — $TEST_PASSED/$total passed, $TEST_FAILED failed" >&2
    fi
}

exit_with_status() {
    test_summary
    [[ "$TEST_FAILED" -eq 0 ]]
}
