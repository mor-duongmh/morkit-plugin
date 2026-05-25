#!/usr/bin/env bash
# fetch-checklist.sh — fetch the Mor Developer Review Checklist from the canonical
# Google Doc, with 24h cache fallback.
#
# Output: full markdown of the doc on stdout.
# Behaviour:
#   - Cache fresh (<24h)        → cat cache, exit 0
#   - Cache stale, fetch ok     → update cache, cat fresh, exit 0
#   - Cache stale, fetch fail   → cat stale cache + warn on stderr, exit 0
#   - No cache, fetch fail      → error to stderr, exit 1
#
# Args:
#   --refresh   Force fetch (ignore cache TTL)
#   --help      Show this help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"   # provides file_mtime

DOC_URL="https://docs.google.com/document/d/184wY2N2WOUExmZrClvHCfcRCnSQsJYvav6gc6JwL6xc/export?format=md"
CACHE_DIR="${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data}}/spec"
CACHE_FILE="$CACHE_DIR/.checklist-cache.md"
TTL_SECONDS=$((24 * 3600))
FORCE_REFRESH=0

print_usage() {
    cat <<'EOF'
Usage: fetch-checklist.sh [--refresh] [--help]

Fetches the Mor Developer Review Checklist (Google Doc) and prints to stdout.
Cached at ${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-~/.claude/plugins/data}}/spec/.checklist-cache.md for 24h.

Options:
  --refresh   Bypass cache TTL and fetch fresh
  --help      Show this help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) print_usage; exit 0 ;;
        --refresh) FORCE_REFRESH=1; shift ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
    esac
done

mkdir -p "$CACHE_DIR" 2>/dev/null || true

cache_age() {
    [[ -f "$CACHE_FILE" ]] || { echo 99999999; return; }
    echo $(( $(date +%s) - $(file_mtime "$CACHE_FILE") ))
}

# Use cache if fresh and not forcing
if [[ "$FORCE_REFRESH" -eq 0 ]] && [[ -f "$CACHE_FILE" ]]; then
    age="$(cache_age)"
    if [[ "$age" -lt "$TTL_SECONDS" ]]; then
        cat "$CACHE_FILE"
        exit 0
    fi
fi

# Try fresh fetch
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

if curl -fsSL --max-time 15 "$DOC_URL" -o "$TMP" 2>/dev/null; then
    # Sanity check: response should contain known checklist anchor
    if grep -q "Plan Review Checklist" "$TMP" 2>/dev/null \
       || grep -q "BE - Feature" "$TMP" 2>/dev/null \
       || grep -q "Developer_Review_Checklist" "$TMP" 2>/dev/null; then
        mv "$TMP" "$CACHE_FILE"
        cat "$CACHE_FILE"
        exit 0
    else
        echo "⚠ fetch-checklist: response doesn't look like the checklist (sharing may have been revoked)." >&2
    fi
fi

# Fetch failed — fall back to stale cache
if [[ -f "$CACHE_FILE" ]]; then
    age="$(cache_age)"
    days=$(( age / 86400 ))
    echo "⚠ fetch-checklist: live fetch failed; using cache (${days} days old)." >&2
    cat "$CACHE_FILE"
    exit 0
fi

# No cache and no fresh — fail loud
cat >&2 <<EOF
✗ fetch-checklist: cannot fetch and no cache available.
  URL:   $DOC_URL
  Cache: $CACHE_FILE

  Causes:
    - Google Doc sharing changed (no longer "anyone with link can view")
    - No network connectivity
    - URL changed (update DOC_URL constant in this script)
EOF
exit 1
