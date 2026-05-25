#!/usr/bin/env bash
# doctor-codex.sh — verify morkit installation health under Codex CLI.
#
# Reports status of every component required for morkit-on-Codex to function.
# No -e: all checks run even if some fail.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
AGENTS_HOME="${AGENTS_HOME:-$HOME/.agents}"
SKILL_LINK="$AGENTS_HOME/skills/morkit"
AGENTS_LINK="$CODEX_HOME/AGENTS.md"
HOOKS_JSON="$CODEX_HOME/hooks.json"

FAIL_COUNT=0
WARN_COUNT=0

ok()   { echo "  OK    $1"; }
warn() { echo "  WARN  $1"; WARN_COUNT=$((WARN_COUNT+1)); }
fail() { echo "  FAIL  $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }

echo "=== morkit Codex doctor ==="
echo "Plugin root: $PLUGIN_ROOT"
echo

# --- codex CLI ---
echo "[1] codex CLI"
if command -v codex >/dev/null 2>&1; then
    CODEX_VER="$(codex --version 2>&1 | awk '{print $NF}' | head -1)"
    # version is X.Y.Z; require ≥ 0.120
    MAJOR=$(echo "$CODEX_VER" | cut -d. -f1)
    MINOR=$(echo "$CODEX_VER" | cut -d. -f2)
    if [ "${MAJOR:-0}" -gt 0 ] 2>/dev/null || { [ "${MAJOR:-0}" -eq 0 ] && [ "${MINOR:-0}" -ge 120 ]; } 2>/dev/null; then
        ok "codex $CODEX_VER"
    else
        warn "codex $CODEX_VER (recommend ≥ 0.120.0)"
    fi
else
    fail "codex CLI not in PATH"
fi

# --- skill symlink ---
echo
echo "[2] Skill discovery ($SKILL_LINK)"
if [ -L "$SKILL_LINK" ]; then
    TARGET="$(readlink "$SKILL_LINK")"
    if [ -d "$SKILL_LINK" ]; then
        # Codex install must point at skills/ (Codex vocab), not the
        # raw skills/ (Claude vocab). Verify the basename of the target.
        TARGET_BASE="$(basename "$TARGET")"
        if [ "$TARGET_BASE" = "skills" ]; then
            ok "symlink -> $TARGET (skills/)"
        else
            warn "symlink -> $TARGET (expected target: skills/, got: $TARGET_BASE/). Re-run install-codex.sh to repoint."
        fi
    else
        fail "symlink dangling -> $TARGET"
    fi
elif [ -d "$SKILL_LINK" ]; then
    warn "directory (not symlink) — updates won't auto-flow from this repo"
else
    fail "missing — run install-codex.sh"
fi

if [ -d "$SKILL_LINK" ]; then
    COUNT=$(find -L "$SKILL_LINK" -mindepth 2 -maxdepth 2 -name SKILL.md 2>/dev/null | wc -l | tr -d ' ')
    if [ "$COUNT" -ge 20 ]; then
        ok "$COUNT SKILL.md files discoverable"
    elif [ "$COUNT" -gt 0 ]; then
        warn "only $COUNT SKILL.md files (expected ≥ 20)"
    else
        fail "no SKILL.md files found"
    fi
fi

# --- AGENTS.md ---
echo
echo "[3] AGENTS.md ($AGENTS_LINK)"
if [ -L "$AGENTS_LINK" ]; then
    if [ -f "$AGENTS_LINK" ]; then
        ok "symlink -> $(readlink "$AGENTS_LINK")"
    else
        fail "symlink dangling"
    fi
elif [ -f "$AGENTS_LINK" ]; then
    if grep -q "morkit — Codex agent guidance" "$AGENTS_LINK" 2>/dev/null; then
        ok "regular file with morkit guidance embedded"
    else
        warn "exists but no morkit guidance — Codex won't see working agreements"
    fi
else
    fail "missing — Codex won't auto-load morkit working agreements"
fi

# --- shell rc env block ---
echo
echo "[4] Shell rc MORKIT_PLUGIN_ROOT export"
SHELL_NAME="$(basename "${SHELL:-/bin/sh}")"
case "$SHELL_NAME" in
    zsh)  RC_FILE="$HOME/.zshrc" ;;
    bash) [ -f "$HOME/.bashrc" ] && RC_FILE="$HOME/.bashrc" || RC_FILE="$HOME/.bash_profile" ;;
    *)    RC_FILE="" ;;
esac
if [ -z "$RC_FILE" ]; then
    warn "unsupported shell $SHELL_NAME — set MORKIT_PLUGIN_ROOT manually"
elif [ ! -f "$RC_FILE" ]; then
    warn "$RC_FILE not found — re-run install-codex.sh"
elif grep -q "# >>> morkit-codex >>>" "$RC_FILE"; then
    ok "morkit-codex block present in $RC_FILE"
else
    fail "$RC_FILE missing morkit-codex block — skills (propose/review/archive/deep-review) will fail"
