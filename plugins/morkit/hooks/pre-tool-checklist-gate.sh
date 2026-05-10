#!/usr/bin/env bash
# pre-tool-checklist-gate.sh — block plan-execution implementation skills when the
# active morkit change's review-checklist.md is missing or not marked
# "Overall Decision: OK".
#
# Claude Code passes a JSON payload describing the pending tool call on stdin:
#   { "tool_name": "Skill", "tool_input": { "skill": "morkit:executing-plans", ... } }
#
# Hook contract:
#   exit 0       → allow tool call
#   exit non-0   → block; stderr is shown to the agent (and to the user)
#
# We intercept ONLY the Skill tool, only for these implementation skills:
#   - executing-plans / morkit:executing-plans
#   - subagent-driven-development / morkit:subagent-driven-development
#
# Legacy v1 OpenSpec skill names (openspec-apply-change, spec:apply) are also
# matched for projects that haven't migrated yet.
#
# Folder convention: ${MORKIT_ROOT:-morkit/output/spec}/
# Dual-read fallback: openspec/changes/ for v1 projects pre-migration.
#
# Fail-open scenarios:
#   - jq missing
#   - empty / malformed stdin
#   - non-Skill tool
#   - skill not in matcher list
#   - no morkit/output/spec/ AND no openspec/changes/

set -euo pipefail

CWD="$(pwd)"

# jq required; fail-open if absent
if ! command -v jq >/dev/null 2>&1; then
    exit 0
fi

input="$(cat || true)"
[[ -n "$input" ]] || exit 0

tool_name="$(printf '%s' "$input" | jq -r '.tool_name // ""' 2>/dev/null || echo '')"
[[ "$tool_name" == "Skill" ]] || exit 0

skill_name="$(printf '%s' "$input" | jq -r '.tool_input.skill // ""' 2>/dev/null || echo '')"
case "$skill_name" in
    executing-plans|morkit:executing-plans) ;;
    subagent-driven-development|morkit:subagent-driven-development) ;;
    openspec-apply-change|spec:openspec-apply-change|spec:apply) ;;
    *) exit 0 ;;
esac

# Resolve folder convention. Honor MORKIT_ROOT override.
PRIMARY="${MORKIT_ROOT:-morkit/output/spec}"
LEGACY="openspec/changes"

CHANGES_DIR=""
USED_LEGACY=0
if [[ -d "$CWD/$PRIMARY" ]]; then
    CHANGES_DIR="$CWD/$PRIMARY"
elif [[ -d "$CWD/$LEGACY" ]]; then
    CHANGES_DIR="$CWD/$LEGACY"
    USED_LEGACY=1
else
    # Project doesn't use morkit plugin → fail-open
    exit 0
fi

# Pick the most recently modified non-archive change directory.
# NUL-delimited pipeline so paths with spaces/newlines are safe.
# Cross-platform: BSD `stat -f` (macOS) and GNU `stat -c` (Linux) both tried.
CHANGE_DIR=""
while IFS= read -r d; do
    [[ -n "$CHANGE_DIR" ]] || CHANGE_DIR="$d"
done < <(
    find "$CHANGES_DIR" -mindepth 1 -maxdepth 1 -type d \
         ! -name 'archive' ! -name '.morkit' -print0 2>/dev/null \
    | xargs -0 -I{} sh -c 'stat -f "%m %N" "$1" 2>/dev/null || stat -c "%Y %n" "$1"' _ {} \
    | sort -rn \
    | sed 's/^[0-9]* //'
)

[[ -n "$CHANGE_DIR" && -d "$CHANGE_DIR" ]] || exit 0

CHECKLIST="$CHANGE_DIR/review-checklist.md"
CHANGE_NAME="$(basename "$CHANGE_DIR")"

if [[ "$USED_LEGACY" -eq 1 ]]; then
    echo "⚠ Using legacy openspec/changes/ folder. Run: bash \${CLAUDE_PLUGIN_ROOT}/scripts/migrate-from-openspec.sh" >&2
fi

if [[ ! -f "$CHECKLIST" ]]; then
    cat >&2 <<EOF
✗ Refusing $skill_name for change "$CHANGE_NAME": review checklist missing.

  Expected: $CHECKLIST

  Run /morkit:review to generate the checklist (auto-detects BE/FE × Feature/BugFix/Refactor),
  fill it out honestly, set "Overall Decision: OK", then re-run.
EOF
    exit 1
fi

# Match "Overall Decision: OK" with optional surrounding whitespace.
if ! grep -qE '^[[:space:]]*Overall Decision:[[:space:]]+OK[[:space:]]*$' "$CHECKLIST"; then
    cat >&2 <<EOF
✗ Refusing $skill_name for change "$CHANGE_NAME": review checklist not approved.

  File: $CHECKLIST

  Open the file, tick the checklist items, fill the Review Summary, then change
  the bottom line from
      Overall Decision: PENDING
  to
      Overall Decision: OK
  and re-run the command.
EOF
    exit 1
fi

exit 0
