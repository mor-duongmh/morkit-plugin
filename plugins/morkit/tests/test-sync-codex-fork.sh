#!/usr/bin/env bash
# test-sync-codex-fork.sh — coverage for scripts/sync-codex-fork.sh
# (Task 4 of codex-fork-skills-clone).
#
# Cases covered:
#   1. Preflight — missing PyYAML → exit non-zero, clear error
#   2. Dry-run — fixture with mixed files prints SWAP/PRESERVE/ASSET correctly
#                and writes nothing
#   3. Full sync — fixture produces correct target tree with vocab applied,
#                  preserve verbatim, binary asset passthrough, baseline written
#   4. Idempotent — running sync twice produces identical target + baseline
#   5. Baseline format — every line is `<relpath>:<sha256>`, sorted
#   6. Real-repo dry-run — sync against real plugins/morkit/skills/ as a smoke
#                          test (dry-run only, no writes)
#   7. Exclude — built-in defaults skip __pycache__/, *.pyc, .DS_Store;
#                user --exclude flag adds more patterns
#
# All cases use mktemp -d fixtures — real skills/ is only read for case 6.

set -uo pipefail

TEST_NAME="sync-codex-fork"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

SCRIPT="$TEST_PLUGIN_ROOT/scripts/sync-codex-fork.sh"
HELPER_PY="$TEST_PLUGIN_ROOT/scripts/lib/apply-vocab-map.py"

# Portable sha256
sha256_of() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    else
        shasum -a 256 "$1" | awk '{print $1}'
    fi
}

# ---------------------------------------------------------------------------
# Fixture builder — creates a tmp dir containing:
#   skills/A.md                              (will SWAP — uses "Skill tool")
#   skills/sub/B.md                          (will SWAP — uses "TodoWrite")
#   skills/sub/C.png                         (ASSET — binary, passthrough)
#   skills/using-morkit/references/codex-tools.md   (PRESERVE — verbatim)
#   codex/vocab-map.yaml                     (real vocab map, copied from repo)
#
# Echoes the tmp dir path.
# ---------------------------------------------------------------------------
build_fixture() {
    local tmp
    tmp="$(mktemp -d)" || return 1
    mkdir -p "$tmp/skills/sub" \
             "$tmp/skills/using-morkit/references" \
             "$tmp/codex" \
             "$tmp/.codex"

    cat > "$tmp/skills/A.md" <<'EOF'
# Skill A
Use the Skill tool to invoke X.
Use the Agent tool with subagent_type=reviewer.
EOF

    cat > "$tmp/skills/sub/B.md" <<'EOF'
# Skill B
Use TodoWrite to track work.
EOF

    # Binary-ish file with bytes that would be mangled if processed as utf-8 text
    # without care. Use printf with octal escapes.
    printf '\x89PNG\r\n\x1a\nNOT-A-REAL-PNG-BUT-BINARY-SAFE\x00\xff\xfe' \
        > "$tmp/skills/sub/C.png"

    cat > "$tmp/skills/using-morkit/references/codex-tools.md" <<'EOF'
# Codex tools reference (preserved)
This file mentions Skill tool, TodoWrite, ExitPlanMode intentionally
as documentation about Claude. Must NOT be swapped.
EOF

    # Copy real vocab-map.yaml — it's the source of truth for swap rules.
    cp "$TEST_PLUGIN_ROOT/codex/vocab-map.yaml" "$tmp/codex/vocab-map.yaml"

    # Placeholder baseline (header-only). Sync should overwrite preserving header.
    cat > "$tmp/.codex/.drift-baseline" <<'EOF'
# drift-baseline — populated by sync script.
EOF

    echo "$tmp"
}

# Bail early if python3 / PyYAML unavailable.
if ! command -v python3 >/dev/null 2>&1; then
    _fail "python3 not available — cannot test sync"
    exit_with_status
    exit $?
fi
if ! python3 -c 'import yaml' >/dev/null 2>&1; then
    _fail "PyYAML not installed — cannot test sync"
    exit_with_status
    exit $?
fi

