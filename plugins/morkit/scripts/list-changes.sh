#!/usr/bin/env bash
# list-changes.sh — list spec changes in ${MORKIT_ROOT:-morkit/output/spec}/
# Replaces `npx openspec list`.
#
# Usage:
#   list-changes.sh [--json] [--include-archived]
#
# Options:
#   --json                Emit JSON array (default: text)
#   --include-archived    Include archive/ subfolder entries
#   --help                Show help
#
# Output (JSON):
#   [{ "name": "...", "created_at": "...", "schema_version": 1, "archived": false,
#      "mtime": <epoch>, "meta_corrupt": false }]
#
# Sorted: newest mtime first.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
. "$SCRIPT_DIR/lib/common.sh"

JSON=0
INCLUDE_ARCHIVED=0

print_usage() {
    cat <<'EOF'
Usage: list-changes.sh [--json] [--include-archived] [--help]
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)            print_usage; exit 0 ;;
        --json)               JSON=1; shift ;;
        --include-archived)   INCLUDE_ARCHIVED=1; shift ;;
        *)                    echo "Unknown option: $1" >&2; exit 2 ;;
    esac
done

ensure_jq

ROOT="$(morkit_root)"

# No folder → empty result
if [[ ! -d "$ROOT" ]]; then
    if [[ "$JSON" -eq 1 ]]; then echo "[]"; fi
    exit 0
fi

# Collect entries as NDJSON (one JSON object per line); convert to array at end.
# This reduces jq invocations from 2N+1 to roughly N+1 (one per entry + final slurp).
emit_entries() {
    local base="$1"
    local archived_flag="$2"
    [[ -d "$base" ]] || return 0
    local d
    while IFS= read -r -d '' d; do
        local name; name="$(basename "$d")"
        if is_reserved_name "$name"; then continue; fi
        local mtime; mtime="$(file_mtime "$d")"
        local meta="$d/.meta.json"
        if [[ -f "$meta" ]] && jq empty "$meta" >/dev/null 2>&1; then
            jq -c \
                --arg name "$name" \
                --argjson mtime "$mtime" \
                --argjson archived "$archived_flag" \
                '. + {name: $name, mtime: $mtime, archived: $archived, meta_corrupt: false}' \
                "$meta"
        else
            jq -nc \
                --arg name "$name" \
                --argjson mtime "$mtime" \
                --argjson archived "$archived_flag" \
                '{name: $name, mtime: $mtime, archived: $archived, meta_corrupt: true, schema_version: null, created_at: null}'
        fi
    done < <(find "$base" -mindepth 1 -maxdepth 1 -type d ! -name 'archive' -print0 2>/dev/null)
}

# Slurp NDJSON into a single sorted array (one final jq call)
SORTED="$(
    {
        emit_entries "$ROOT" false
        if [[ "$INCLUDE_ARCHIVED" -eq 1 ]]; then
            emit_entries "$ROOT/archive" true
        fi
    } | jq -sc 'sort_by(-.mtime)'
)"
[[ -z "$SORTED" ]] && SORTED='[]'

if [[ "$JSON" -eq 1 ]]; then
    echo "$SORTED"
else
    # Human-readable
    if [[ "$(printf '%s' "$SORTED" | jq 'length')" -eq 0 ]]; then
        echo "(no changes)"
        exit 0
    fi
    printf "%-40s  %-25s  %-10s\n" "NAME" "CREATED" "STATUS"
    printf '%s' "$SORTED" | jq -r '.[] | [.name, (.created_at // "-"), (if .archived then "archived" elif .meta_corrupt then "corrupt" else "active" end)] | @tsv' \
        | while IFS=$'\t' read -r name created status; do
            printf "%-40s  %-25s  %-10s\n" "$name" "$created" "$status"
          done
fi
