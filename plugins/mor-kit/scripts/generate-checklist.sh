#!/usr/bin/env bash
# generate-checklist.sh — generate review-checklist.md for an OpenSpec change.
#
# Workflow:
#   1. Detect variant (BE|FE × Feature|Bug Fix|Refactor) from proposal.md + tasks.md.
#   2. Fetch the canonical Google Doc (with 24h cache fallback) via fetch-checklist.sh.
#   3. Extract the matching variant section.
#   4. Inject metadata header (change name, paths, generated_at).
#   5. Write to <change-dir>/review-checklist.md.
#
# Args: <change-dir>           Path to the OpenSpec change folder
#       --variant <BE-Feature> Optional override (e.g. "BE-Feature", "FE-BugFix", "BE-Refactor")
#       --refresh              Force fetch (passed to fetch-checklist.sh)
#       --help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FETCH="$SCRIPT_DIR/fetch-checklist.sh"

CHANGE_DIR=""
VARIANT_OVERRIDE=""
REFRESH=0

print_usage() {
    cat <<'EOF'
Usage: generate-checklist.sh <change-dir> [--variant <id>] [--refresh] [--help]

Detects variant, fetches the Mor Developer Review Checklist from the canonical
Google Doc, extracts the matching section, and writes <change-dir>/review-checklist.md.

<change-dir> typically resolves to "${MOR_KIT_ROOT:-mor-kit/changes}/<name>". Any
folder containing proposal.md and tasks.md works.

Variant ids (override --variant):
  BE-Feature, BE-BugFix, BE-Refactor, FE-Feature, FE-BugFix, FE-Refactor
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) print_usage; exit 0 ;;
        --variant) VARIANT_OVERRIDE="$2"; shift 2 ;;
        --refresh) REFRESH=1; shift ;;
        *)
            if [[ -z "$CHANGE_DIR" ]]; then CHANGE_DIR="$1"; shift
            else echo "Unexpected arg: $1" >&2; exit 2; fi
            ;;
    esac
done

[[ -n "$CHANGE_DIR" ]] || { print_usage >&2; exit 2; }
[[ -d "$CHANGE_DIR" ]] || { echo "✗ Change dir does not exist: $CHANGE_DIR" >&2; exit 1; }

PROPOSAL="$CHANGE_DIR/proposal.md"
TASKS="$CHANGE_DIR/tasks.md"
TARGET="$CHANGE_DIR/review-checklist.md"

# ---------------------------------------------------------------------------
# Step 1: detect variant
# ---------------------------------------------------------------------------
detect_variant() {
    local side="BE"
    local type="Feature"

    # FE signals: file paths in tasks.md mentioning frontend conventions
    if [[ -f "$TASKS" ]] && grep -qiE 'frontend/|src/components/|src/pages/|\.tsx|\.jsx|\.vue|\.svelte|next\.config|tailwind\.config|public/' "$TASKS"; then
        side="FE"
    fi

    # Type signals: scan proposal.md
    if [[ -f "$PROPOSAL" ]]; then
        if grep -qiE '\b(bug|fix|regression|crash|error|broken|defect)\b' "$PROPOSAL"; then
            type="Bug Fix"
        elif grep -qiE '\b(refactor|cleanup|simplify|rename|restructure|modernize|tech.debt)\b' "$PROPOSAL"; then
            type="Refactor"
        fi
    fi

    echo "$side|$type"
}

# Map a friendly variant id (BE-Feature etc) to the canonical "BE - Feature".
expand_variant_id() {
    case "$1" in
        BE-Feature)  echo "BE|Feature" ;;
        BE-BugFix)   echo "BE|Bug Fix" ;;
        BE-Refactor) echo "BE|Refactor" ;;
        FE-Feature)  echo "FE|Feature" ;;
        FE-BugFix)   echo "FE|Bug Fix" ;;
        FE-Refactor) echo "FE|Refactor" ;;
        *) echo "" ;;
    esac
}

