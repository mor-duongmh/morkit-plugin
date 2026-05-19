#!/usr/bin/env bash
# sync-codex-fork.sh — regenerate skills-codex/ from skills/ by applying
# codex/vocab-map.yaml swap rules; refresh .codex/.drift-baseline (Task 4 of
# codex-fork-skills-clone).
#
# Why this exists:
#   skills-codex/ is a Codex-agent flavored mirror of skills/. Maintaining it
#   by hand drifts. This script consumes the vocab map (Task 3) and produces
#   the mirror deterministically. The accompanying baseline is what
#   check-codex-drift.sh (Task 2) compares against.
#
# Usage:
#   sync-codex-fork.sh [--source <dir>] [--target <dir>] [--map <yaml>]
#                      [--baseline <path>] [--exclude <pattern>] [--dry-run]
#
# Defaults (cascade-aware):
#   --source    ${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-<derived>}}/skills/
#   --target    .../skills-codex/
#   --map       .../codex/vocab-map.yaml
#   --baseline  .../.codex/.drift-baseline
#   --exclude   (repeatable) extra fnmatch-style patterns to skip; built-in
#               defaults always apply: __pycache__, *.pyc, .DS_Store. Patterns
#               match against the basename OR any path segment in the relpath
#               (so '__pycache__' skips the whole dir).
#
# Per-file action matrix:
#   in preserve list          → PRESERVE: cp src tgt (verbatim)
#   basename ∈ apply_to glob  → SWAP:     run apply-vocab-map.py
#   otherwise                 → ASSET:    cp src tgt (passthrough for .png etc)
#
# Output:
#   - stdout: per-file action lines (dry-run only) + final summary
#   - stderr: warnings, errors
#   - non-zero exit: preflight failed (python3/PyYAML/source dir missing,
#     vocab-map missing or malformed, baseline path unwritable)
#
# Dependencies: bash, python3 + PyYAML, find, sha256sum OR shasum, sort.

set -uo pipefail

# ---------------------------------------------------------------------------
# Locate plugin root via cascade (matches check-codex-drift.sh convention)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_ROOT="${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$DEFAULT_PLUGIN_ROOT}}"

SOURCE_DIR="$PLUGIN_ROOT/skills"
TARGET_DIR="$PLUGIN_ROOT/skills-codex"
VOCAB_MAP="$PLUGIN_ROOT/codex/vocab-map.yaml"
BASELINE="$PLUGIN_ROOT/.codex/.drift-baseline"
HELPER_PY="$SCRIPT_DIR/lib/apply-vocab-map.py"
DRY_RUN=0

# Built-in excludes — build artifacts and editor cruft that should never reach
# skills-codex/. User-supplied --exclude patterns append to this list.
EXCLUDE_PATTERNS=('__pycache__' '*.pyc' '.DS_Store')

# ---------------------------------------------------------------------------
# Arg parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --source)   SOURCE_DIR="$2"; shift 2 ;;
        --target)   TARGET_DIR="$2"; shift 2 ;;
        --map)      VOCAB_MAP="$2"; shift 2 ;;
        --baseline) BASELINE="$2";  shift 2 ;;
        --exclude)  EXCLUDE_PATTERNS+=("$2"); shift 2 ;;
        --dry-run)  DRY_RUN=1; shift ;;
        -h|--help)
            sed -n '2,30p' "$0"
            exit 0
            ;;
        *)
            echo "ERROR: unknown arg '$1'" >&2
            exit 2
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 required but not found in PATH" >&2
    exit 1
fi
if ! python3 -c 'import yaml' >/dev/null 2>&1; then
    echo "ERROR: PyYAML required (install: pip install pyyaml)" >&2
    exit 1
fi
if [[ ! -d "$SOURCE_DIR" ]]; then
    echo "ERROR: source dir not found: $SOURCE_DIR" >&2
    exit 1
fi
if [[ ! -f "$VOCAB_MAP" ]]; then
    echo "ERROR: vocab-map not found: $VOCAB_MAP" >&2
    exit 1
fi
if [[ ! -f "$HELPER_PY" ]]; then
    echo "ERROR: apply-vocab-map.py helper not found: $HELPER_PY" >&2
    exit 1
