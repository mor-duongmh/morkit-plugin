#!/usr/bin/env bash
# test-docs-codex.sh — coverage for AGENTS.md + .codex/INSTALL.md (single-source).
#
# Documentation-only checks: the two user-facing Codex docs must reflect the
# single-source model (one plugins/morkit/skills/, mapping reference, native
# multi_agent, Advisory mode) — NOT the retired fork.
#
# Cases covered:
#   1. AGENTS.md slash-command bridge points at commands/ (single source).
#   2. AGENTS.md documents ${MORKIT_PLUGIN_ROOT} as canonical env var.
#   3. AGENTS.md surfaces the Advisory-mode note (enforcement is advisory on Codex).
#   4. .codex/INSTALL.md symlink step targets plugins/morkit/skills.
#   5. .codex/INSTALL.md documents --with-hooks installer flag.
#   6. .codex/INSTALL.md surfaces native multi_agent for deep-review.

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

# Case 1: AGENTS.md bridge points at commands/ (single source, not a fork)
echo "[case 1] AGENTS.md slash bridge → commands/"
assert_contains "$AGENTS_CONTENT" "commands/<name>.md" \
    "AGENTS.md references commands/<name>.md for slash bridge"

# Case 2: AGENTS.md documents MORKIT_PLUGIN_ROOT
echo "[case 2] AGENTS.md mentions MORKIT_PLUGIN_ROOT"
assert_contains "$AGENTS_CONTENT" "MORKIT_PLUGIN_ROOT" \
    "AGENTS.md documents MORKIT_PLUGIN_ROOT as canonical env"

# Case 3: AGENTS.md surfaces Advisory mode
echo "[case 3] AGENTS.md surfaces Advisory mode"
if printf '%s' "$AGENTS_CONTENT" | grep -qiE "advisory"; then
    _pass "AGENTS.md surfaces Advisory mode"
else
    _fail "AGENTS.md should describe Advisory mode (enforcement is advisory on Codex)"
fi

# Case 4: INSTALL.md symlink step targets plugins/morkit/skills
echo "[case 4] INSTALL.md symlink → plugins/morkit/skills"
assert_contains "$INSTALL_CONTENT" "morkit/skills" \
    "INSTALL.md references plugins/morkit/skills for manual symlink"

# Case 5: INSTALL.md documents --with-hooks flag
echo "[case 5] INSTALL.md documents --with-hooks"
assert_contains "$INSTALL_CONTENT" "--with-hooks" \
    "INSTALL.md mentions --with-hooks installer flag"

# Case 6: INSTALL.md surfaces native multi_agent for deep-review
echo "[case 6] INSTALL.md surfaces native multi_agent"
assert_contains "$INSTALL_CONTENT" "multi_agent" \
    "INSTALL.md references native multi_agent for deep-review"

exit_with_status
