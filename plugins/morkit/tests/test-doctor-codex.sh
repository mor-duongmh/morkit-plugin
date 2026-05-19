#!/usr/bin/env bash
# test-doctor-codex.sh — coverage for scripts/doctor-codex.sh
# (Task 8 of codex-fork-skills-clone).
#
# Cases covered:
#   1. All artifacts present (symlink → skills/, AGENTS.md, env, hooks)
#      → 0 FAIL.
#   2. Symlink points at legacy skills/ (not skills/) → WARN
#      surfaces "expected skills".
#   3. hooks.json missing → WARN, not FAIL.
#   4. commands/ presence check appears in output when dir exists.
#   5. Drift check section surfaced (informational).

set -uo pipefail

TEST_NAME="doctor-codex"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

# Codex doctor script now lives in the sibling morkit-codex plugin.
CODEX_PLUGIN_ROOT="$(cd "$TEST_PLUGIN_ROOT/../morkit-codex" && pwd)"
SCRIPT="$CODEX_PLUGIN_ROOT/scripts/doctor-codex.sh"

# ---------------------------------------------------------------------------
# Sandbox builder — mirror layout used by test-install-codex.sh.
# ---------------------------------------------------------------------------
SANDBOXES=()
cleanup_sandboxes() {
    for s in "${SANDBOXES[@]:-}"; do [[ -n "$s" && -d "$s" ]] && rm -rf "$s"; done
}
trap cleanup_sandboxes EXIT

make_sandbox() {
    local tmp
    tmp="$(mktemp -d)" || return 1
    mkdir -p "$tmp/home" "$tmp/agents-home/skills" "$tmp/codex-home" "$tmp/plugin"
    mkdir -p "$tmp/plugin/scripts" "$tmp/plugin/hooks"

    # The doctor script reads from $PLUGIN_ROOT. Copy it + symlink the rest
    # of the plugin tree we need.
    cp "$CODEX_PLUGIN_ROOT/scripts/doctor-codex.sh"        "$tmp/plugin/scripts/"
    cp "$CODEX_PLUGIN_ROOT/scripts/codex-deep-review.sh"   "$tmp/plugin/scripts/" 2>/dev/null || true
    cp "$CODEX_PLUGIN_ROOT/scripts/codex-deep-review-aggregate.py" "$tmp/plugin/scripts/" 2>/dev/null || true
    cp "$TEST_PLUGIN_ROOT/scripts/check-codex-drift.sh"    "$tmp/plugin/scripts/" 2>/dev/null || true
    ln -s "$CODEX_PLUGIN_ROOT/skills"           "$tmp/plugin/skills"
    ln -s "$CODEX_PLUGIN_ROOT/commands"         "$tmp/plugin/commands"
    ln -s "$CODEX_PLUGIN_ROOT/AGENTS.md"        "$tmp/plugin/AGENTS.md"
    ln -s "$CODEX_PLUGIN_ROOT/hooks/hooks.json" "$tmp/plugin/hooks/hooks.json"

    SANDBOXES+=("$tmp")
    echo "$tmp"
}

# Run doctor with sandboxed env. Echoes combined stdout+stderr; sets last_rc.
last_rc=0
run_doctor() {
    local sandbox="$1"
    local out
    out=$(HOME="$sandbox/home" \
          AGENTS_HOME="$sandbox/agents-home" \
          CODEX_HOME="$sandbox/codex-home" \
          SHELL="/bin/bash" \
          MORKIT_PLUGIN_ROOT="$sandbox/plugin" \
          bash "$sandbox/plugin/scripts/doctor-codex.sh" 2>&1)
    last_rc=$?
    printf '%s' "$out"
}

# Standard setup: skill symlink → skills/, AGENTS.md, rc env, hooks.json
setup_healthy() {
    local sandbox="$1"
    ln -s "$sandbox/plugin/skills" "$sandbox/agents-home/skills/morkit"
    ln -s "$sandbox/plugin/AGENTS.md"    "$sandbox/codex-home/AGENTS.md"
    ln -s "$sandbox/plugin/hooks/hooks.json" "$sandbox/codex-home/hooks.json"
    cat > "$sandbox/home/.bashrc" <<RC
# >>> morkit-codex >>>
export MORKIT_PLUGIN_ROOT="$sandbox/plugin"
# <<< morkit-codex <<<
RC
}

