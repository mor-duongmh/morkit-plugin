#!/usr/bin/env bash
# Shared helpers for sync/verify/start-overlay scripts.
# This file is sourced — never run directly. No top-level side effects.
set -euo pipefail

# Resolve the plugin root from any script in scripts/ or scripts/lib/.
plugin_root() {
    local script_path="${BASH_SOURCE[1]:-$0}"
    local dir
    dir="$(cd "$(dirname "$script_path")" && pwd)"
    # Walk up until we find .claude-plugin/plugin.json
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/.claude-plugin/plugin.json" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "common.sh: cannot locate plugin root from $script_path" >&2
    return 1
}

# Cross-platform SHA256 (macOS shasum vs Linux sha256sum).
compute_sha256() {
    local file="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$file" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$file" | awk '{print $1}'
    else
        echo "common.sh: neither sha256sum nor shasum found" >&2
        return 1
    fi
}

require_command() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Required command '$cmd' not found in PATH" >&2
        exit 1
    fi
}

require_commands() {
    for cmd in "$@"; do
        require_command "$cmd"
    done
}

# Read a top-level field from .vendor-manifest.json. Returns "null" string for null/missing.
manifest_get() {
    local manifest="$1" field="$2"
    jq -r ".$field // \"null\"" "$manifest"
}

# Set a top-level field in .vendor-manifest.json (in place).
manifest_set() {
    local manifest="$1" field="$2" value="$3"
    local tmp
    tmp="$(mktemp)"
    jq --arg v "$value" ".$field = \$v" "$manifest" > "$tmp"
    mv "$tmp" "$manifest"
}

# Set a top-level field as null literal (jq distinguishes string "null" from JSON null).
manifest_set_null() {
    local manifest="$1" field="$2"
    local tmp
    tmp="$(mktemp)"
    jq ".$field = null" "$manifest" > "$tmp"
    mv "$tmp" "$manifest"
}
