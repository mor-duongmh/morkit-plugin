#!/usr/bin/env bash
# migrate-from-openspec.sh — convert legacy openspec/changes/ to morkit/output/spec/
# (or to ${MORKIT_ROOT}/<name>/ if env override set).
#
# Usage:
#   migrate-from-openspec.sh [--dry-run] [--keep-openspec]
#
# Behaviour:
#   - If openspec/changes/ doesn't exist → no-op, exit 0.
#   - If primary morkit/output/spec/ already exists with content → refuse, exit 1.
#   - Otherwise, move openspec/changes/ → morkit/output/spec/ (preserving archive/ subfolder).
#   - Add .morkit marker in primary root.
#   - --keep-openspec: don't delete the (now-empty) openspec/ dir.
#
# Exit:
#   0 = success or no-op
#   1 = refused (conflict)
#   2 = bad usage

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
. "$SCRIPT_DIR/lib/common.sh"

DRY=0
KEEP_OPENSPEC=0

print_usage() {
    cat <<'EOF'
Usage: migrate-from-openspec.sh [--dry-run] [--keep-openspec] [--help]

Migrates legacy openspec/changes/ to ${MORKIT_ROOT:-morkit/output/spec}/.

Options:
  --dry-run           Print plan without modifying filesystem
  --keep-openspec     Keep the openspec/ directory after migration
  --help              Show help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)        print_usage; exit 0 ;;
        --dry-run)        DRY=1; shift ;;
        --keep-openspec)  KEEP_OPENSPEC=1; shift ;;
        *)                echo "Unknown option: $1" >&2; exit 2 ;;
    esac
done

LEGACY="openspec/changes"
PRIMARY="$(morkit_root)"

# No legacy → no-op
if [[ ! -d "$LEGACY" ]]; then
    echo "✓ No legacy openspec/changes/ found — nothing to migrate."
    exit 0
fi

# Conflict: primary already exists with content
if [[ -d "$PRIMARY" ]]; then
    if find "$PRIMARY" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | grep -q .; then
        cat >&2 <<EOF
✗ Conflict: both $LEGACY/ and $PRIMARY/ exist with content.

Manual resolution required. Inspect both folders and:
  - Move desired changes from $LEGACY/<name> to $PRIMARY/<name>
  - Delete $LEGACY/ when done
  - Re-run this script to verify
EOF
        exit 1
    fi
fi

# Plan
echo "Migration plan:"
echo "  Source:      $LEGACY/"
echo "  Destination: $PRIMARY/"
echo ""
echo "Changes to migrate:"
find "$LEGACY" -mindepth 1 -maxdepth 1 -type d | while read -r d; do
    echo "  - $(basename "$d")"
done

if [[ "$DRY" -eq 1 ]]; then
    echo ""
    echo "(--dry-run: no filesystem changes performed)"
    exit 0
fi

# Execute
mkdir -p "$(dirname "$PRIMARY")"
if [[ ! -d "$PRIMARY" ]]; then
    mv "$LEGACY" "$PRIMARY"
else
    # PRIMARY is empty — move contents
    if find "$LEGACY" -mindepth 1 -maxdepth 1 2>/dev/null | grep -q .; then
        mv "$LEGACY"/* "$PRIMARY/" 2>/dev/null || true
        mv "$LEGACY"/.[!.]* "$PRIMARY/" 2>/dev/null || true
    fi
    rmdir "$LEGACY" 2>/dev/null || true
fi

# Marker
ensure_marker

# Cleanup empty openspec/
if [[ "$KEEP_OPENSPEC" -ne 1 ]]; then
    if [[ -d openspec ]] && [[ -z "$(find openspec -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
        rmdir openspec 2>/dev/null || true
    fi
fi

echo ""
echo "✓ Migration complete."
echo "  Primary:  $PRIMARY/"
echo "  Marker:   $PRIMARY/.morkit"
[[ "$KEEP_OPENSPEC" -eq 1 ]] && echo "  Legacy preserved: openspec/"

# ---------------------------------------------------------------------------
# Post-migration validation: run validate-tasks.sh on each migrated tasks.md
# v1 schemas may not satisfy v2 rules (R1-R6). Surface violations as warnings,
# not errors — migration itself succeeded; validation is advisory.
# ---------------------------------------------------------------------------
VALIDATE="$SCRIPT_DIR/validate-tasks.sh"
if [[ -x "$VALIDATE" ]]; then
    echo ""
    echo "Validating migrated tasks.md files against v2 schema..."
    VIOLATIONS=0
    while IFS= read -r tasks_file; do
        if ! "$VALIDATE" "$tasks_file" >/dev/null 2>&1; then
            VIOLATIONS=$((VIOLATIONS + 1))
            echo "  ⚠ $tasks_file does not pass v2 schema (run validate-tasks.sh for details)"
        fi
    done < <(find "$PRIMARY" -mindepth 2 -maxdepth 3 -name 'tasks.md' -not -path "*/archive/*" 2>/dev/null)

    if [[ "$VIOLATIONS" -gt 0 ]]; then
        echo ""
        echo "  $VIOLATIONS migrated change(s) need manual schema fixup."
        echo "  Run: bash \${CLAUDE_PLUGIN_ROOT}/scripts/validate-tasks.sh --explain"
    else
        echo "  ✓ All migrated tasks.md pass v2 schema."
    fi
fi

echo ""
echo "Next: re-run /morkit:executing-plans or /morkit:review to verify the migration."
