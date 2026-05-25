#!/usr/bin/env bash
# install-codex.sh — one-command morkit installer for Codex CLI.
#
# Symlinks morkit skills/ + AGENTS.md into Codex's discovery paths.
# Optionally enables codex_hooks feature and links ~/.codex/hooks.json
# to plugin's hooks.json (so upstream changes propagate via git pull).
#
# Usage:
#   bash plugins/morkit/scripts/install-codex.sh              # interactive
#   bash plugins/morkit/scripts/install-codex.sh --yes        # accept defaults
#   bash plugins/morkit/scripts/install-codex.sh --with-hooks # also enable hooks
#   bash plugins/morkit/scripts/install-codex.sh --uninstall  # remove symlinks
#
# Idempotent: re-running is safe; existing correct symlinks are left alone.

set -uo pipefail

# --- resolve plugin root (this script lives at <root>/scripts/) ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
AGENTS_HOME="${AGENTS_HOME:-$HOME/.agents}"
SKILL_LINK="$AGENTS_HOME/skills/morkit"
AGENTS_LINK="$CODEX_HOME/AGENTS.md"

ASSUME_YES=0
WITH_HOOKS=0
UNINSTALL=0

for arg in "$@"; do
    case "$arg" in
        --yes|-y) ASSUME_YES=1 ;;
        --with-hooks) WITH_HOOKS=1 ;;
        --uninstall) UNINSTALL=1 ;;
        --help|-h)
            sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "unknown arg: $arg" >&2
            exit 2
            ;;
    esac
done

confirm() {
    [ "$ASSUME_YES" -eq 1 ] && return 0
    local prompt="$1"
    read -r -p "$prompt [Y/n] " ans
    case "${ans:-Y}" in
        Y|y|Yes|yes|YES|"") return 0 ;;
        *) return 1 ;;
    esac
}