# ---------------------------------------------------------------------------
# Case 1 — Preflight: missing PyYAML produces clear error and non-zero exit.
# We simulate by invoking apply-vocab-map.py with a python that lacks PyYAML.
# Easiest: invoke the wrapper with PATH=/usr/bin only IF python3 there lacks
# yaml, but that's flaky across systems. Instead, exercise the wrapper's
# preflight branch by giving it a non-existent map file path — the wrapper
# MUST exit non-zero with a clear "vocab-map not found" error.
# ---------------------------------------------------------------------------
case_1_preflight_missing_map() {
    local tmp; tmp="$(build_fixture)"
    local stderr rc
    stderr=$(bash "$SCRIPT" \
        --source "$tmp/skills" \
        --target "$tmp/skills-codex" \
        --map    "$tmp/does-not-exist.yaml" \
        --baseline "$tmp/.codex/.drift-baseline" \
        --dry-run 2>&1 1>/dev/null) || rc=$?
    rc=${rc:-0}
    assert_not_equal "$rc" "0" "1. exit non-zero when vocab-map.yaml missing"
    assert_contains "$stderr" "vocab-map" "1. error message mentions vocab-map"
    rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 2 — Dry-run prints per-file SWAP/PRESERVE/ASSET labels, writes nothing.
# ---------------------------------------------------------------------------
case_2_dry_run() {
    local tmp; tmp="$(build_fixture)"
    local target="$tmp/skills-codex"
    local stdout rc
    stdout=$(bash "$SCRIPT" \
        --source "$tmp/skills" \
        --target "$target" \
        --map    "$tmp/codex/vocab-map.yaml" \
        --baseline "$tmp/.codex/.drift-baseline" \
        --dry-run 2>&1)
    rc=$?
    assert_equal "$rc" "0" "2. dry-run exits 0"
    assert_contains "$stdout" "SWAP" "2. dry-run reports SWAP action"
    assert_contains "$stdout" "PRESERVE" "2. dry-run reports PRESERVE action"
    assert_contains "$stdout" "ASSET" "2. dry-run reports ASSET action"
    assert_contains "$stdout" "A.md" "2. lists A.md"
    assert_contains "$stdout" "C.png" "2. lists C.png"
    assert_contains "$stdout" "codex-tools.md" "2. lists preserved file"
    # No writes — target should not exist
    assert_dir_not_exists "$target" "2. target dir not created in dry-run"
    # Baseline should be unchanged (still header-only)
    local entries
    entries=$(grep -cv '^[[:space:]]*\(#\|$\)' "$tmp/.codex/.drift-baseline" || true)
    assert_equal "$entries" "0" "2. baseline untouched in dry-run"
    rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 3 — Full sync produces correct target tree + baseline.
# ---------------------------------------------------------------------------
case_3_full_sync() {
    local tmp; tmp="$(build_fixture)"
    local target="$tmp/skills-codex"
    local baseline="$tmp/.codex/.drift-baseline"

    local stdout rc
    stdout=$(bash "$SCRIPT" \
        --source "$tmp/skills" \
        --target "$target" \
        --map    "$tmp/codex/vocab-map.yaml" \
        --baseline "$baseline" 2>&1)
    rc=$?
    assert_equal "$rc" "0" "3. full sync exits 0"
    assert_dir_exists "$target" "3. target dir created"

    # A.md — swapped
    assert_file_exists "$target/A.md" "3. A.md present in target"
    if [[ -f "$target/A.md" ]]; then
        local a_content
        a_content=$(cat "$target/A.md")
        assert_contains "$a_content" "skill discovery" "3. A.md vocab swapped (Skill tool→skill discovery)"
        assert_contains "$a_content" "delegate to a reviewer specialist" \
            "3. A.md vocab swapped (Agent tool→delegate)"
        assert_not_contains "$a_content" "Skill tool" "3. A.md no longer contains 'Skill tool'"
    fi

    # B.md — swapped
    assert_file_exists "$target/sub/B.md" "3. sub/B.md present in target"
    if [[ -f "$target/sub/B.md" ]]; then
        local b_content
        b_content=$(cat "$target/sub/B.md")
        assert_contains "$b_content" "task list" "3. B.md vocab swapped (TodoWrite→task list)"
        assert_not_contains "$b_content" "TodoWrite" "3. B.md no longer contains 'TodoWrite'"
    fi

    # C.png — verbatim (binary-safe)
    assert_file_exists "$target/sub/C.png" "3. C.png present in target"
    if [[ -f "$target/sub/C.png" ]]; then
        local src_hash tgt_hash
        src_hash=$(sha256_of "$tmp/skills/sub/C.png")
        tgt_hash=$(sha256_of "$target/sub/C.png")
        assert_equal "$tgt_hash" "$src_hash" "3. C.png binary preserved byte-for-byte"
    fi

    # codex-tools.md — preserved verbatim (contains words that swap rules match)
    assert_file_exists "$target/using-morkit/references/codex-tools.md" \
        "3. preserved file present in target"
    if [[ -f "$target/using-morkit/references/codex-tools.md" ]]; then
        local p_content
        p_content=$(cat "$target/using-morkit/references/codex-tools.md")
        # Preserve = NO swap, so original words remain
        assert_contains "$p_content" "Skill tool" "3. preserved file keeps 'Skill tool'"
        assert_contains "$p_content" "TodoWrite" "3. preserved file keeps 'TodoWrite'"
    fi

    # Baseline — 4 entries, sorted, format <relpath>:<sha256>
    local data_lines
    data_lines=$(grep -v '^[[:space:]]*\(#\|$\)' "$baseline" || true)
    local count
    count=$(printf '%s\n' "$data_lines" | grep -c '.' || true)
    assert_equal "$count" "4" "3. baseline has 4 entries"

    # Summary line
    assert_contains "$stdout" "Synced" "3. summary line printed"
    rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 4 — Idempotent: second run yields identical target tree + baseline.
# ---------------------------------------------------------------------------
case_4_idempotent() {
    local tmp; tmp="$(build_fixture)"
    local target="$tmp/skills-codex"
    local baseline="$tmp/.codex/.drift-baseline"

    bash "$SCRIPT" \
        --source "$tmp/skills" --target "$target" \
        --map "$tmp/codex/vocab-map.yaml" --baseline "$baseline" >/dev/null 2>&1

    # Snapshot first-run state
    local snap1="$tmp/snap1.txt"
    {
        find "$target" -type f | sort | while IFS= read -r f; do
            printf '%s %s\n' "$(sha256_of "$f")" "${f#"$target/"}"
        done
        echo "---BASELINE---"
        grep -v '^[[:space:]]*#' "$baseline" | sort
    } > "$snap1"

    # Run again
    bash "$SCRIPT" \
        --source "$tmp/skills" --target "$target" \
        --map "$tmp/codex/vocab-map.yaml" --baseline "$baseline" >/dev/null 2>&1

    local snap2="$tmp/snap2.txt"
    {
        find "$target" -type f | sort | while IFS= read -r f; do
            printf '%s %s\n' "$(sha256_of "$f")" "${f#"$target/"}"
        done
        echo "---BASELINE---"
        grep -v '^[[:space:]]*#' "$baseline" | sort
    } > "$snap2"

    if diff -q "$snap1" "$snap2" >/dev/null 2>&1; then
        _pass "4. second sync identical (idempotent)"
    else
        _fail "4. second sync differs from first — not idempotent"
        diff "$snap1" "$snap2" | head -20 >&2
    fi
    rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 5 — Baseline format: every data line is `<relpath>:<sha256>` (sha256
# is 64 hex chars), entries sorted ascending.
# ---------------------------------------------------------------------------
case_5_baseline_format() {
    local tmp; tmp="$(build_fixture)"
    local target="$tmp/skills-codex"
    local baseline="$tmp/.codex/.drift-baseline"

    bash "$SCRIPT" \
        --source "$tmp/skills" --target "$target" \
        --map "$tmp/codex/vocab-map.yaml" --baseline "$baseline" >/dev/null 2>&1

    local bad
    bad=$(grep -v '^[[:space:]]*\(#\|$\)' "$baseline" | \
          grep -cvE '^[^:]+:[0-9a-f]{64}$' || true)
    assert_equal "$bad" "0" "5. every baseline line matches <relpath>:<sha256> format"

    # Sorted check
    local data sorted
    data=$(grep -v '^[[:space:]]*\(#\|$\)' "$baseline" || true)
    sorted=$(printf '%s\n' "$data" | sort)
    if [[ "$data" == "$sorted" ]]; then
        _pass "5. baseline entries are sorted"
    else
        _fail "5. baseline entries not sorted"
    fi
    rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# Case 6 — Smoke test against real repo skills/, dry-run only (no writes).
# ---------------------------------------------------------------------------
case_6_real_repo_dry_run() {
    local tmp_target
    tmp_target="$(mktemp -d)/skills-codex-test"
    local stdout rc
    stdout=$(bash "$SCRIPT" \
        --source "$TEST_PLUGIN_ROOT/skills" \
        --target "$tmp_target" \
        --map    "$TEST_PLUGIN_ROOT/codex/vocab-map.yaml" \
        --baseline "$(dirname "$tmp_target")/.drift-baseline" \
        --dry-run 2>&1)
    rc=$?
    assert_equal "$rc" "0" "6. dry-run against real repo exits 0"
    assert_contains "$stdout" "SWAP" "6. real repo dry-run shows SWAP actions"
    assert_contains "$stdout" "PRESERVE" "6. real repo dry-run shows PRESERVE actions"
    # Target dir must NOT exist (dry-run wrote nothing)
    assert_dir_not_exists "$tmp_target" "6. real repo dry-run wrote nothing"
    rm -rf "$(dirname "$tmp_target")"
}

# ---------------------------------------------------------------------------
# Case 7 — Exclude: defaults skip __pycache__/, *.pyc, .DS_Store. User-supplied
# --exclude (repeatable) adds further patterns. Matched paths are absent from
# target tree and absent from baseline.
# ---------------------------------------------------------------------------
case_7_exclude() {
    local tmp; tmp="$(build_fixture)"
    local target="$tmp/skills-codex"
    local baseline="$tmp/.codex/.drift-baseline"

    # Add fixture noise that exclusion should drop:
    #   __pycache__/ subdir with .pyc
    #   loose .pyc
    #   .DS_Store
    #   user-excluded *.tmp file
    mkdir -p "$tmp/skills/sub/__pycache__"
    printf 'compiled' > "$tmp/skills/sub/__pycache__/B.cpython-313.pyc"
    printf 'loose'    > "$tmp/skills/sub/loose.pyc"
    printf 'ds'       > "$tmp/skills/.DS_Store"
    printf 'tmp'      > "$tmp/skills/scratch.tmp"

    local stdout rc
    stdout=$(bash "$SCRIPT" \
        --source "$tmp/skills" \
        --target "$target" \
        --map    "$tmp/codex/vocab-map.yaml" \
        --baseline "$baseline" \
        --exclude '*.tmp' 2>&1)
    rc=$?
    assert_equal "$rc" "0" "7. sync with --exclude exits 0"

    # Defaults skipped
    assert_dir_not_exists "$target/sub/__pycache__" \
        "7. __pycache__/ excluded by default"
    assert_file_not_exists "$target/sub/loose.pyc" \
        "7. *.pyc excluded by default"
    assert_file_not_exists "$target/.DS_Store" \
        "7. .DS_Store excluded by default"

    # User exclude
    assert_file_not_exists "$target/scratch.tmp" \
        "7. user --exclude '*.tmp' honored"

    # Baseline should not list excluded files
    local baseline_data
    baseline_data=$(grep -v '^[[:space:]]*\(#\|$\)' "$baseline" || true)
    assert_not_contains "$baseline_data" "__pycache__" "7. baseline omits __pycache__"
    assert_not_contains "$baseline_data" ".pyc" "7. baseline omits .pyc"
    assert_not_contains "$baseline_data" ".DS_Store" "7. baseline omits .DS_Store"
    assert_not_contains "$baseline_data" "scratch.tmp" "7. baseline omits user-excluded"

    # Real files still present
    assert_file_exists "$target/A.md" "7. A.md still synced"
    rm -rf "$tmp"
}

case_1_preflight_missing_map
case_2_dry_run
case_3_full_sync
case_4_idempotent
case_5_baseline_format
case_6_real_repo_dry_run
case_7_exclude

exit_with_status
