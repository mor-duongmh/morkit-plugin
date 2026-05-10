#!/usr/bin/env bash
# test-e2e.sh — end-to-end smoke test exercising the full lifecycle:
#   scaffold → list → validate → checklist (mocked) → gate blocks → approve → gate allows → archive → migrate
# Network-dependent steps fall back to mocked checklist.

set -uo pipefail

TEST_NAME="e2e"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

SCAFFOLD="$TEST_PLUGIN_ROOT/scripts/scaffold-change.sh"
LIST="$TEST_PLUGIN_ROOT/scripts/list-changes.sh"
VALIDATE="$TEST_PLUGIN_ROOT/scripts/validate-tasks.sh"
GATE="$TEST_PLUGIN_ROOT/hooks/pre-tool-checklist-gate.sh"
MIG="$TEST_PLUGIN_ROOT/scripts/migrate-from-openspec.sh"

run_e2e() {
    local tmp; tmp="$(mktemp -d)"; cd "$tmp" || return 1

    # --- Scaffold ---
    bash "$SCAFFOLD" add-csv-export >/dev/null 2>&1
    assert_dir_exists "morkit/output/spec/add-csv-export" "e2e: scaffold ok"

    # --- List ---
    local out; out=$(bash "$LIST" --json 2>/dev/null)
    local len; len=$(printf '%s' "$out" | jq 'length')
    assert_equal "$len" "1" "e2e: list has 1 entry"

    # --- Mock checklist (skip live fetch) — write a valid PENDING file ---
    cat > morkit/output/spec/add-csv-export/review-checklist.md <<'EOF'
# Review Checklist
- [ ] Items
Overall Decision: PENDING
EOF

    # --- Augment tasks.md so it passes validator ---
    cat > morkit/output/spec/add-csv-export/tasks.md <<'EOF'
# add-csv-export

> **For agentic workers:** REQUIRED SUB-SKILL: morkit:executing-plans

## Task 1: Setup

**Files:**

- Create: `setup.sh`

- [ ] Test
- [ ] Implement
- [ ] Refactor
EOF

    bash "$VALIDATE" morkit/output/spec/add-csv-export/tasks.md >/dev/null 2>&1
    assert_equal "$?" 0 "e2e: validate passes"

    # --- Gate blocks (PENDING) ---
    printf '%s' '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}' \
        | bash "$GATE" >/dev/null 2>&1
    [[ "$?" -ne 0 ]] && _pass "e2e: gate blocks PENDING" || _fail "e2e: gate should block"

    # --- Approve + gate allows ---
    sed -i.bak 's/Overall Decision: PENDING/Overall Decision: OK/' \
        morkit/output/spec/add-csv-export/review-checklist.md
    rm -f morkit/output/spec/add-csv-export/review-checklist.md.bak

    printf '%s' '{"tool_name":"Skill","tool_input":{"skill":"morkit:executing-plans"}}' \
        | bash "$GATE" >/dev/null 2>&1
    assert_equal "$?" 0 "e2e: gate allows after OK"

    # --- Archive ---
    mkdir -p morkit/output/spec/archive
    mv morkit/output/spec/add-csv-export morkit/output/spec/archive/add-csv-export
    assert_dir_exists "morkit/output/spec/archive/add-csv-export" "e2e: archived"
    assert_dir_not_exists "morkit/output/spec/add-csv-export" "e2e: active gone"

    # --- Migration smoke (separate scenario) ---
    cd /; rm -rf "$tmp"
    tmp="$(mktemp -d)"; cd "$tmp" || return 1
    mkdir -p openspec/changes/legacy
    echo "# legacy" > openspec/changes/legacy/proposal.md
    bash "$MIG" >/dev/null 2>&1
    assert_dir_exists "morkit/output/spec/legacy" "e2e: migration succeeded"
    assert_dir_not_exists "openspec/changes" "e2e: legacy removed"

    cd /; rm -rf "$tmp"
}

run_e2e

exit_with_status