is_morkit_symlink() {
    # $1: path. Returns 0 if it's a symlink resolving inside PLUGIN_ROOT.
    [ -L "$1" ] || return 1
    local target
    target="$(readlink "$1")"
    case "$target" in
        "$PLUGIN_ROOT"/*) return 0 ;;
        *) return 1 ;;
    esac
}

# --- shell rc detection (for MORKIT_PLUGIN_ROOT / CLAUDE_PLUGIN_ROOT env export) ---
RC_MARKER_BEGIN="# >>> morkit-codex >>>"
RC_MARKER_END="# <<< morkit-codex <<<"

detect_shell_rc() {
    # Echo the user's interactive shell rc path. Prefer current $SHELL.
    local shell_name rc
    shell_name="$(basename "${SHELL:-/bin/sh}")"
    case "$shell_name" in
        zsh)  rc="$HOME/.zshrc" ;;
        bash) [ -f "$HOME/.bashrc" ] && rc="$HOME/.bashrc" || rc="$HOME/.bash_profile" ;;
        *)    rc="" ;;
    esac
    echo "$rc"
}

remove_rc_block() {
    local rc="$1"
    [ -f "$rc" ] || return 0
    grep -q "$RC_MARKER_BEGIN" "$rc" 2>/dev/null || return 0
    local tmp; tmp="$(mktemp)"
    awk -v b="$RC_MARKER_BEGIN" -v e="$RC_MARKER_END" '
        $0 == b {skip=1; next}
        $0 == e {skip=0; next}
        !skip {print}
    ' "$rc" > "$tmp" && mv "$tmp" "$rc"
    echo "  removed morkit-codex block from $rc"
}

uninstall() {
    echo "=== morkit Codex uninstall ==="
    if is_morkit_symlink "$SKILL_LINK"; then
        rm "$SKILL_LINK" && echo "removed: $SKILL_LINK"
    else
        echo "skip: $SKILL_LINK (not a morkit symlink)"
    fi
    if is_morkit_symlink "$AGENTS_LINK"; then
        rm "$AGENTS_LINK" && echo "removed: $AGENTS_LINK"
    else
        echo "skip: $AGENTS_LINK (not a morkit symlink — manual cleanup if needed)"
    fi
    local hooks_json="$CODEX_HOME/hooks.json"
    if is_morkit_symlink "$hooks_json"; then
        rm "$hooks_json" && echo "removed: $hooks_json"
    else
        [ -e "$hooks_json" ] && echo "skip: $hooks_json (not a morkit symlink — manual cleanup if needed)"
    fi
    local rc; rc="$(detect_shell_rc)"
    if [ -n "$rc" ] && [ -f "$rc" ]; then
        remove_rc_block "$rc"
    fi
    echo "done."
    exit 0
}

[ "$UNINSTALL" -eq 1 ] && uninstall

echo "=== morkit Codex installer ==="
echo "Plugin root: $PLUGIN_ROOT"
echo "Codex home:  $CODEX_HOME"
echo "Agents home: $AGENTS_HOME"
echo

# --- prerequisite: codex CLI ---
if ! command -v codex >/dev/null 2>&1; then
    echo "FAIL: codex CLI not found in PATH. Install from https://developers.openai.com/codex/" >&2
    exit 1
fi
CODEX_VER="$(codex --version 2>&1 | awk '{print $NF}' | head -1)"
echo "codex CLI: $CODEX_VER"

# --- prerequisite: source files exist ---
# Single-source: Codex install symlinks the same plugins/morkit/skills/ that
# Claude Code uses. Skill files keep Claude vocab; the agent translates via
# using-morkit/references/codex-tools.md at runtime.
if [ ! -d "$PLUGIN_ROOT/skills" ]; then
    echo "FAIL: $PLUGIN_ROOT/skills/ not found." >&2
    exit 1
fi
if [ ! -f "$PLUGIN_ROOT/AGENTS.md" ]; then
    echo "FAIL: $PLUGIN_ROOT/AGENTS.md not found." >&2
    exit 1
fi

mkdir -p "$AGENTS_HOME/skills" "$CODEX_HOME"

# --- step 1: skills symlink (targets skills/, not skills/) ---
SKILL_TARGET="$PLUGIN_ROOT/skills"
echo
echo "[1/4] Skill discovery symlink (target: skills/)"
if is_morkit_symlink "$SKILL_LINK"; then
    CURRENT="$(readlink "$SKILL_LINK")"
    if [ "$CURRENT" = "$SKILL_TARGET" ]; then
        echo "  already linked: $SKILL_LINK -> $CURRENT"
    else
        echo "  WARN: $SKILL_LINK points to $CURRENT (expected $SKILL_TARGET)."
        if confirm "  Repoint to $SKILL_TARGET?"; then
            rm "$SKILL_LINK"
            ln -s "$SKILL_TARGET" "$SKILL_LINK"
            echo "  re-linked: $SKILL_LINK -> $SKILL_TARGET"
        else
            echo "  skipped — Codex will discover stale skill tree."
        fi
    fi
elif [ -e "$SKILL_LINK" ] || [ -L "$SKILL_LINK" ]; then
    echo "  WARN: $SKILL_LINK exists but does not point to this morkit checkout."
    if confirm "  Replace with symlink to $SKILL_TARGET?"; then
        rm -rf "$SKILL_LINK"
        ln -s "$SKILL_TARGET" "$SKILL_LINK"
        echo "  linked: $SKILL_LINK -> $SKILL_TARGET"
    else
        echo "  skipped — Codex will not see morkit skills."
    fi
else
    if confirm "  Create symlink $SKILL_LINK -> $SKILL_TARGET?"; then
        ln -s "$SKILL_TARGET" "$SKILL_LINK"
        echo "  linked: $SKILL_LINK"
    else
        echo "  skipped."
    fi
fi

# --- step 2: AGENTS.md ---
echo
echo "[2/4] AGENTS.md (working agreements + slash-command bridge)"
if is_morkit_symlink "$AGENTS_LINK"; then
    echo "  already linked: $AGENTS_LINK -> $(readlink "$AGENTS_LINK")"
elif [ -f "$AGENTS_LINK" ]; then
    if grep -q "morkit — Codex agent guidance" "$AGENTS_LINK" 2>/dev/null; then
        echo "  already contains morkit guidance (manual append detected). leaving alone."
    else
        echo "  WARN: $AGENTS_LINK exists with non-morkit content."
        if confirm "  Append morkit AGENTS.md content?"; then
            printf '\n\n' >> "$AGENTS_LINK"
            cat "$PLUGIN_ROOT/AGENTS.md" >> "$AGENTS_LINK"
            echo "  appended."
        else
            echo "  skipped — Codex will not load morkit working agreements."
        fi
    fi
else
    if confirm "  Create symlink $AGENTS_LINK -> $PLUGIN_ROOT/AGENTS.md?"; then
        ln -s "$PLUGIN_ROOT/AGENTS.md" "$AGENTS_LINK"
        echo "  linked: $AGENTS_LINK"
    else
        echo "  skipped."
    fi
fi

# --- step 3: shell rc env block (unblocks 12 skills using ${MORKIT_PLUGIN_ROOT}) ---
echo
echo "[3/4] Shell rc env (export MORKIT_PLUGIN_ROOT for skills)"
RC_FILE="$(detect_shell_rc)"
if [ -z "$RC_FILE" ]; then
    echo "  skipped — unsupported shell ($SHELL). Add manually:"
    echo "    export MORKIT_PLUGIN_ROOT=\"$PLUGIN_ROOT\""
elif grep -q "$RC_MARKER_BEGIN" "$RC_FILE" 2>/dev/null; then
    echo "  $RC_FILE already contains morkit-codex block — leaving alone."
    echo "  (re-run with --uninstall first if you need to repoint)"
elif confirm "  Append MORKIT_PLUGIN_ROOT export to $RC_FILE?"; then
    {
        echo ""
        echo "$RC_MARKER_BEGIN"
        echo "# morkit-codex: makes \${MORKIT_PLUGIN_ROOT} visible to skills invoked by Codex."
        echo "# (Also exports CLAUDE_PLUGIN_ROOT as a MORKIT_PLUGIN_ROOT fallback for legacy scripts.)"
        echo "export MORKIT_PLUGIN_ROOT=\"$PLUGIN_ROOT\""
        echo "export CLAUDE_PLUGIN_ROOT=\"\${MORKIT_PLUGIN_ROOT:-\${CLAUDE_PLUGIN_ROOT:-$PLUGIN_ROOT}}\""
        echo "export PATH=\"\$PATH:$PLUGIN_ROOT/scripts\""
        echo "$RC_MARKER_END"
    } >> "$RC_FILE"
    echo "  appended to $RC_FILE — open a new terminal or run: source $RC_FILE"
else
    echo "  skipped — skills (propose/review/archive/deep-review/*) will fail under Codex."
fi

# --- step 4: hooks (optional, opt-in only) ---
echo
echo "[4/4] Hooks (optional, default OFF)"
HOOKS_WANTED=0
if [ "$WITH_HOOKS" -eq 1 ]; then
    HOOKS_WANTED=1
elif [ "$ASSUME_YES" -eq 0 ]; then
    # only ask in interactive mode; --yes alone does not enable hooks
    confirm "  Enable codex_hooks + write ~/.codex/hooks.json?" && HOOKS_WANTED=1
fi
if [ "$HOOKS_WANTED" -eq 0 ]; then
    echo "  skipped — re-run with --with-hooks to enable."
else
    # try enabling the feature flag; tolerate already-enabled or unsupported builds
    if codex features enable codex_hooks >/dev/null 2>&1; then
        echo "  codex_hooks: enabled"
    else
        echo "  codex_hooks: could not toggle (check 'codex features list'); continuing"
    fi

    HOOKS_JSON="$CODEX_HOME/hooks.json"
    HOOKS_SRC="$PLUGIN_ROOT/hooks/hooks.json"
    if [ ! -f "$HOOKS_SRC" ]; then
        echo "  WARN: $HOOKS_SRC missing; skipping hooks.json."
    elif is_morkit_symlink "$HOOKS_JSON"; then
        echo "  already linked: $HOOKS_JSON -> $(readlink "$HOOKS_JSON")"
    elif [ -f "$HOOKS_JSON" ] && grep -q "morkit" "$HOOKS_JSON" 2>/dev/null; then
        echo "  $HOOKS_JSON already references morkit — leaving alone."
    elif [ -e "$HOOKS_JSON" ] || [ -L "$HOOKS_JSON" ]; then
        echo "  WARN: $HOOKS_JSON exists; refusing to overwrite. Add morkit hook manually."
    else
        # Symlink (preferred over copy: upstream changes propagate via git
        # pull, no drift between installed config and source of truth).
        # Cross-platform note: on Windows / FAT filesystems where symlinks
        # don't work, swap this for `cp` and re-run install after upgrades.
        ln -s "$HOOKS_SRC" "$HOOKS_JSON"
        echo "  linked: $HOOKS_JSON -> $HOOKS_SRC"
    fi
fi

# --- summary ---
echo
echo "=== summary ==="
SKILL_COUNT=0
if [ -d "$SKILL_LINK" ]; then
    SKILL_COUNT=$(find -L "$SKILL_LINK" -mindepth 2 -maxdepth 2 -name SKILL.md 2>/dev/null | wc -l | tr -d ' ')
fi
echo "  skills discovered: $SKILL_COUNT"
echo "  AGENTS.md:         $([ -e "$AGENTS_LINK" ] && echo present || echo missing)"
echo
echo "Next: restart Codex (quit + relaunch), then verify:"
echo "  bash $PLUGIN_ROOT/scripts/doctor-codex.sh"
