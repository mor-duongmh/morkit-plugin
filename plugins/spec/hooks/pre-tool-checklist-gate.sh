#!/usr/bin/env bash
# pre-tool-checklist-gate.sh — block implementation skills when the OpenSpec
# change's review-checklist.md is missing or not marked "Overall Decision: OK".
#
# Claude Code passes a JSON payload describing the pending tool call on stdin:
#   { "tool_name": "Skill", "tool_input": { "skill": "openspec-apply-change", ... } }
#
# Hook contract:
#   exit 0       → allow tool call
#   exit non-0   → block; stderr is shown to the agent (and to the user)
#
# We intercept ONLY the Skill tool, only for these implementation skills:
#   - openspec-apply-change                          (Mor)
#   - executing-plans / superpowers:executing-plans  (Superpowers)
#   - subagent-driven-development / superpowers:subagent-driven-development
#
# For everything else we exit 0 immediately. We also exit 0 when the project
# has no OpenSpec changes in flight — this hook is OpenSpec-aware, not a global
# block.

set -euo pipefail

CWD="$(pwd)"

# Read stdin (JSON payload). If empty / no jq, fail-open so we never break
# unrelated tools.
if ! command -v jq >/dev/null 2>&1; then
    exit 0
fi
input="$(cat || true)"
[[ -n "$input" ]] || exit 0

tool_name="$(printf '%s' "$input" | jq -r '.tool_name // ""' 2>/dev/null || echo '')"
[[ "$tool_name" == "Skill" ]] || exit 0

skill_name="$(printf '%s' "$input" | jq -r '.tool_input.skill // ""' 2>/dev/null || echo '')"
case "$skill_name" in
    openspec-apply-change|spec:openspec-apply-change|spec:apply) ;;
    executing-plans|superpowers:executing-plans) ;;
    subagent-driven-development|superpowers:subagent-driven-development) ;;
    *) exit 0 ;;
esac

# Only gate when the project actually uses OpenSpec.
[[ -d "$CWD/openspec/changes" ]] || exit 0

# Pick the most recently modified non-archive change directory.
# The skill itself decides which change to apply, but we approximate "active
# change" with most-recent-mtime; this is fine for the typical 1-change-in-flight
# workflow. If there are multiple, only the latest is checked.
CHANGE_DIR=""
while IFS= read -r -d '' d; do
    [[ -n "$CHANGE_DIR" ]] || CHANGE_DIR="$d"
done < <(find "$CWD/openspec/changes" -mindepth 1 -maxdepth 1 -type d \
              ! -name 'archive' -print0 \
              2>/dev/null \
         | xargs -0 -I{} stat -f "%m %N" "{}" 2>/dev/null \
         | sort -rn \
         | awk '{print $2}' \
         | tr '\n' '\0')

# Fallback for environments without macOS stat; try Linux flavour.
if [[ -z "$CHANGE_DIR" ]]; then
    while IFS= read -r d; do
        [[ -n "$CHANGE_DIR" ]] || CHANGE_DIR="$d"
    done < <(find "$CWD/openspec/changes" -mindepth 1 -maxdepth 1 -type d \
                  ! -name 'archive' -printf "%T@ %p\n" 2>/dev/null \
             | sort -rn | awk '{print $2}')
fi

[[ -n "$CHANGE_DIR" && -d "$CHANGE_DIR" ]] || exit 0

CHECKLIST="$CHANGE_DIR/review-checklist.md"
CHANGE_NAME="$(basename "$CHANGE_DIR")"

if [[ ! -f "$CHECKLIST" ]]; then
    cat >&2 <<EOF
✗ Refusing $skill_name for change "$CHANGE_NAME": review checklist missing.

  Expected: $CHECKLIST

  Run /spec:review to generate the checklist (auto-detects BE/FE × Feature/BugFix/Refactor),
  fill it out honestly, set "Overall Decision: OK", then re-run.
EOF
    exit 1
fi

# We require the EXACT line "Overall Decision: OK" — the template ships with
# "Overall Decision: PENDING" and the human flips it once they're satisfied.
# A line containing the OK marker, ignoring leading/trailing whitespace, counts.
if ! grep -qE '^[[:space:]]*Overall Decision:[[:space:]]*OK[[:space:]]*$' "$CHECKLIST"; then
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
