#!/usr/bin/env bash
# sync-superpowers.sh — refresh the vendored Superpowers layer from upstream.
# Usage:
#   ./sync-superpowers.sh                    Use version pinned in .vendor-manifest.json
#   ./sync-superpowers.sh <version>          Bump to specific upstream tag (e.g. 5.1.0)
#   ./sync-superpowers.sh --dry-run [<ver>]  Show what would change without writing
#   ./sync-superpowers.sh --help             Show this help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

DRY_RUN=0
TARGET_VERSION=""

print_usage() {
    cat <<'EOF'
Usage: sync-superpowers.sh [--dry-run] [--help] [<version>]

Refresh the vendored Superpowers layer from obra/superpowers.

Options:
  --dry-run    Print actions without writing files
  --help       Show this help

Arguments:
  <version>    Upstream tag to sync (e.g. 5.1.0). If omitted, the version
               pinned in .vendor-manifest.json is used.

Examples:
  sync-superpowers.sh                  # use pinned version
  sync-superpowers.sh 5.1.0            # bump to 5.1.0
  sync-superpowers.sh --dry-run 5.1.0  # preview only
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                print_usage
                exit 0
                ;;
            --dry-run)
                DRY_RUN=1
                shift
                ;;
            -*)
                echo "Unknown option: $1" >&2
                print_usage >&2
                exit 2
                ;;
            *)
                if [[ -z "$TARGET_VERSION" ]]; then
                    TARGET_VERSION="$1"
                    shift
                else
                    echo "Unexpected extra argument: $1" >&2
                    exit 2
                fi
                ;;
        esac
    done
}

resolve_version() {
    local manifest="$PLUGIN_ROOT/.vendor-manifest.json"
    if [[ -n "$TARGET_VERSION" ]]; then
        echo "$TARGET_VERSION"
        return
    fi
    local pinned
    pinned="$(manifest_get "$manifest" version)"
    if [[ "$pinned" == "null" ]]; then
        echo "No version pinned in manifest. Pass version explicitly: ./sync-superpowers.sh <version>" >&2
        exit 1
    fi
    echo "$pinned"
}

print_dry_run_plan() {
    local version="$1"
    cat <<EOF
=== DRY RUN ===
Target version: $version
Tarball URL:    https://github.com/obra/superpowers/archive/refs/tags/v$version.tar.gz

Plan:
  1. would download tarball to /tmp
  2. would compute SHA256 and verify against manifest (or store if first sync)
  3. would extract to a tempdir
  4. would wipe: \$PLUGIN_ROOT/skills \$PLUGIN_ROOT/commands \$PLUGIN_ROOT/agents \$PLUGIN_ROOT/LICENSE
  5. would copy from extracted tree
  6. would apply overlay/ on top
  7. would update .vendor-manifest.json

No files were written.
EOF
}

check_git_clean() {
    local plugin_root="$1"
    local dirty
    dirty="$(cd "$plugin_root" && git status --porcelain skills/ commands/ agents/ LICENSE 2>/dev/null || true)"
    if [[ -n "$dirty" ]]; then
        echo "Refusing to sync: vendored layer has uncommitted changes." >&2
        echo "Commit, stash, or discard them before running sync." >&2
        echo "$dirty" >&2
        exit 1
    fi
}

download_tarball() {
    local version="$1" dest="$2"
    local url="https://github.com/obra/superpowers/archive/refs/tags/v${version}.tar.gz"
    echo "Downloading $url"
    if ! curl -fsSL "$url" -o "$dest"; then
        echo "Download failed for $url" >&2
        exit 1
    fi
}

verify_or_record_sha256() {
    # Args: tarball_path manifest_path target_version
    # Prints the actual sha as last line for caller to capture.
    local tarball="$1" manifest="$2" version="$3"
    local actual
    actual="$(compute_sha256 "$tarball")"
    local recorded_version recorded_sha
    recorded_version="$(manifest_get "$manifest" version)"
    recorded_sha="$(manifest_get "$manifest" tarball_sha256)"
    if [[ "$recorded_version" == "$version" && "$recorded_sha" != "null" ]]; then
        if [[ "$actual" != "$recorded_sha" ]]; then
            echo "SHA256 mismatch for v$version!" >&2
            echo "  expected: $recorded_sha" >&2
            echo "  actual:   $actual" >&2
            exit 1
        fi
        echo "✓ SHA256 verified: $actual" >&2
    else
        echo "✓ SHA256 computed (first sync of v$version): $actual" >&2
    fi
    echo "$actual"
}

