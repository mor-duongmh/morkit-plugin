#!/usr/bin/env bash
# validate-tasks.sh — validate a tasks.md against the morkit-driven schema.
# Replaces `npx openspec schema validate`.
#
# Rules (R1-R6):
#   R1: tasks.md contains line `> **For agentic workers:** REQUIRED SUB-SKILL`
#   R2: at least one heading matching `^## Task \d+:`
#   R3: every Task block contains line `**Files:**`
#   R4: every Task block contains ≥1 `- [ ]` or `- [x]` checkbox
#   R5: total checkbox count across the file ≥ 3
#   R6: companion .meta.json (if present in same dir) has schema_version == validator's
#
# Usage:
#   validate-tasks.sh <tasks.md>
#   validate-tasks.sh --rule <Rn> <tasks.md>
#   validate-tasks.sh --explain
#
# Exit:
#   0 = valid
#   1 = invalid (rule violation)
#   2 = bad usage / file missing

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
. "$SCRIPT_DIR/lib/common.sh"

EXPLAIN=0
ONLY_RULE=""
TARGET=""

print_usage() {
    cat <<'EOF'
Usage: validate-tasks.sh [--rule R1|R2|R3|R4|R5|R6] [--explain] <tasks.md>

Validates tasks.md against the morkit-driven schema. Rules R1-R6 are checked
in order. First failure exits non-zero.

Options:
  --rule <Rn>   Check only one rule (others skipped)
  --explain     Print rule descriptions and exit
  --help        Show this help
EOF
}

print_explanation() {
    cat <<'EOF'
morkit-driven tasks.md schema rules
========================================

R1 Header
   Line containing exactly:
   > **For agentic workers:** REQUIRED SUB-SKILL

R2 Tasks present
   At least one heading matching `^## Task <N>:`

R3 Files block per task
   Each `## Task` heading is followed (before next `## ` or EOF) by a line
   `**Files:**`

R4 Checkbox per task
   Each `## Task` block contains at least one `- [ ]` or `- [x]` checkbox.

R5 Minimum checkbox count
   Total checkbox count across whole file is at least 3.

R6 Schema version match
   If a sibling `.meta.json` exists, its `schema_version` field matches the
   validator's MORKIT_SCHEMA_VERSION.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)   print_usage; exit 0 ;;
        --explain)   EXPLAIN=1; shift ;;
        --rule)      ONLY_RULE="$2"; shift 2 ;;
        *)
            if [[ -z "$TARGET" ]]; then TARGET="$1"; shift
            else echo "Unexpected arg: $1" >&2; exit 2; fi
            ;;
    esac
done

if [[ "$EXPLAIN" -eq 1 ]]; then
    print_explanation
    exit 0
fi

if [[ -z "$TARGET" ]]; then
    print_usage >&2
    exit 2
fi

if [[ ! -f "$TARGET" ]]; then
    echo "✗ File not found: $TARGET" >&2
    exit 2
fi

# Normalize: read file stripping CR (CRLF tolerance)
NORMALIZED="$(tr -d '\r' < "$TARGET")"

should_check() {
    local rule="$1"
    [[ -z "$ONLY_RULE" || "$ONLY_RULE" == "$rule" ]]
}

# ---------------------------------------------------------------------------
# Rule implementations
# ---------------------------------------------------------------------------
check_R1() {
    if ! grep -qE '^>[[:space:]]*\*\*For agentic workers:\*\*[[:space:]]*REQUIRED SUB-SKILL' <<< "$NORMALIZED"; then
        echo "✗ R1 — missing Superpowers header line:" >&2
        echo "  Expected: > **For agentic workers:** REQUIRED SUB-SKILL ..." >&2
        return 1
    fi
}

check_R2() {
    if ! grep -qE '^## Task [0-9]+:' <<< "$NORMALIZED"; then
        echo "✗ R2 — no '## Task <N>:' heading found" >&2
        return 1
    fi
}

# Iterate task blocks; each block is from `^## Task N:` to next `^## ` or EOF.
# For R3, R4: per-block check.
iter_task_blocks() {
    # Print blocks separated by NUL
    awk '
        /^## Task [0-9]+:/ {
            if (in_block) printf "%s%c", block, 0
            in_block = 1
            block = ""
        }
        /^## / && !/^## Task [0-9]+:/ {
            if (in_block) { printf "%s%c", block, 0; in_block = 0; block = "" }
        }
        in_block { block = block $0 "\n" }
        END { if (in_block) printf "%s%c", block, 0 }
    ' <<< "$NORMALIZED"
}

check_R3() {
    local missing=""
    local block
    local idx=0
    while IFS= read -r -d '' block; do
        idx=$((idx + 1))
        if ! grep -qE '^\*\*Files:\*\*' <<< "$block"; then
            local title
            title=$(grep -m1 -E '^## Task [0-9]+:' <<< "$block" || echo "Task $idx")
            missing+="  - $title (block $idx)"$'\n'
        fi
    done < <(iter_task_blocks)
    if [[ -n "$missing" ]]; then
        {
            echo "✗ R3 — task block(s) missing **Files:** section:"
            printf '%s' "$missing"
        } >&2
        return 1
    fi
}

check_R4() {
    local missing=""
    local block
    local idx=0
    while IFS= read -r -d '' block; do
        idx=$((idx + 1))
        if ! grep -qE '^[[:space:]]*-[[:space:]]+\[[ xX]\]' <<< "$block"; then
            local title
            title=$(grep -m1 -E '^## Task [0-9]+:' <<< "$block" || echo "Task $idx")
            missing+="  - $title (block $idx)"$'\n'
        fi
    done < <(iter_task_blocks)
    if [[ -n "$missing" ]]; then
        {
            echo "✗ R4 — task block(s) missing checkbox:"
            printf '%s' "$missing"
        } >&2
        return 1
    fi
}

check_R5() {
    local count
    count=$(grep -cE '^[[:space:]]*-[[:space:]]+\[[ xX]\]' <<< "$NORMALIZED" || true)
    if [[ "$count" -lt 3 ]]; then
        echo "✗ R5 — only $count checkbox(es) found (minimum 3)" >&2
        return 1
    fi
}

check_R6() {
    local dir
    dir="$(cd "$(dirname "$TARGET")" && pwd)"
    local meta="$dir/.meta.json"
    [[ -f "$meta" ]] || return 0   # absent = OK
    ensure_jq || return 1
    local sv
    sv=$(jq -r '.schema_version // empty' "$meta" 2>/dev/null || echo "")
    if [[ -z "$sv" ]]; then
        echo "✗ R6 — .meta.json has no schema_version field" >&2
        return 1
    fi
    if [[ "$sv" != "$MORKIT_SCHEMA_VERSION" ]]; then
        echo "✗ R6 — .meta.json schema_version=$sv does not match validator=$MORKIT_SCHEMA_VERSION" >&2
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Run rules in order, short-circuit on first failure
# ---------------------------------------------------------------------------
RULES=(R1 R2 R3 R4 R5 R6)
FAILED=0

for r in "${RULES[@]}"; do
    if ! should_check "$r"; then
        continue
    fi
    if ! "check_$r"; then
        FAILED=1
        # Continue to surface all violations rather than stop at first
    fi
done

if [[ "$FAILED" -ne 0 ]]; then
    exit 1
fi

echo "✓ Validation passed: $TARGET"
