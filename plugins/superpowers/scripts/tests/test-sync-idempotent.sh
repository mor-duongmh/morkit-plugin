#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helper.sh"

SYNC="$SCRIPT_DIR/../sync-superpowers.sh"
PLUGIN_ROOT="$SCRIPT_DIR/../.."
TEST_VERSION="5.0.7"

backup="$(mktemp -d)"
for d in skills commands agents LICENSE; do
    [[ -e "$PLUGIN_ROOT/$d" ]] && mv "$PLUGIN_ROOT/$d" "$backup/$d"
done
manifest_backup="$(cat "$PLUGIN_ROOT/.vendor-manifest.json")"

cleanup() {
    rm -rf "$PLUGIN_ROOT/skills" "$PLUGIN_ROOT/commands" "$PLUGIN_ROOT/agents" "$PLUGIN_ROOT/LICENSE"
    for d in skills commands agents LICENSE; do
        [[ -e "$backup/$d" ]] && mv "$backup/$d" "$PLUGIN_ROOT/$d"
    done
    echo "$manifest_backup" > "$PLUGIN_ROOT/.vendor-manifest.json"
    rm -rf "$backup"
}
trap cleanup EXIT

# First sync
echo "y" | "$SYNC" "$TEST_VERSION" >/dev/null

sha_first="$(jq -r .tarball_sha256 "$PLUGIN_ROOT/.vendor-manifest.json")"
mtime_first="$(stat -f %m "$PLUGIN_ROOT/skills/brainstorming/SKILL.md" 2>/dev/null || stat -c %Y "$PLUGIN_ROOT/skills/brainstorming/SKILL.md")"

# Second sync (same version)
output="$(echo "y" | "$SYNC" "$TEST_VERSION" 2>&1)"
assert_contains "$output" "already at v$TEST_VERSION" "idempotent skip message"

sha_second="$(jq -r .tarball_sha256 "$PLUGIN_ROOT/.vendor-manifest.json")"
assert_equal "$sha_second" "$sha_first" "sha unchanged"

mtime_second="$(stat -f %m "$PLUGIN_ROOT/skills/brainstorming/SKILL.md" 2>/dev/null || stat -c %Y "$PLUGIN_ROOT/skills/brainstorming/SKILL.md")"
assert_equal "$mtime_second" "$mtime_first" "skill file mtime unchanged"

echo "PASS: test-sync-idempotent"
