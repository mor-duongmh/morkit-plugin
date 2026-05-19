#!/usr/bin/env bash
# test-install-codex.sh — coverage for scripts/install-codex.sh
# (Task 8 of codex-fork-skills-clone).
#
# All cases use mktemp dirs for AGENTS_HOME / CODEX_HOME / HOME — real
# user home is never touched.
#
# Cases covered:
#   1. Fresh install (--yes, no hooks) → skills symlink + AGENTS.md
#      symlink + rc env block; reports skill count.
#   2. skills/ missing in plugin → script errors with helpful message
#      mentioning sync-codex-fork.sh.
#   3. --uninstall removes symlinks and rc block.
#   4. --with-hooks --yes creates ~/.codex/hooks.json as a symlink to
#      hooks.json (cross-repo updates propagate).
#   5. Idempotency: re-running install does not duplicate rc block and
#      leaves correct symlinks intact.

set -uo pipefail

TEST_NAME="install-codex"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

# Codex install script now lives in the sibling morkit-codex plugin (post-fix/codex-separate-plugin).
CODEX_PLUGIN_ROOT="$(cd "$TEST_PLUGIN_ROOT/../morkit-codex" && pwd)"
SCRIPT="$CODEX_PLUGIN_ROOT/scripts/install-codex.sh"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SANDBOXES=()
cleanup_sandboxes() {
    for s in "${SANDBOXES[@]:-}"; do [[ -n "$s" && -d "$s" ]] && rm -rf "$s"; done
}
trap cleanup_sandboxes EXIT

# Create an isolated test environment with its own HOME/AGENTS_HOME/CODEX_HOME
# and a staged plugin (so we can mutate it without affecting the real tree —
# e.g. for Case 2 we need to hide skills/).
#
# Echoes the path to a sandbox dir containing:
#   sandbox/home/            → HOME
#   sandbox/agents-home/     → AGENTS_HOME
#   sandbox/codex-home/      → CODEX_HOME
#   sandbox/plugin/          → staged plugin root (only the bits install needs)
make_sandbox() {
    local tmp
    tmp="$(mktemp -d)" || return 1
    mkdir -p "$tmp/home" "$tmp/agents-home" "$tmp/codex-home" "$tmp/plugin"

    # Stage just what install-codex.sh needs. Symlink large content back to
    # the real plugin (install-codex only READS these — it ln -s them into
    # AGENTS_HOME/CODEX_HOME). Tests that need to mutate (Case 2) swap them.
    mkdir -p "$tmp/plugin/scripts" "$tmp/plugin/hooks"
    cp "$CODEX_PLUGIN_ROOT/scripts/install-codex.sh" "$tmp/plugin/scripts/"
    ln -s "$CODEX_PLUGIN_ROOT/skills"          "$tmp/plugin/skills"
    ln -s "$CODEX_PLUGIN_ROOT/commands"        "$tmp/plugin/commands"
    ln -s "$CODEX_PLUGIN_ROOT/AGENTS.md"       "$tmp/plugin/AGENTS.md"
    ln -s "$CODEX_PLUGIN_ROOT/hooks/hooks.json" "$tmp/plugin/hooks/hooks.json"
    ln -s "$TEST_PLUGIN_ROOT/hooks/session-start.sh" "$tmp/plugin/hooks/session-start.sh"

    SANDBOXES+=("$tmp")
    echo "$tmp"
}

# Run install with sandboxed env. Args after $1 (sandbox) pass through to script.
run_install() {
    local sandbox="$1"; shift
    HOME="$sandbox/home" \
    AGENTS_HOME="$sandbox/agents-home" \
    CODEX_HOME="$sandbox/codex-home" \
    SHELL="/bin/bash" \
    bash "$sandbox/plugin/scripts/install-codex.sh" "$@" 2>&1
}

# ---------------------------------------------------------------------------
# Case 1: fresh install (no hooks)
# ---------------------------------------------------------------------------
echo "[case 1] fresh install symlinks skills/"
SANDBOX="$(make_sandbox)"
# Touch .bashrc so installer has an rc file to append to
touch "$SANDBOX/home/.bashrc"
OUT="$(run_install "$SANDBOX" --yes)"
RC=$?
assert_equal "$RC" "0" "install exits 0"

# Skill symlink points to skills/ (not skills/)
SKILL_LINK="$SANDBOX/agents-home/skills/morkit"
if [[ -L "$SKILL_LINK" ]]; then
    TARGET="$(readlink "$SKILL_LINK")"
    assert_contains "$TARGET" "skills" "skill symlink target ends in skills"
else
    _fail "skill symlink missing: $SKILL_LINK"
fi

# AGENTS.md symlinked into codex-home
assert_file_exists "$SANDBOX/codex-home/AGENTS.md" "AGENTS.md placed in codex-home"

# rc block appended
if grep -q "morkit-codex" "$SANDBOX/home/.bashrc" 2>/dev/null; then
    _pass "rc block appended"
else
    _fail "rc block not appended to .bashrc — output: $OUT"