# ---------------------------------------------------------------------------
# Case 1: healthy install → no FAIL
# ---------------------------------------------------------------------------
echo "[case 1] healthy install"
SANDBOX="$(make_sandbox)"
setup_healthy "$SANDBOX"
OUT="$(run_doctor "$SANDBOX")"

assert_contains "$OUT" "skills" "doctor mentions skills"
# FAIL count == 0 (script reports `FAIL:  N` in summary)
if printf '%s' "$OUT" | grep -qE "FAIL:[[:space:]]+0"; then
    _pass "no FAILs"
else
    _fail "expected FAIL: 0, output: $OUT"
fi

# ---------------------------------------------------------------------------
# Case 2: missing skill symlink → FAIL surfaced
# ---------------------------------------------------------------------------
# (Old Case 2 tested "wrong target skills/ vs skills-codex/" — no longer
# meaningful after fix/codex-separate-plugin since morkit-codex/skills/ is now
# the canonical default-convention name. Replaced with a missing-symlink check.)
echo "[case 2] missing skill symlink → FAIL surfaced"
SANDBOX="$(make_sandbox)"
# Set up everything EXCEPT the skill symlink
ln -s "$SANDBOX/plugin/AGENTS.md" "$SANDBOX/codex-home/AGENTS.md"
cat > "$SANDBOX/home/.bashrc" <<RC
# >>> morkit-codex >>>
export MORKIT_PLUGIN_ROOT="$SANDBOX/plugin"
# <<< morkit-codex <<<
RC

OUT="$(run_doctor "$SANDBOX")"
if printf '%s' "$OUT" | grep -qiE "FAIL.*skill|skill.*missing|missing.*install"; then
    _pass "doctor flags missing skill symlink"
else
    _fail "expected missing-symlink FAIL, got: $OUT"
fi

# ---------------------------------------------------------------------------
# Case 3: hooks.json missing → WARN, not FAIL
# ---------------------------------------------------------------------------
echo "[case 3] hooks.json missing → WARN only"
SANDBOX="$(make_sandbox)"
setup_healthy "$SANDBOX"
rm -f "$SANDBOX/codex-home/hooks.json"

OUT="$(run_doctor "$SANDBOX")"
assert_contains "$OUT" "hooks.json" "doctor mentions hooks.json"
# Missing hooks.json should not contribute to FAIL count.
# Allow other unrelated FAILs (e.g. missing optional deep-review pieces in
# this stripped sandbox) — but ensure none of them is about hooks.json.
if printf '%s' "$OUT" | grep -E "FAIL" | grep -qi "hooks.json"; then
    _fail "hooks.json missing should not be FAIL"
else
    _pass "hooks.json missing is treated as WARN"
fi

# ---------------------------------------------------------------------------
# Case 4: commands/ check present in output
# ---------------------------------------------------------------------------
echo "[case 4] commands/ presence reported"
SANDBOX="$(make_sandbox)"
setup_healthy "$SANDBOX"
OUT="$(run_doctor "$SANDBOX")"

assert_contains "$OUT" "commands" "doctor reports on commands/"

# ---------------------------------------------------------------------------
# Case 5: drift check surfaced
# ---------------------------------------------------------------------------
echo "[case 5] drift check surfaced"
SANDBOX="$(make_sandbox)"
setup_healthy "$SANDBOX"
OUT="$(run_doctor "$SANDBOX")"

# Doctor should mention drift check somewhere — at minimum echo the script
# name or the word "drift".
if printf '%s' "$OUT" | grep -qiE "drift"; then
    _pass "doctor surfaces drift check"
else
    _fail "expected drift check mention, got: $OUT"
fi

# ---------------------------------------------------------------------------
exit_with_status
