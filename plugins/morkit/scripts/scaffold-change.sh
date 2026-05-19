#!/usr/bin/env bash
# scaffold-change.sh — create a new spec change folder with proposal/design/tasks
# templates and .meta.json. Replaces `npx openspec new change`.
#
# Usage:
#   scaffold-change.sh [--force] <name>
#
# Args:
#   <name>     Kebab-case identifier (e.g. "add-csv-export")
#   --force    Overwrite an existing folder
#
# Output: writes to ${MORKIT_ROOT:-morkit/output/spec}/<name>/{proposal,design,tasks}.md
#         + .meta.json + ensures ${MORKIT_ROOT}/.morkit marker
#
# Exit codes:
#   0  success
#   1  validation / filesystem error
#   2  bad usage

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
. "$SCRIPT_DIR/lib/common.sh"

FORCE=0
NAME=""

print_usage() {
    cat <<'EOF'
Usage: scaffold-change.sh [--force] <name>

Creates a new spec change folder under ${MORKIT_ROOT:-morkit/output/spec}/<name>/
with proposal.md, design.md, tasks.md, and .meta.json.

Options:
  --force    Overwrite an existing folder
  --help     Show this help

Env:
  MORKIT_ROOT          Override the changes folder (default: morkit/output/spec)
  MORKIT_PLUGIN_ROOT   Plugin root (falls back to CLAUDE_PLUGIN_ROOT, then auto-derived from script location)
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) print_usage; exit 0 ;;
        --force)   FORCE=1; shift ;;
        --)        shift; break ;;
        -*)        echo "Unknown option: $1" >&2; print_usage >&2; exit 2 ;;
        *)
            if [[ -z "$NAME" ]]; then NAME="$1"; shift
            else echo "✗ Unexpected arg: $1" >&2; exit 2; fi
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------
if [[ -z "$NAME" ]]; then
    print_usage >&2
    exit 2
fi

if is_reserved_name "$NAME"; then
    echo "✗ '$NAME' is a reserved name (cannot be used as a change name)." >&2
    exit 1
fi

if ! is_kebab_case "$NAME"; then
    cat >&2 <<EOF
✗ Invalid change name: '$NAME'

Names must be kebab-case:
  - lowercase letters, digits, and dashes only
  - start with a letter
  - no consecutive dashes
  - no leading/trailing dash

Example: 'add-csv-export', 'fix-login-bug', 'refactor-auth'
EOF
    exit 1
fi

ensure_jq

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
PLUGIN_ROOT="$(plugin_root "${BASH_SOURCE[0]}")"
TEMPLATES_DIR="$PLUGIN_ROOT/templates"

if [[ ! -d "$TEMPLATES_DIR" ]]; then
    echo "✗ Templates dir missing: $TEMPLATES_DIR" >&2
    exit 1
fi

ROOT="$(morkit_root)"
TARGET="$ROOT/$NAME"

# ---------------------------------------------------------------------------
# Existence check + safety: --force only removes paths confirmed to be
# nested under CWD/$ROOT (defense against MORKIT_ROOT=/ misconfiguration).
# ---------------------------------------------------------------------------
if [[ -e "$TARGET" ]]; then
    if [[ "$FORCE" -ne 1 ]]; then
        echo "✗ '$TARGET' already exists. Use --force to overwrite." >&2
        exit 1
    fi
    # Resolve absolute path; refuse to rm anything outside CWD.
    ABS_TARGET="$(cd "$(dirname "$TARGET")" 2>/dev/null && pwd)/$(basename "$TARGET")" || ABS_TARGET=""
    ABS_CWD="$(pwd)"
    if [[ -z "$ABS_TARGET" ]] || [[ "$ABS_TARGET" != "$ABS_CWD"/* ]]; then
        echo "✗ Refusing --force: target '$TARGET' resolves outside cwd." >&2
        echo "  Resolved: $ABS_TARGET" >&2
        echo "  CWD:      $ABS_CWD" >&2
        exit 1
    fi
    # Also refuse if target == cwd or target is a top-level dir like / or $HOME.
    if [[ "$ABS_TARGET" == "$ABS_CWD" ]] || [[ "$ABS_TARGET" == "/" ]] || [[ "$ABS_TARGET" == "$HOME" ]]; then
        echo "✗ Refusing --force: target '$ABS_TARGET' is too broad." >&2
        exit 1
    fi
    rm -rf "$ABS_TARGET"
fi

# ---------------------------------------------------------------------------
# Create dirs and ensure marker
# ---------------------------------------------------------------------------
mkdir -p "$TARGET" || { echo "✗ Cannot create $TARGET" >&2; exit 1; }
ensure_marker

# ---------------------------------------------------------------------------
# Render templates
# ---------------------------------------------------------------------------
NOW="$(iso_now)"

render() {
    local src="$1"
    local dst="$2"
    if [[ ! -f "$src" ]]; then
        echo "✗ Template missing: $src" >&2
        return 1
    fi
    sed -e "s|{{NAME}}|$NAME|g" -e "s|{{GENERATED_AT}}|$NOW|g" "$src" > "$dst"
}

render "$TEMPLATES_DIR/proposal.md.tpl" "$TARGET/proposal.md"
render "$TEMPLATES_DIR/design.md.tpl"   "$TARGET/design.md"
render "$TEMPLATES_DIR/tasks.md.tpl"    "$TARGET/tasks.md"

# ---------------------------------------------------------------------------
# Write .meta.json (atomic)
# ---------------------------------------------------------------------------
META="$TARGET/.meta.json"
jq -n \
    --arg name "$NAME" \
    --arg created_at "$NOW" \
    --argjson schema_version "$MORKIT_SCHEMA_VERSION" \
    '{
        name: $name,
        created_at: $created_at,
        schema_version: $schema_version,
        archived: false
    }' > "$META.tmp"
mv "$META.tmp" "$META"

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
echo "✓ Created $TARGET"
echo "  Files:"
echo "    - $TARGET/proposal.md"
echo "    - $TARGET/design.md"
echo "    - $TARGET/tasks.md"
echo "    - $TARGET/.meta.json"
echo "  Marker: $ROOT/.morkit"
echo ""
echo "Next steps:"
echo "  1. Edit proposal.md, design.md, tasks.md"
echo "  2. Run: /morkit:review (generate review-checklist from Google Doc)"
echo "  3. Tick checklist items, set 'Overall Decision: OK'"
echo "  4. Run: /morkit:executing-plans"
