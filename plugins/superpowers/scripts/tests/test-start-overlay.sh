#!/usr/bin/env bash
# start-overlay.sh copies a live skill into overlay/ and creates .overlay-meta.json.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helper.sh"

START="$SCRIPT_DIR/../start-overlay.sh"
PLUGIN_ROOT="$SCRIPT_DIR/../.."
TARGET="skills/brainstorming"

# Backup overlay
backup="$(mktemp -d)"
[[ -e "$PLUGIN_ROOT/overlay/$TARGET" ]] && cp -R "$PLUGIN_ROOT/overlay/$TARGET" "$backup/"
cleanup() {
    rm -rf "$PLUGIN_ROOT/overlay/$TARGET"
    if [[ -e "$backup/$(basename "$TARGET")" ]]; then
        mkdir -p "$PLUGIN_ROOT/overlay/$(dirname "$TARGET")"
        cp -R "$backup/$(basename "$TARGET")" "$PLUGIN_ROOT/overlay/$(dirname "$TARGET")/"
    fi
    rm -rf "$backup"
}
trap cleanup EXIT

# Run helper
"$START" "$TARGET"

# Assertions
assert_dir_exists "$PLUGIN_ROOT/overlay/$TARGET" "overlay dir created"
assert_file_exists "$PLUGIN_ROOT/overlay/$TARGET/SKILL.md" "skill content copied"
assert_file_exists "$PLUGIN_ROOT/overlay/$TARGET/.overlay-meta.json" ".overlay-meta.json created"

base_version="$(jq -r .based_on_upstream_version "$PLUGIN_ROOT/overlay/$TARGET/.overlay-meta.json")"
manifest_version="$(jq -r .version "$PLUGIN_ROOT/.vendor-manifest.json")"
assert_equal "$base_version" "$manifest_version" "meta records current upstream version"

echo "PASS: test-start-overlay"
