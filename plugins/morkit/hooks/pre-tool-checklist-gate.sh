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
# Two trigger paths:
#
# 1. Claude Code (Skill path): intercept tool_name=="Skill" for implementation
#    skills (executing-plans, subagent-driven-development, legacy openspec-apply-change).
#    CHANGE_DIR is resolved via "most recently modified" heuristic.
#
# 2. Codex (multi-tool path): Codex CLI has no `Skill` tool, so the unified
#    hooks.json matcher also covers file-mutation tools apply_patch|Edit|Write. These fire
#    on EVERY file edit, so the gate self-determines whether it's actually in
#    an executing-plans context by checking the MORKIT_CURRENT_CHANGE env var.
#    The Codex executing-plans skill is responsible for exporting this.
#    If unset → fail-open (not in executing-plans context).
#    If set → CHANGE_DIR is resolved as $PRIMARY/$MORKIT_CURRENT_CHANGE.
#
# Folder convention: ${MORKIT_ROOT:-morkit/output/spec}/
# Dual-read fallback: openspec/changes/ for v1 projects pre-migration.
#
# Fail-open scenarios:
#   - jq missing
#   - empty / malformed stdin
#   - tool_name not in matcher list
#   - Skill path: skill name not in matcher list
#   - Codex path: MORKIT_CURRENT_CHANGE unset, OR points to nonexistent change
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

# Dispatch on tool_name. Claude Code uses Skill; Codex uses apply_patch/Edit/Write.
# trigger_label is the human-facing string used in error messages.
trigger_label=""
case "$tool_name" in
    Skill)
        skill_name="$(printf '%s' "$input" | jq -r '.tool_input.skill // ""' 2>/dev/null || echo '')"
        case "$skill_name" in
            executing-plans|morkit:executing-plans) ;;
            subagent-driven-development|morkit:subagent-driven-development) ;;
            openspec-apply-change|spec:openspec-apply-change|spec:apply) ;;
            *) exit 0 ;;
        esac
        trigger_label="$skill_name"
        ;;
    apply_patch|Edit|Write)
        # Codex path — broad matcher, narrow on env var
        [[ -n "${MORKIT_CURRENT_CHANGE:-}" ]] || exit 0
        # Validate the env var is a simple change name (no path components, no archive).
        # Prevents path traversal (../sibling) and archive bypass (archive/old-thing)
        # that would let the gate appear "approved" via an unintended checklist file.
        if [[ "$MORKIT_CURRENT_CHANGE" == */* \
           || "$MORKIT_CURRENT_CHANGE" == "." \
           || "$MORKIT_CURRENT_CHANGE" == ".." \
           || "$MORKIT_CURRENT_CHANGE" == "archive" \
           || ! "$MORKIT_CURRENT_CHANGE" =~ ^[A-Za-z0-9._-]+$ ]]; then
            echo "⚠ morkit gate: MORKIT_CURRENT_CHANGE must be a single change name (alphanumeric, dot, dash, underscore), got '$MORKIT_CURRENT_CHANGE' — fail-open" >&2
            exit 0
        fi
        trigger_label="$tool_name (change=$MORKIT_CURRENT_CHANGE)"
        ;;
    *)
        # Unknown tool → fail-open
        exit 0
        ;;
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

# Resolve CHANGE_DIR.
#   Skill path: pick most recently modified non-archive change directory.
#   Codex path: use $MORKIT_CURRENT_CHANGE directly (fail-open if missing).
CHANGE_DIR=""
if [[ "$tool_name" == "Skill" ]]; then
    # NUL-delimited pipeline so paths with spaces/newlines are safe.
    # Cross-platform: BSD `stat -f` (macOS) and GNU `stat -c` (Linux) both tried.
    while IFS= read -r d; do
        [[ -n "$CHANGE_DIR" ]] || CHANGE_DIR="$d"
    done < <(
        find "$CHANGES_DIR" -mindepth 1 -maxdepth 1 -type d \
             ! -name 'archive' ! -name '.morkit' -print0 2>/dev/null \
        | xargs -0 -I{} sh -c 'stat -f "%m %N" "$1" 2>/dev/null || stat -c "%Y %n" "$1"' _ {} \
        | sort -rn \
        | sed 's/^[0-9]* //'
    )
else
    # Codex path
    candidate="$CHANGES_DIR/$MORKIT_CURRENT_CHANGE"
    if [[ -d "$candidate" ]]; then
        CHANGE_DIR="$candidate"
    else
        # Env var points to a name that doesn't exist → fail-open with WARN.
        # User error, but don't block unrelated file edits.
        echo "⚠ morkit gate: MORKIT_CURRENT_CHANGE=$MORKIT_CURRENT_CHANGE not found under $CHANGES_DIR — fail-open" >&2
        exit 0
    fi
fi

[[ -n "$CHANGE_DIR" && -d "$CHANGE_DIR" ]] || exit 0

CHECKLIST="$CHANGE_DIR/review-checklist.md"
CHANGE_NAME="$(basename "$CHANGE_DIR")"

if [[ "$USED_LEGACY" -eq 1 ]]; then
    echo "⚠ Using legacy openspec/changes/ folder. Run: bash \${MORKIT_PLUGIN_ROOT:-\${CLAUDE_PLUGIN_ROOT}}/scripts/migrate-from-openspec.sh" >&2
fi

if [[ ! -f "$CHECKLIST" ]]; then
    cat >&2 <<EOF
✗ Refusing $trigger_label for change "$CHANGE_NAME": review checklist missing.

  Expected: $CHECKLIST

  Run /morkit:review to generate the checklist (auto-detects BE/FE × Feature/BugFix/Refactor),
  fill it out honestly, set "Overall Decision: OK", then re-run.
EOF
    exit 1
fi

# Match "Overall Decision: OK" with optional surrounding whitespace.
if ! grep -qE '^[[:space:]]*Overall Decision:[[:space:]]+OK[[:space:]]*$' "$CHECKLIST"; then
    cat >&2 <<EOF
✗ Refusing $trigger_label for change "$CHANGE_NAME": review checklist not approved.

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