fi
# Baseline parent must be writable (or createable) — skip in dry-run.
if [[ "$DRY_RUN" -eq 0 ]]; then
    baseline_dir="$(dirname "$BASELINE")"
    if ! mkdir -p "$baseline_dir" 2>/dev/null; then
        echo "ERROR: cannot create baseline dir: $baseline_dir" >&2
        exit 1
    fi
    if [[ -e "$BASELINE" && ! -w "$BASELINE" ]]; then
        echo "ERROR: baseline not writable: $BASELINE" >&2
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Portable sha256 (mirrors check-codex-drift.sh)
# ---------------------------------------------------------------------------
_sha256() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" 2>/dev/null | awk '{print $1}'
    else
        shasum -a 256 "$1" 2>/dev/null | awk '{print $1}'
    fi
}
if ! command -v sha256sum >/dev/null 2>&1 && ! command -v shasum >/dev/null 2>&1; then
    echo "ERROR: neither sha256sum nor shasum available" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Load preserve list (newline-delimited) and apply_to globs (newline-delimited,
# unique) from vocab-map.yaml in one python invocation.
# Output format:
#   PRESERVE:<path>
#   GLOB:<pattern>
# ---------------------------------------------------------------------------
MAP_INFO=$(python3 <<PY 2>&1
import sys, yaml
try:
    with open("$VOCAB_MAP", "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
except Exception as e:
    print(f"__ERR__:{e}", file=sys.stderr)
    sys.exit(1)
preserves = data.get("preserve", []) or []
rules = data.get("rules", []) or []
globs = set()
for r in rules:
    for g in (r.get("apply_to") or []):
        globs.add(g)
for p in preserves:
    print(f"PRESERVE:{p}")
for g in sorted(globs):
    print(f"GLOB:{g}")
PY
)
if [[ "$MAP_INFO" == *"__ERR__"* ]]; then
    echo "ERROR: failed to load vocab-map: $MAP_INFO" >&2
    exit 1
fi

# Split into bash arrays (portable: read line-by-line)
PRESERVE_LIST=()
GLOB_LIST=()
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    case "$line" in
        PRESERVE:*) PRESERVE_LIST+=("${line#PRESERVE:}") ;;
        GLOB:*)     GLOB_LIST+=("${line#GLOB:}") ;;
    esac
done <<< "$MAP_INFO"

# Helpers — preserve membership + glob match
_in_preserve() {
    local rel="$1" p
    for p in "${PRESERVE_LIST[@]}"; do
        [[ "$rel" == "$p" ]] && return 0
    done
    return 1
}

_matches_any_glob() {
    local base="$1" g
    for g in "${GLOB_LIST[@]}"; do
        # bash extglob via case (no need for shopt extglob with simple `*` `?`)
        # shellcheck disable=SC2254
        case "$base" in
            $g) return 0 ;;
        esac
    done
    return 1
}

# True if relpath should be skipped per EXCLUDE_PATTERNS. A pattern matches if
# it fnmatches the basename OR any path segment (so `__pycache__` excludes the
# whole directory subtree without needing `__pycache__/*`).
_is_excluded() {
    local rel="$1" base pat seg
    base="$(basename "$rel")"
    for pat in "${EXCLUDE_PATTERNS[@]}"; do
        # shellcheck disable=SC2254
        case "$base" in
            $pat) return 0 ;;
        esac
        # Check each path segment for dir-style exclusions.
        local IFS='/'
        # shellcheck disable=SC2206
        local segments=( $rel )
        unset IFS
        for seg in "${segments[@]}"; do
            # shellcheck disable=SC2254
            case "$seg" in
                $pat) return 0 ;;
            esac
        done
    done
    return 1
}

# ---------------------------------------------------------------------------
# Walk source tree, classify each file, act (or report in dry-run)
# ---------------------------------------------------------------------------
SWAPPED=0
PRESERVED=0
ASSETS=0
EXCLUDED=0

