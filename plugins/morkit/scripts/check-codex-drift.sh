#!/usr/bin/env bash
# check-codex-drift.sh — CI guard that WARNS (never fails) when files under
# `plugins/morkit/skills/` have changed but their `plugins/morkit/skills-codex/`
# counterparts are stale relative to a hash baseline.
#
# Contract:
#   - ALWAYS exits 0. Reviewers see warnings in the PR check summary and decide
#     whether to require a sync before merge. (Per design.md R3 + user decision.)
#   - WARN/INFO messages go to STDERR; success messages to STDOUT.
#
# Usage:
#   check-codex-drift.sh [--baseline <path>] [--source <path>] [--target <path>]
#
# Defaults (relative to plugin root inferred from script location):
#   --baseline  plugins/morkit/.codex/.drift-baseline
#   --source    plugins/morkit/skills/
#   --target    plugins/morkit/skills-codex/
#
# Baseline format (plain text, one entry per line, '#' lines ignored):
#   <relpath-from-source>:<sha256-of-source-content-at-sync-time>
#
# Behavior matrix:
#   skills-codex/ missing        → INFO "not yet bootstrapped (Task 5)", exit 0
#   baseline missing OR empty    → WARN "baseline missing, run sync...", exit 0
#   hash matches baseline        → STDOUT "no drift detected", exit 0
#   hash diverged AND skills-    → WARN with file list + sync hint, exit 0
#     codex/<rel> mtime < src
#
# Notes for Task 2 scope:
#   - Vocab swap (Task 3 vocab-map.yaml) does not exist yet, so we hash raw
#     source content. When Task 4 lands sync-codex-fork.sh, swap source → text
#     before hashing inside the helper `_current_hash`.
#   - mtime comparison is portable: stat -f (BSD/macOS) with fallback to
#     stat -c (GNU/Linux). Pattern borrowed from hooks/pre-tool-checklist-gate.sh.
#
# Dependencies: bash, coreutils (find, awk), sha256sum OR shasum, stat. No new
# runtime deps introduced.

set -uo pipefail   # no -e — checks must not abort on grep no-match etc.

# ---------------------------------------------------------------------------
# Locate plugin root via cascade
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_ROOT="${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$DEFAULT_PLUGIN_ROOT}}"

BASELINE="$PLUGIN_ROOT/.codex/.drift-baseline"
SOURCE_DIR="$PLUGIN_ROOT/skills"
TARGET_DIR="$PLUGIN_ROOT/skills-codex"

# ---------------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --baseline) BASELINE="$2"; shift 2 ;;
        --source)   SOURCE_DIR="$2"; shift 2 ;;
        --target)   TARGET_DIR="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,40p' "$0"
            exit 0
            ;;
        *)
            echo "WARN: unknown arg '$1' — ignored" >&2
            shift
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Portable helpers
# ---------------------------------------------------------------------------
_sha256() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" 2>/dev/null | awk '{print $1}'
    else
        shasum -a 256 "$1" 2>/dev/null | awk '{print $1}'
    fi
}

# Epoch mtime of a file. BSD first, GNU fallback. Empty string on error.
_mtime() {
    stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null || echo ""
}

# Hash of "current" source content. Task 2: raw bytes.
# TODO(Task 4): when codex/vocab-map.yaml exists, pipe through the swap helper
# before hashing so a vocab-only diff doesn't read as drift.
_current_hash() {
    _sha256 "$1"
}

# Look up baseline hash for a relative path. Empty if not found.
_baseline_hash_for() {
    local rel="$1" baseline="$2"
    # Strip comments + blank lines; match "<rel>:<hash>"
    awk -F: -v r="$rel" '
        /^[[:space:]]*#/ { next }
        NF < 2           { next }
        $1 == r          { print $2; exit }
    ' "$baseline" 2>/dev/null
}

# Count meaningful (non-comment, non-blank) entries in baseline.
_baseline_entry_count() {
    local baseline="$1"
    [[ -f "$baseline" ]] || { echo 0; return; }
    awk '
        /^[[:space:]]*#/ { next }
        /^[[:space:]]*$/ { next }
        { c++ }
        END { print c+0 }
    ' "$baseline" 2>/dev/null
}

# ---------------------------------------------------------------------------
# Case 1 — skills-codex/ not yet bootstrapped
# ---------------------------------------------------------------------------
if [[ ! -d "$TARGET_DIR" ]]; then
    {
        echo "INFO: skills-codex/ not yet bootstrapped (Task 5) — drift check skipped."
        echo "      Target dir: $TARGET_DIR"
    } >&2
    exit 0
fi

# ---------------------------------------------------------------------------
# Case 4/5 — baseline missing or empty (but target exists)
# ---------------------------------------------------------------------------
ENTRIES=$(_baseline_entry_count "$BASELINE")
if [[ ! -f "$BASELINE" || "$ENTRIES" -eq 0 ]]; then
    {
        echo "WARN: drift baseline missing or empty — cannot verify skills-codex/ sync."
        echo "      Baseline: $BASELINE"
        echo "      Action:   run \`bash plugins/morkit/scripts/sync-codex-fork.sh\` to populate it."
    } >&2
    exit 0
fi

# ---------------------------------------------------------------------------
# Cases 2 & 3 — walk source skills, detect drift
# ---------------------------------------------------------------------------
DRIFTED=()
CHECKED=0

while IFS= read -r src_file; do
    CHECKED=$((CHECKED + 1))
    rel="${src_file#"$SOURCE_DIR/"}"

    current=$(_current_hash "$src_file")
    baseline_hash=$(_baseline_hash_for "$rel" "$BASELINE")

    # No baseline entry for this file — treat as new/untracked (info-only).
    if [[ -z "$baseline_hash" ]]; then
        continue
    fi

    # In sync — nothing to do.
    if [[ "$current" == "$baseline_hash" ]]; then
        continue
    fi

    # Diverged. Is the codex counterpart stale (older mtime than source)?
    tgt_file="$TARGET_DIR/$rel"
    if [[ ! -f "$tgt_file" ]]; then
        DRIFTED+=("$rel  (skills-codex counterpart missing)")
        continue
    fi

    src_mtime=$(_mtime "$src_file")
    tgt_mtime=$(_mtime "$tgt_file")
    if [[ -n "$src_mtime" && -n "$tgt_mtime" && "$tgt_mtime" -lt "$src_mtime" ]]; then
        DRIFTED+=("$rel  (source newer than skills-codex counterpart)")
    elif [[ -z "$src_mtime" || -z "$tgt_mtime" ]]; then
        # Couldn't stat — be conservative, flag it.
        DRIFTED+=("$rel  (mtime unavailable; hash differs from baseline)")
    fi
done < <(find "$SOURCE_DIR" -type f -name 'SKILL.md' 2>/dev/null | sort)

if [[ "${#DRIFTED[@]}" -eq 0 ]]; then
    echo "OK: no drift detected ($CHECKED skill file(s) checked)."
    exit 0
fi

{
    echo "WARN: codex skills fork drift detected (${#DRIFTED[@]} of $CHECKED file(s)):"
    for f in "${DRIFTED[@]}"; do
        echo "      - $f"
    done
    echo ""
    echo "      Action: run \`bash plugins/morkit/scripts/sync-codex-fork.sh\`"
    echo "              to re-apply the vocab map and refresh the baseline."
    echo "      Note:   this is a non-blocking warning; reviewer decides whether"
    echo "              to require sync before merge."
} >&2
exit 0
