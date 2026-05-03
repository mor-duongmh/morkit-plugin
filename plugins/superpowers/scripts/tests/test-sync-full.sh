#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helper.sh"

SYNC="$SCRIPT_DIR/../sync-superpowers.sh"
PLUGIN_ROOT="$SCRIPT_DIR/../.."

TEST_VERSION="5.0.7"

# Backup live folders if any
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

# Run full sync (auto-confirm with 'y')
echo "y" | "$SYNC" "$TEST_VERSION"

# Verify file structure
assert_dir_exists "$PLUGIN_ROOT/skills/brainstorming" "brainstorming skill present"
assert_dir_exists "$PLUGIN_ROOT/skills/executing-plans" "executing-plans skill present"
assert_file_exists "$PLUGIN_ROOT/skills/brainstorming/SKILL.md" "SKILL.md present"
assert_file_exists "$PLUGIN_ROOT/commands/brainstorm.md" "brainstorm command present"
assert_file_exists "$PLUGIN_ROOT/LICENSE" "LICENSE present"

skill_count="$(find "$PLUGIN_ROOT/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
assert_equal "$skill_count" "14" "14 skill dirs"

manifest_version="$(jq -r .version "$PLUGIN_ROOT/.vendor-manifest.json")"
assert_equal "$manifest_version" "$TEST_VERSION" "manifest version updated"

manifest_sha="$(jq -r .tarball_sha256 "$PLUGIN_ROOT/.vendor-manifest.json")"
[[ ${#manifest_sha} -eq 64 ]] || { echo "FAIL: tarball_sha256 not 64 chars" >&2; exit 1; }

manifest_fetched_at="$(jq -r .fetched_at "$PLUGIN_ROOT/.vendor-manifest.json")"
assert_contains "$manifest_fetched_at" "T" "fetched_at is ISO8601-ish"

echo "PASS: test-sync-full"