extract_tarball() {
    local tarball="$1" dest="$2"
    mkdir -p "$dest"
    tar -xzf "$tarball" -C "$dest"
    local extracted_root
    extracted_root="$(find "$dest" -mindepth 1 -maxdepth 1 -type d | head -1)"
    echo "$extracted_root"
}

wipe_vendored_layer() {
    local plugin_root="$1"
    rm -rf "$plugin_root/skills" "$plugin_root/commands" "$plugin_root/agents" "$plugin_root/LICENSE"
}

copy_vendored_layer() {
    local src="$1" plugin_root="$2"
    for path in skills commands agents LICENSE; do
        if [[ -e "$src/$path" ]]; then
            cp -R "$src/$path" "$plugin_root/$path"
        fi
    done
}

apply_overlay() {
    local plugin_root="$1"
    local overlay="$plugin_root/overlay"
    [[ -d "$overlay" ]] || return 0
    local applied=0
    for sub in skills commands agents; do
        [[ -d "$overlay/$sub" ]] || continue
        cp -R "$overlay/$sub/." "$plugin_root/$sub/"
        applied=$((applied + 1))
    done
    if [[ "$applied" -gt 0 ]]; then
        echo "✓ Applied overlay layer"
    fi
}

update_manifest() {
    local manifest="$1" version="$2" sha="$3"
    local url="https://github.com/obra/superpowers/archive/refs/tags/v${version}.tar.gz"
    local now
    now="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    manifest_set "$manifest" version "$version"
    manifest_set "$manifest" tarball_url "$url"
    manifest_set "$manifest" tarball_sha256 "$sha"
    manifest_set "$manifest" fetched_at "$now"
}

confirm_or_abort() {
    local current="$1" target="$2"
    echo
    echo "Sync vendored Superpowers layer"
    echo "  Current: ${current}"
    echo "  Target:  ${target}"
    read -r -p "Continue? [y/N]: " ans
    if [[ "$ans" != "y" && "$ans" != "Y" ]]; then
        echo "Aborted by user."
        exit 0
    fi
}

main() {
    parse_args "$@"
    PLUGIN_ROOT="$(plugin_root)"
    require_commands curl tar jq git

    local manifest="$PLUGIN_ROOT/.vendor-manifest.json"
    local version
    version="$(resolve_version)"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        print_dry_run_plan "$version"
        exit 0
    fi

    local current
    current="$(manifest_get "$manifest" version)"
    if [[ "$current" == "$version" ]]; then
        echo "✓ already at v$version (manifest matches target). Nothing to do."
        echo "  To force re-fetch, manually clear .vendor-manifest.json version field."
        exit 0
    fi

    check_git_clean "$PLUGIN_ROOT"
    confirm_or_abort "$current" "$version"

    SYNC_TMP="$(mktemp -d)"
    trap 'rm -rf "${SYNC_TMP:-}"' EXIT
    local tmp="$SYNC_TMP"

    local tarball="$tmp/superpowers-v${version}.tar.gz"
    download_tarball "$version" "$tarball"

    local sha
    sha="$(verify_or_record_sha256 "$tarball" "$manifest" "$version" | tail -1)"

    local extract_dir="$tmp/extract"
    local extracted
    extracted="$(extract_tarball "$tarball" "$extract_dir")"

    wipe_vendored_layer "$PLUGIN_ROOT"
    copy_vendored_layer "$extracted" "$PLUGIN_ROOT"
    apply_overlay "$PLUGIN_ROOT"
    update_manifest "$manifest" "$version" "$sha"

    echo
    echo "✓ Vendored layer synced to v$version"
    echo "  SHA256: $sha"
    echo
    echo "Suggested commit:"
    echo "  git add plugins/superpowers/{skills,commands,agents,LICENSE,.vendor-manifest.json}"
    echo "  git commit -m \"chore(superpowers): vendor upstream v$version\""
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