if [[ -n "$VARIANT_OVERRIDE" ]]; then
    pair="$(expand_variant_id "$VARIANT_OVERRIDE")"
    [[ -n "$pair" ]] || { echo "✗ Invalid --variant: $VARIANT_OVERRIDE" >&2; exit 2; }
else
    pair="$(detect_variant)"
fi
SIDE="${pair%|*}"
TYPE="${pair#*|}"

# ---------------------------------------------------------------------------
# Step 2: fetch the doc
# ---------------------------------------------------------------------------
DOC_TMP="$(mktemp)"
trap 'rm -f "$DOC_TMP"' EXIT

if [[ "$REFRESH" -eq 1 ]]; then
    "$FETCH" --refresh > "$DOC_TMP" || { echo "✗ Fetch failed" >&2; exit 3; }
else
    "$FETCH" > "$DOC_TMP" || { echo "✗ Fetch failed" >&2; exit 3; }
fi

# ---------------------------------------------------------------------------
# Step 3: extract the matching variant section.
# Header format in Google Doc export uses an escaped hyphen: "## BE \\- Feature".
# We extract from the matching header until the next top-level "## " header.
# ---------------------------------------------------------------------------
extract_section() {
    # Strip "## " prefix and any backslash escapes from each ## header,
    # then string-compare against "<SIDE> - <TYPE>". Print the matching section
    # until the next ## header.
    local doc="$1" target_side="$2" target_type="$3"
    awk -v side="$target_side" -v type="$target_type" '
        /^## / {
            content = substr($0, 4)
            gsub(/\\/, "", content)
            expected = side " - " type
            if (in_section) exit
            if (content == expected) {
                in_section = 1
                print "## " expected
                next
            }
        }
        in_section { print }
    ' "$doc"
}

SECTION="$(extract_section "$DOC_TMP" "$SIDE" "$TYPE")"
if [[ -z "$SECTION" ]]; then
    echo "✗ Could not extract section '$SIDE - $TYPE' from fetched doc." >&2
    echo "  The doc structure may have changed; inspect $DOC_TMP" >&2
    exit 4
fi

# ---------------------------------------------------------------------------
# Step 4: build the file
# ---------------------------------------------------------------------------
CHANGE_NAME="$(basename "$CHANGE_DIR")"
NOW="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

cat > "$TARGET" <<EOF
# Plan Review Checklist — \`${CHANGE_NAME}\`

> **Human gate.** Tick the items below honestly. Set **Overall Decision: OK** at the
> bottom only when you're satisfied with the plan. Until that happens, the plugin
> blocks \`/superpowers:executing-plans\`, \`/superpowers:executing-plans\`, and
> \`/superpowers:subagent-driven-development\` for this change.

## Meta

- **Change:** \`${CHANGE_NAME}\`
- **Variant:** ${SIDE} - ${TYPE}$(if [[ -z "$VARIANT_OVERRIDE" ]]; then echo " *(auto-detected; override via \`--variant\` if wrong)*"; else echo " *(manual override)*"; fi)
- **Generated:** ${NOW}
- **Source:** [Mor Developer Review Checklist](https://docs.google.com/document/d/184wY2N2WOUExmZrClvHCfcRCnSQsJYvav6gc6JwL6xc)
- **Files reviewed:**
  - [\`proposal.md\`](./proposal.md)
  - [\`design.md\`](./design.md) (if present)
  - [\`tasks.md\`](./tasks.md)

---

${SECTION}

---

## Overall Decision

> Replace the line below with **\`Overall Decision: OK\`** when the checklist is fully
> satisfied. Until then, leave it as **\`PENDING\`** — implementation skills will refuse to run.

\`\`\`
Overall Decision: PENDING
\`\`\`

### Notes / questions for the agent
EOF

echo "✓ Wrote $TARGET"
echo "  Variant: $SIDE - $TYPE"
echo "  Source size: $(wc -c < "$DOC_TMP") bytes"
