#!/usr/bin/env bash
# test-docs-codex.sh — coverage for AGENTS.md + .codex/INSTALL.md updates
# (Task 9 of codex-fork-skills-clone).
#
# Documentation-only checks: the two user-facing docs must reflect the
# sibling-folder fork architecture (skills-codex/, commands-codex/,
# hooks-codex.json) introduced by Tasks 5-8.
#
# Cases covered:
#   1. AGENTS.md references commands-codex/ (slash-command bridge updated).
#   2. AGENTS.md mentions ${MORKIT_PLUGIN_ROOT} as canonical env var.
#   3. AGENTS.md surfaces the drift-detection script.
#   4. .codex/INSTALL.md symlink step targets skills-codex (not skills).
#   5. .codex/INSTALL.md documents --with-hooks installer flag.
#   6. .codex/INSTALL.md surfaces sync-codex-fork.sh for bootstrap recovery.

set -uo pipefail

TEST_NAME="docs-codex"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

AGENTS_MD="$TEST_PLUGIN_ROOT/AGENTS.md"
INSTALL_MD="$TEST_PLUGIN_ROOT/.codex/INSTALL.md"

assert_file_exists "$AGENTS_MD"  "AGENTS.md exists"
assert_file_exists "$INSTALL_MD" ".codex/INSTALL.md exists"

AGENTS_CONTENT="$(cat "$AGENTS_MD" 2>/dev/null || true)"
INSTALL_CONTENT="$(cat "$INSTALL_MD" 2>/dev/null || true)"

# ---------------------------------------------------------------------------
# Case 1: AGENTS.md bridge points at commands-codex/
# ---------------------------------------------------------------------------
echo "[case 1] AGENTS.md mentions commands-codex/"
assert_contains "$AGENTS_CONTENT" "commands-codex" \
    "AGENTS.md references commands-codex/ for slash bridge"

# ---------------------------------------------------------------------------
# Case 2: AGENTS.md tool mapping uses MORKIT_PLUGIN_ROOT
# ---------------------------------------------------------------------------
echo "[case 2] AGENTS.md mentions MORKIT_PLUGIN_ROOT"
assert_contains "$AGENTS_CONTENT" "MORKIT_PLUGIN_ROOT" \
    "AGENTS.md documents MORKIT_PLUGIN_ROOT as canonical env"

# ---------------------------------------------------------------------------
# Case 3: AGENTS.md mentions drift detection
# ---------------------------------------------------------------------------
echo "[case 3] AGENTS.md surfaces drift detector"
if printf '%s' "$AGENTS_CONTENT" | grep -qiE "check-codex-drift\.sh|drift detect|codex.drift"; then
    _pass "AGENTS.md surfaces drift detection"
else
    _fail "AGENTS.md should mention check-codex-drift.sh or drift detection"
fi

# ---------------------------------------------------------------------------
# Case 4: INSTALL.md symlink step targets skills-codex (not just skills)
# ---------------------------------------------------------------------------
echo "[case 4] INSTALL.md symlink → skills-codex"
assert_contains "$INSTALL_CONTENT" "skills-codex" \
    "INSTALL.md references skills-codex for manual symlink"

# ---------------------------------------------------------------------------
# Case 5: INSTALL.md documents --with-hooks flag
# ---------------------------------------------------------------------------
echo "[case 5] INSTALL.md documents --with-hooks"
assert_contains "$INSTALL_CONTENT" "--with-hooks" \
    "INSTALL.md mentions --with-hooks installer flag"

# ---------------------------------------------------------------------------
# Case 6: INSTALL.md surfaces sync-codex-fork.sh
# ---------------------------------------------------------------------------
echo "[case 6] INSTALL.md surfaces sync-codex-fork.sh"
assert_contains "$INSTALL_CONTENT" "sync-codex-fork.sh" \
    "INSTALL.md references sync-codex-fork.sh for bootstrap/recovery"

# ---------------------------------------------------------------------------
exit_with_status