# Sorted file list — stable output + deterministic baseline.
while IFS= read -r src; do
    [[ -z "$src" ]] && continue
    rel="${src#"$SOURCE_DIR/"}"
    base="$(basename "$src")"
    tgt="$TARGET_DIR/$rel"

    if _is_excluded "$rel"; then
        EXCLUDED=$((EXCLUDED + 1))
        if [[ "$DRY_RUN" -eq 1 ]]; then
            printf '%-9s %s\n' "EXCLUDE" "$rel"
        fi
        continue
    fi

    if _in_preserve "$rel"; then
        action="PRESERVE"
        PRESERVED=$((PRESERVED + 1))
    elif _matches_any_glob "$base"; then
        action="SWAP"
        SWAPPED=$((SWAPPED + 1))
    else
        action="ASSET"
        ASSETS=$((ASSETS + 1))
    fi

    if [[ "$DRY_RUN" -eq 1 ]]; then
        printf '%-9s %s\n' "$action" "$rel"
        continue
    fi

    # Perform the write
    mkdir -p "$(dirname "$tgt")" || {
        echo "ERROR: cannot mkdir $(dirname "$tgt")" >&2
        exit 1
    }
    case "$action" in
        SWAP)
            if ! python3 "$HELPER_PY" \
                --map "$VOCAB_MAP" \
                --input "$src" \
                --output "$tgt" 2>/tmp/_sync_err.$$; then
                rc=$?
                # Exit 3 = binary input → fall back to verbatim copy
                if [[ "$rc" -eq 3 ]]; then
                    cp "$src" "$tgt"
                    # Reclassify as ASSET in the summary
                    SWAPPED=$((SWAPPED - 1))
                    ASSETS=$((ASSETS + 1))
                else
                    echo "ERROR: swap failed for $rel (exit $rc):" >&2
                    cat /tmp/_sync_err.$$ >&2 2>/dev/null || true
                    rm -f /tmp/_sync_err.$$
                    exit 1
                fi
            fi
            rm -f /tmp/_sync_err.$$
            ;;
        PRESERVE|ASSET)
            cp "$src" "$tgt"
            ;;
    esac
done < <(find "$SOURCE_DIR" -type f 2>/dev/null | sort)

# ---------------------------------------------------------------------------
# Dry-run: report and exit
# ---------------------------------------------------------------------------
if [[ "$DRY_RUN" -eq 1 ]]; then
    total=$((SWAPPED + PRESERVED + ASSETS))
    echo ""
    echo "Dry-run summary: $total files would be processed " \
         "($SWAPPED SWAP, $PRESERVED PRESERVE, $ASSETS ASSET, " \
         "$EXCLUDED EXCLUDE). No writes performed."
    exit 0
fi

# ---------------------------------------------------------------------------
# Write baseline — sorted `<relpath>:<sha256>` lines, header preserved.
# ---------------------------------------------------------------------------
BASELINE_TMP="$(mktemp "${BASELINE}.XXXXXX")" || {
    echo "ERROR: cannot create temp baseline file" >&2
    exit 1
}

{
    # Header — preserve existing comment block if present, else write fresh.
    if [[ -f "$BASELINE" ]] && grep -q '^[[:space:]]*#' "$BASELINE"; then
        awk '/^[[:space:]]*#/ { print; next } /^[[:space:]]*$/ { print; next } { exit }' "$BASELINE"
    else
        cat <<'EOF'
# drift-baseline — generated by scripts/sync-codex-fork.sh.
# Format: <relpath-from-skills/>:<sha256>
# Do NOT edit by hand; re-run the sync script to refresh.
EOF
    fi
    # Data — every file we just wrote into target.
    # Apply the same exclude filter as the source walk so runtime artifacts
    # (e.g., .DS_Store, __pycache__/, .claude-flow/data/*) that may appear in
    # the target tree between syncs don't leak into the baseline.
    while IFS= read -r tgt; do
        [[ -z "$tgt" ]] && continue
        rel="${tgt#"$TARGET_DIR/"}"
        if _is_excluded "$rel"; then
            continue
        fi
        # Reject relpaths containing ':' (would break baseline parser)
        if [[ "$rel" == *:* ]]; then
            echo "ERROR: refusing to write baseline — relpath contains ':' ($rel)" >&2
            rm -f "$BASELINE_TMP"
            exit 1
        fi
        printf '%s:%s\n' "$rel" "$(_sha256 "$tgt")"
    done < <(find "$TARGET_DIR" -type f 2>/dev/null | sort)
} > "$BASELINE_TMP"

mv "$BASELINE_TMP" "$BASELINE" || {
    echo "ERROR: failed to install baseline" >&2
    rm -f "$BASELINE_TMP"
    exit 1
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
total=$((SWAPPED + PRESERVED + ASSETS))
echo "Synced $total files ($SWAPPED swapped via vocab map, " \
     "$PRESERVED preserved verbatim, $ASSETS assets passthrough, " \
     "$EXCLUDED excluded)."
echo "  target:   $TARGET_DIR"
echo "  baseline: $BASELINE"