fi

# Output mentions skill count
assert_contains "$OUT" "skills discovered" "summary reports skill count"

# ---------------------------------------------------------------------------
# Case 2: skills/ missing → helpful error
# ---------------------------------------------------------------------------
echo "[case 2] missing skills/ shows sync-codex-fork.sh hint"
SANDBOX="$(make_sandbox)"
rm "$SANDBOX/plugin/skills"  # remove the symlink so dir is missing

OUT="$(run_install "$SANDBOX" --yes 2>&1)"
RC=$?
assert_not_equal "$RC" "0" "install fails when skills/ missing"
assert_contains "$OUT" "skills" "error mentions skills"
assert_contains "$OUT" "sync-codex-fork.sh" "error hints at sync-codex-fork.sh"

# ---------------------------------------------------------------------------
# Case 3: --uninstall cleanup
# ---------------------------------------------------------------------------
echo "[case 3] --uninstall removes symlinks + rc block"
SANDBOX="$(make_sandbox)"
touch "$SANDBOX/home/.bashrc"
run_install "$SANDBOX" --yes >/dev/null 2>&1

# Sanity: symlinks exist before uninstall
[[ -L "$SANDBOX/agents-home/skills/morkit" ]] || _fail "precondition: skill symlink should exist"

run_install "$SANDBOX" --uninstall >/dev/null 2>&1
RC=$?
assert_equal "$RC" "0" "uninstall exits 0"

assert_file_not_exists "$SANDBOX/agents-home/skills/morkit" "skill symlink removed"
if grep -q "morkit-codex" "$SANDBOX/home/.bashrc" 2>/dev/null; then
    _fail "rc block not removed by uninstall"
else
    _pass "rc block removed"
fi

# ---------------------------------------------------------------------------
# Case 4: --with-hooks symlinks ~/.codex/hooks.json to hooks.json
# ---------------------------------------------------------------------------
echo "[case 4] --with-hooks installs hooks.json from hooks.json"
SANDBOX="$(make_sandbox)"
touch "$SANDBOX/home/.bashrc"
OUT="$(run_install "$SANDBOX" --yes --with-hooks 2>&1)"
RC=$?
assert_equal "$RC" "0" "install --with-hooks exits 0"

HOOKS_JSON="$SANDBOX/codex-home/hooks.json"
assert_file_exists "$HOOKS_JSON" "hooks.json created"

# Verify it points to or contains hooks.json content (matcher is the proof)
if [[ -L "$HOOKS_JSON" ]]; then
    TARGET="$(readlink "$HOOKS_JSON")"
    assert_contains "$TARGET" "hooks.json" "hooks.json symlinked to hooks.json"
fi
# Whether symlinked or copied, content must include the PreToolUse matcher
CONTENT="$(cat "$HOOKS_JSON")"
assert_contains "$CONTENT" "apply_patch|Edit|Write" "hooks.json includes pre-tool matcher"

# ---------------------------------------------------------------------------
# Case 5: idempotency — re-run install does not duplicate rc block
# ---------------------------------------------------------------------------
echo "[case 5] re-running install is idempotent"
SANDBOX="$(make_sandbox)"
touch "$SANDBOX/home/.bashrc"
run_install "$SANDBOX" --yes >/dev/null 2>&1
run_install "$SANDBOX" --yes >/dev/null 2>&1
RC=$?
assert_equal "$RC" "0" "second install exits 0"

BLOCK_COUNT="$(grep -c "# >>> morkit-codex >>>" "$SANDBOX/home/.bashrc" 2>/dev/null || echo 0)"
assert_equal "$BLOCK_COUNT" "1" "rc block appears exactly once"

# Skill symlink still points at skills/
if [[ -L "$SANDBOX/agents-home/skills/morkit" ]]; then
    TARGET="$(readlink "$SANDBOX/agents-home/skills/morkit")"
    assert_contains "$TARGET" "skills" "skill symlink still targets skills after re-run"
else
    _fail "skill symlink missing after re-run"
fi

# ---------------------------------------------------------------------------
# Case 6: --uninstall removes hooks.json symlink installed via --with-hooks
# ---------------------------------------------------------------------------
echo "[case 6] --uninstall removes hooks.json symlink (with-hooks scenario)"
SANDBOX="$(make_sandbox)"
touch "$SANDBOX/home/.bashrc"
run_install "$SANDBOX" --yes --with-hooks >/dev/null 2>&1

# Sanity: hooks.json symlink exists before uninstall
HOOKS_JSON="$SANDBOX/codex-home/hooks.json"
[[ -L "$HOOKS_JSON" ]] || _fail "precondition: hooks.json symlink should exist after --with-hooks install"

run_install "$SANDBOX" --uninstall >/dev/null 2>&1
RC=$?
assert_equal "$RC" "0" "uninstall (post --with-hooks) exits 0"

assert_file_not_exists "$HOOKS_JSON" "hooks.json symlink removed by uninstall"

# ---------------------------------------------------------------------------
exit_with_status
