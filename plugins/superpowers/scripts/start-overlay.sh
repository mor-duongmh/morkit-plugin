#!/usr/bin/env bash
# start-overlay.sh — bootstrap a Mor overlay for an existing vendored path.
# Usage: ./start-overlay.sh <relative-path>

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

main() {
    if [[ $# -ne 1 ]]; then
        echo "Usage: start-overlay.sh <relative-path>" >&2
        echo "  e.g. start-overlay.sh skills/test-driven-development" >&2
        exit 2
    fi
    local rel="$1"
    require_commands jq
    local plugin_root_dir
    plugin_root_dir="$(plugin_root)"
    local source="$plugin_root_dir/$rel"
    local target="$plugin_root_dir/overlay/$rel"

    if [[ ! -e "$source" ]]; then
        echo "Source path does not exist: $source" >&2
        exit 1
    fi
    if [[ -e "$target" ]]; then
        echo "Overlay already exists at $target — refusing to overwrite." >&2
        exit 1
    fi

    mkdir -p "$(dirname "$target")"
    cp -R "$source" "$target"

    local manifest="$plugin_root_dir/.vendor-manifest.json"
    local version
    version="$(manifest_get "$manifest" version)"
    local now
    now="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

    cat > "$target/.overlay-meta.json" <<EOF
{
  "overlay_path": "$rel",
  "based_on_upstream_version": "$version",
  "created_at": "$now",
  "note": ""
}
EOF

    echo "✓ Overlay created at $target"
    echo "  Edit files in that directory, then run sync-superpowers.sh to apply."
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
