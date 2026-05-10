#!/usr/bin/env bash
# test-list-changes.sh — tests for scripts/list-changes.sh
# Coverage: 12 cases per Appendix B § 2.

set -uo pipefail

TEST_NAME="list-changes"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

LIST="$TEST_PLUGIN_ROOT/scripts/list-changes.sh"
SCAFFOLD="$TEST_PLUGIN_ROOT/scripts/scaffold-change.sh"

# ---------------------------------------------------------------------------
# 2.1 — empty (no folder)
# ---------------------------------------------------------------------------
case_2_1() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    local out; out=$(bash "$LIST" --json 2>/dev/null)
    assert_equal "$out" "[]" "2.1 empty array"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# 2.2 — single change
# ---------------------------------------------------------------------------
case_2_2() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    local out; out=$(bash "$LIST" --json 2>/dev/null)
    local len; len=$(printf '%s' "$out" | jq 'length' 2>/dev/null)
    assert_equal "$len" "1" "2.2 length 1"
    assert_json_path "$out" '.[0].name' 'foo' "2.2 name"
    assert_json_path "$out" '.[0].archived' 'false' "2.2 archived flag"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# 2.3 — multiple changes, sort by mtime desc (newest first)
# ---------------------------------------------------------------------------
case_2_3() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" alpha >/dev/null 2>&1
    sleep 1
    bash "$SCAFFOLD" beta >/dev/null 2>&1
    sleep 1
    bash "$SCAFFOLD" gamma >/dev/null 2>&1
    local out; out=$(bash "$LIST" --json 2>/dev/null)
    assert_json_path "$out" '.[0].name' 'gamma' "2.3 newest first"
    assert_json_path "$out" '.[2].name' 'alpha' "2.3 oldest last"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# 2.4 — active vs archived split
# ---------------------------------------------------------------------------
case_2_4() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" active1 >/dev/null 2>&1
    bash "$SCAFFOLD" old1 >/dev/null 2>&1
    mkdir -p mor-kit/changes/archive
    mv mor-kit/changes/old1 mor-kit/changes/archive/old1
    local active; active=$(bash "$LIST" --json 2>/dev/null)
    local len; len=$(printf '%s' "$active" | jq 'length')
    assert_equal "$len" "1" "2.4 active count = 1"
    assert_json_path "$active" '.[0].name' 'active1' "2.4 active name"
    local all; all=$(bash "$LIST" --json --include-archived 2>/dev/null)
    local len2; len2=$(printf '%s' "$all" | jq 'length')
    assert_equal "$len2" "2" "2.4 with archived = 2"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# 2.5 — text format
# ---------------------------------------------------------------------------
case_2_5() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    local out; out=$(bash "$LIST" 2>/dev/null)
    assert_contains "$out" "foo" "2.5 text contains name"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# 2.6 — no mor-kit/changes/ dir → empty result, exit 0
# ---------------------------------------------------------------------------
case_2_6() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$LIST" --json >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" "0" "2.6 exit 0 when no folder"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# 2.7 — folder without .meta.json (warn, still list)
# ---------------------------------------------------------------------------
case_2_7() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    rm mor-kit/changes/foo/.meta.json
    local out; out=$(bash "$LIST" --json 2>/dev/null)
    local len; len=$(printf '%s' "$out" | jq 'length')
    assert_equal "$len" "1" "2.7 still listed"
    assert_json_path "$out" '.[0].meta_corrupt' 'true' "2.7 marked corrupt"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# 2.8 — corrupt .meta.json (graceful)
# ---------------------------------------------------------------------------
case_2_8() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    echo "{ broken json" > mor-kit/changes/foo/.meta.json
    bash "$LIST" --json 2>/dev/null >/dev/null
    local rc=$?
    assert_equal "$rc" "0" "2.8 exit 0 on corrupt meta"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# 2.9 — many entries (perf smoke; just check exit 0)
# ---------------------------------------------------------------------------
case_2_9() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    mkdir -p mor-kit/changes
    for i in $(seq 1 50); do
        mkdir -p "mor-kit/changes/item-$i"
        echo "{\"name\":\"item-$i\",\"created_at\":\"2026-01-01T00:00:00Z\",\"schema_version\":1,\"archived\":false}" \
            > "mor-kit/changes/item-$i/.meta.json"
    done
    touch mor-kit/changes/.mor-kit
    bash "$LIST" --json >/dev/null 2>&1
    local rc=$?
    assert_equal "$rc" "0" "2.9 50 entries succeeds"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# 2.10 — MOR_KIT_ROOT override
# ---------------------------------------------------------------------------
case_2_10() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    MOR_KIT_ROOT=mor/changes bash "$SCAFFOLD" foo >/dev/null 2>&1
    local out; out=$(MOR_KIT_ROOT=mor/changes bash "$LIST" --json 2>/dev/null)
    local len; len=$(printf '%s' "$out" | jq 'length')
    assert_equal "$len" "1" "2.10 honored env override"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# 2.11 — cross-platform stat (smoke; tests run on whichever OS)
# ---------------------------------------------------------------------------
case_2_11() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    local out; out=$(bash "$LIST" --json 2>/dev/null)
    local mtime; mtime=$(printf '%s' "$out" | jq -r '.[0].mtime')
    [[ "$mtime" =~ ^[0-9]+$ ]] && _pass "2.11 mtime is numeric epoch" || _fail "2.11 mtime invalid: $mtime"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# 2.12 — only archive, no active
# ---------------------------------------------------------------------------
case_2_12() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return
    bash "$SCAFFOLD" foo >/dev/null 2>&1
    mkdir -p mor-kit/changes/archive
    mv mor-kit/changes/foo mor-kit/changes/archive/
    local out; out=$(bash "$LIST" --json 2>/dev/null)
    assert_equal "$out" "[]" "2.12 active list empty when only archive"
    cd /; rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
case_2_1
case_2_2
case_2_3
case_2_4
case_2_5
case_2_6
case_2_7
case_2_8
case_2_9
case_2_10
case_2_11
case_2_12

exit_with_status
