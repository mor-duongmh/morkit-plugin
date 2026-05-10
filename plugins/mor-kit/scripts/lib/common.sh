#!/usr/bin/env bash
# common.sh — shared cross-platform helpers for mor-kit plugin scripts.
# This file is sourced; it never auto-runs.
#
# Provides:
#   mor_kit_root           — resolve project-relative changes folder (honors MOR_KIT_ROOT)
#   marker_path            — path of .mor-kit marker
#   plugin_root            — resolve ${CLAUDE_PLUGIN_ROOT} or fallback to script location
#   file_mtime <path>      — cross-platform mtime (epoch seconds)
#   iso_now                — current time as ISO 8601 UTC
#   is_kebab_case <name>   — exit 0 if valid kebab-case, 1 otherwise
#   ensure_jq              — exit 1 if jq missing
#   atomic_write <file> <content>  — write via tmp + mv
#   atomic_jq <file> <jq-expr>     — read JSON, transform, write atomic

# Guard against double-sourcing
[[ -n "${MOR_KIT_COMMON_LOADED:-}" ]] && return 0
MOR_KIT_COMMON_LOADED=1

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
mor_kit_root() {
    echo "${MOR_KIT_ROOT:-mor-kit/changes}"
}

marker_path() {
    echo "$(mor_kit_root)/.mor-kit"
}

# Resolve plugin root: prefer env, fall back to derive-from-script-location.
# Caller must pass a "hint" path (e.g. ${BASH_SOURCE[0]} of the calling script).
plugin_root() {
    local hint="${1:-}"
    if [[ -n "${CLAUDE_PLUGIN_ROOT:-}" ]]; then
        echo "$CLAUDE_PLUGIN_ROOT"
        return 0
    fi
    if [[ -n "$hint" ]]; then
        # hint is path of a script in $plugin_root/scripts/<file> or
        # $plugin_root/scripts/lib/<file>; walk up until we find .claude-plugin/
        local dir
        dir="$(cd "$(dirname "$hint")" && pwd)"
        while [[ "$dir" != "/" ]]; do
            if [[ -d "$dir/.claude-plugin" ]]; then
                echo "$dir"
                return 0
            fi
            dir="$(dirname "$dir")"
        done
    fi
    echo "✗ common.sh: cannot resolve plugin root (no CLAUDE_PLUGIN_ROOT, no hint walks to .claude-plugin/)" >&2
    return 1
}

# ---------------------------------------------------------------------------
# Cross-platform mtime
# ---------------------------------------------------------------------------
file_mtime() {
    local f="$1"
    [[ -e "$f" ]] || { echo 0; return 1; }
    stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null
}

# ---------------------------------------------------------------------------
# ISO timestamp
# ---------------------------------------------------------------------------
iso_now() {
    date -u +'%Y-%m-%dT%H:%M:%SZ'
}

# ---------------------------------------------------------------------------
# Kebab-case validator
# Rules: lowercase letters, digits, dashes; starts with a letter; no consecutive
# dashes; no leading/trailing dash.
# ---------------------------------------------------------------------------
is_kebab_case() {
    local name="$1"
    [[ -n "$name" ]] || return 1
    [[ "$name" =~ ^[a-z][a-z0-9]*(-[a-z0-9]+)*$ ]]
}

# ---------------------------------------------------------------------------
# Reserved names that cannot be used as change names
# ---------------------------------------------------------------------------
RESERVED_NAMES=(archive .mor-kit)

is_reserved_name() {
    local name="$1"
    local r
    for r in "${RESERVED_NAMES[@]}"; do
        [[ "$name" == "$r" ]] && return 0
    done
    return 1
}

# ---------------------------------------------------------------------------
# jq dependency check
# ---------------------------------------------------------------------------
ensure_jq() {
    if ! command -v jq >/dev/null 2>&1; then
        echo "✗ jq is required but not installed. Install via brew/apt/dnf." >&2
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Atomic write helpers
# ---------------------------------------------------------------------------
atomic_write() {
    local target="$1"
    local content="$2"
    local tmp
    tmp="$(mktemp "${target}.XXXXXX")" || return 1
    printf '%s' "$content" > "$tmp" || { rm -f "$tmp"; return 1; }
    mv "$tmp" "$target" || { rm -f "$tmp"; return 1; }
}

atomic_jq() {
    local file="$1"
    local expr="$2"
    ensure_jq || return 1
    local tmp
    tmp="$(mktemp "${file}.XXXXXX")" || return 1
    if [[ -f "$file" ]]; then
        if ! jq "$expr" "$file" > "$tmp" 2>/dev/null; then
            rm -f "$tmp"; return 1
        fi
    else
        if ! echo '{}' | jq "$expr" > "$tmp" 2>/dev/null; then
            rm -f "$tmp"; return 1
        fi
    fi
    mv "$tmp" "$file" || { rm -f "$tmp"; return 1; }
}

# ---------------------------------------------------------------------------
# Marker file management
# ---------------------------------------------------------------------------
ensure_marker() {
    ensure_jq || return 1
    local root marker
    root="$(mor_kit_root)"
    marker="$root/.mor-kit"
    mkdir -p "$root" 2>/dev/null || true
    if [[ ! -f "$marker" ]]; then
        local now
        now="$(iso_now)"
        printf '{"format_version":1,"plugin":"mor-kit@mor-duongmh","created_at":"%s"}\n' "$now" > "$marker"
    fi
}

is_plugin_managed() {
    local root
    root="$(mor_kit_root)"
    [[ -f "$root/.mor-kit" ]]
}

# Schema version of validator/scaffold (must match .meta.json schema_version)
MOR_KIT_SCHEMA_VERSION=1
