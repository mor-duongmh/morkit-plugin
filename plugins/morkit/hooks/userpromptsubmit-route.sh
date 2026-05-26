#!/usr/bin/env bash
# userpromptsubmit-route.sh — Codex UserPromptSubmit hook (advisory routing).
#
# Reads the user prompt from hook stdin JSON, invokes the shared router with
# harness=codex, and emits a [ROUTING] line to stdout → Codex picks it up as
# additionalContext injected into the model context.
#
# Advisory: Codex has no SubagentStart/SubagentStop events (v0.130.0), so this
# hook cannot enforce model selection at spawn time. The [ROUTING] line is a
# suggestion in context; model-baked custom agents (.codex/agents/*.toml) are the
# robust enforcement mechanism.
#
# Path assumption: the shared router lives at .claude/helpers/hook-handler.cjs
# relative to the repo root (i.e. parent of plugins/morkit). This script resolves
# that path via MORKIT_PLUGIN_ROOT / CLAUDE_PLUGIN_ROOT (pointing to plugins/morkit)
# → repo root is two levels up. If neither env var is set, the script derives the
# repo root from its own filesystem location.
#
# Safety contract:
#   - Never hangs: relies on hook-handler.cjs's 5 s global timer + 500 ms stdin timer.
#   - Never fails the prompt: all error paths exit 0.
#   - Emits nothing (silent) on jq-missing or malformed stdin; Codex proceeds normally.

set -uo pipefail

# Resolve repo root. MORKIT_PLUGIN_ROOT / CLAUDE_PLUGIN_ROOT both point to
# plugins/morkit — repo root is two dirs up.
if [[ -n "${MORKIT_PLUGIN_ROOT:-}" ]]; then
    REPO_ROOT="$(cd "${MORKIT_PLUGIN_ROOT}/../.." && pwd -P)"
elif [[ -n "${CLAUDE_PLUGIN_ROOT:-}" ]]; then
    REPO_ROOT="$(cd "${CLAUDE_PLUGIN_ROOT}/../.." && pwd -P)"
else
    # Fallback: derive from this script's own location
    # This script is at <repo>/plugins/morkit/hooks/userpromptsubmit-route.sh
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
    REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd -P)"
fi

HOOK_HANDLER="$REPO_ROOT/.claude/helpers/hook-handler.cjs"
SCOPE_MARKER="$REPO_ROOT/.model-routing.json"

# Scope guard: only proceed when the claude-plugins scope marker is present
# and has "enabled": true. Fail-open: any error or absent marker → exit 0 silently.
# We check the marker at the repo root (already resolved above); no upward walk
# needed because the hook is only invoked when morkit is the plugin root, which
# already implies we're inside the repo. The hook-handler.cjs performs the same
# guard internally for double-safety.
if [[ ! -f "$SCOPE_MARKER" ]]; then
    exit 0
fi
if command -v jq >/dev/null 2>&1; then
    enabled=$(jq -r '.enabled // false' "$SCOPE_MARKER" 2>/dev/null || echo "false")
    [[ "$enabled" == "true" ]] || exit 0
elif command -v node >/dev/null 2>&1; then
    # FIX N-2: export SCOPE_MARKER as an env var so the path is read via process.env
    # rather than embedded as an inline JS string literal. This handles paths with spaces.
    SCOPE_MARKER_PATH="$SCOPE_MARKER"
    export SCOPE_MARKER_PATH
    enabled=$(node -e "try{var m=JSON.parse(require('fs').readFileSync(process.env.SCOPE_MARKER_PATH,'utf8'));console.log(m.enabled===true?'true':'false')}catch(_){console.log('false')}" 2>/dev/null || echo "false")
    [[ "$enabled" == "true" ]] || exit 0
else
    # Neither jq nor node available → fail-open (exit 0, noop)
    exit 0
fi

# Fail-open: if node or the handler is not available, exit silently.
if ! command -v node >/dev/null 2>&1; then
    exit 0
fi
if [[ ! -f "$HOOK_HANDLER" ]]; then
    exit 0
fi

# Read stdin (Codex passes hook payload as JSON on stdin). Codex UserPromptSubmit
# payload: { "prompt": "<user text>" } (or similar — we pass the raw JSON through
# to hook-handler.cjs which extracts .prompt / .command).
input="$(cat || true)"
[[ -n "$input" ]] || exit 0

# Invoke the shared router with harness=codex. The handler reads the prompt from
# the piped stdin JSON and prints the [ROUTING] line to stdout.
printf '%s' "$input" | node "$HOOK_HANDLER" route --harness codex 2>/dev/null || true