fi
RESOLVED_ROOT="${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"
if [ -n "$RESOLVED_ROOT" ]; then
    if [ -d "$RESOLVED_ROOT" ]; then
        ok "MORKIT_PLUGIN_ROOT (or CLAUDE_PLUGIN_ROOT fallback) resolves to $RESOLVED_ROOT"
    else
        fail "MORKIT_PLUGIN_ROOT/CLAUDE_PLUGIN_ROOT exported but path invalid: $RESOLVED_ROOT"
    fi
else
    warn "neither MORKIT_PLUGIN_ROOT nor CLAUDE_PLUGIN_ROOT exported in current shell — open a new terminal or 'source $RC_FILE'"
fi

# --- hooks feature flag ---
echo
echo "[5] Hooks (optional)"
if command -v codex >/dev/null 2>&1; then
    FEATURES_OUT="$(codex features list 2>&1 || true)"
    if echo "$FEATURES_OUT" | grep -qi "codex_hooks.*enabled\|codex_hooks.*true\|codex_hooks: on"; then
        ok "codex_hooks: enabled"
    elif echo "$FEATURES_OUT" | grep -qi "codex_hooks"; then
        warn "codex_hooks: feature exists but disabled (run: codex features enable codex_hooks)"
    else
        warn "codex_hooks: not surfaced by 'codex features list' (build may not support hooks)"
    fi
else
    warn "codex CLI missing — skipping hooks feature check"
fi

if [ -L "$HOOKS_JSON" ]; then
    HOOKS_TARGET="$(readlink "$HOOKS_JSON")"
    if [ "$(basename "$HOOKS_TARGET")" = "hooks.json" ]; then
        ok "$HOOKS_JSON -> $HOOKS_TARGET (hooks.json)"
    else
        warn "$HOOKS_JSON -> $HOOKS_TARGET (expected hooks.json — re-run install-codex.sh --with-hooks)"
    fi
elif [ -f "$HOOKS_JSON" ]; then
    # Regular file (copy or manual). Check either explicit morkit reference
    # or the gate script that ships in hooks.json (stable token regardless of
    # how the PreToolUse matcher is formatted).
    if grep -qE "morkit|MORKIT_PLUGIN_ROOT" "$HOOKS_JSON" 2>/dev/null || grep -qF "pre-tool-checklist-gate" "$HOOKS_JSON" 2>/dev/null; then
        ok "$HOOKS_JSON references morkit (hooks.json content detected)"
    else
        warn "$HOOKS_JSON exists but doesn't reference morkit hooks.json"
    fi
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "import json,sys; json.load(open('$HOOKS_JSON'))" 2>/dev/null; then
            ok "$HOOKS_JSON valid JSON"
        else
            fail "$HOOKS_JSON invalid JSON"
        fi
    fi
else
    warn "$HOOKS_JSON not present — hooks disabled (this is fine if you don't need them)"
fi

# --- commands/ presence (read-only check; no symlink) ---
echo
echo "[6] commands/ (slash-command bridge source)"
COMMANDS_DIR="$PLUGIN_ROOT/commands"
if [ -d "$COMMANDS_DIR" ]; then
    CMD_COUNT=$(find "$COMMANDS_DIR" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
    if [ "$CMD_COUNT" -ge 10 ]; then
        ok "$CMD_COUNT command files in commands/"
    elif [ "$CMD_COUNT" -gt 0 ]; then
        warn "only $CMD_COUNT command files in commands/ (expected ≥ 10)"
    else
        warn "commands/ empty"
    fi
else
    fail "commands/ missing"
fi

# --- deep-review prerequisites (native multi_agent) ---
echo
echo "[7] Deep-review prerequisites"
ok "deep-review uses native Codex multi_agent (spawn_agent) — see using-morkit/references/codex-tools.md"
if [ -d "$PLUGIN_ROOT/agents" ]; then
    AGENT_COUNT=$(find "$PLUGIN_ROOT/agents" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
    ok "$AGENT_COUNT specialist prompts in agents/"
else
    warn "agents/ missing — deep-review specialists unavailable"
fi
if command -v git >/dev/null 2>&1; then ok "git available"; else fail "git missing"; fi
if command -v gh >/dev/null 2>&1; then ok "gh CLI (for PR targets)"; else warn "gh missing — PR targets unavailable, --diff still works"; fi

# --- summary ---
echo
echo "=== summary ==="
echo "  FAIL:  $FAIL_COUNT"
echo "  WARN:  $WARN_COUNT"
if [ "$FAIL_COUNT" -eq 0 ] && [ "$WARN_COUNT" -eq 0 ]; then
    echo "  morkit-on-Codex is healthy."
    exit 0
elif [ "$FAIL_COUNT" -eq 0 ]; then
    echo "  morkit-on-Codex works, but review WARNings above."
    exit 0
else
    echo "  morkit-on-Codex has FAILures — fix before use."
    exit 1
fi
