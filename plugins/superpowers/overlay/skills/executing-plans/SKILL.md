---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Note:** Tell your human partner that Superpowers works much better with access to subagents. The quality of its work will be significantly higher if run on a platform with subagent support (such as Claude Code or Codex). If subagents are available, use superpowers:subagent-driven-development instead of this skill.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. If concerns: Raise them with your human partner before starting
4. If no concerns: Create TodoWrite and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent

## Integration

**Required workflow skills:**
- **superpowers:using-git-worktrees** - REQUIRED: Set up isolated workspace before starting
- **superpowers:writing-plans** - Creates the plan this skill executes
- **superpowers:finishing-a-development-branch** - Complete development after all tasks

---

## Library research with Context7 (Mor overlay)

When this skill needs accurate, version-specific library/framework documentation (Tech Stack design, API verification, debugging library behaviour, writing tests against a library API), prefer **Context7** over generic web search to avoid hallucinated APIs from stale training data.

**MCP path (preferred when Context7 MCP installed) — two tool calls:**

1. `mcp__context7__resolve-library-id` with `libraryName` (e.g. `"React"`) + `query` (the topic) → returns Context7 IDs like `/reactjs/react.dev`. Skip this step if the user already gave you an ID in `/org/project` form.
2. `mcp__context7__query-docs` with `libraryId` (from step 1) + `query` (be specific). Retry once with `researchMode: true` if the first answer is too shallow. Each tool ≤ 3 calls per question.

**CLI fallback (no setup needed; uses npx cache):**
```bash
# Step 1 — resolve the library to a Context7 ID
npx -y ctx7 library "<library-name>" "<topic>"   # e.g. "React" "hooks" → /reactjs/react.dev

# Step 2 — query docs for that ID
npx -y ctx7 docs "<library-id>" "<topic>"
```

When you encounter a library API you're not 100% certain about — query Context7 first, then proceed. Cheaper than discovering the bug at test time or rewriting after.

*This overlay is maintained by `mor-duongmh/claude-plugins`; not part of upstream `obra/superpowers`.*

---

## Pre-flight: developer review checklist must be approved (Mor overlay)

**BEFORE starting any work in this skill** — especially before reading the plan, dispatching subagents, or making any code change — verify the active spec change has an approved review checklist.

This skill mirrors the dual-read logic of the plugin's `pre-tool-checklist-gate.sh` hook: it looks for `${MOR_KIT_ROOT:-mor-kit/changes}/` first, then falls back to legacy `openspec/changes/` (with deprecation warning).

```bash
# Resolve folder convention (v2 primary, v1 legacy fallback)
PRIMARY="${MOR_KIT_ROOT:-mor-kit/changes}"
LEGACY="openspec/changes"

CHANGES_DIR=""
if [ -d "$PRIMARY" ]; then
    CHANGES_DIR="$PRIMARY"
elif [ -d "$LEGACY" ]; then
    CHANGES_DIR="$LEGACY"
    echo "⚠ Using legacy $LEGACY/. Run \${CLAUDE_PLUGIN_ROOT}/scripts/migrate-from-openspec.sh." >&2
fi

if [ -n "$CHANGES_DIR" ]; then
    # Detect most recent non-archive change (cross-platform stat)
    CHANGE_DIR="$(find "$CHANGES_DIR" -mindepth 1 -maxdepth 1 -type d \
                    ! -name 'archive' ! -name '.mor-kit' -print0 2>/dev/null \
                  | xargs -0 -I{} sh -c 'stat -f "%m %N" "$1" 2>/dev/null || stat -c "%Y %n" "$1"' _ {} \
                  | sort -rn | head -1 | awk '{print $2}')"
    CHECKLIST="$CHANGE_DIR/review-checklist.md"

    if [ -n "$CHANGE_DIR" ] && [ ! -f "$CHECKLIST" ]; then
        echo "✗ STOP: $CHECKLIST does not exist. Run /mor-kit:review."
        exit 1
    fi
    if [ -n "$CHANGE_DIR" ] && ! grep -qE '^[[:space:]]*Overall Decision:[[:space:]]+OK[[:space:]]*$' "$CHECKLIST"; then
        echo "✗ STOP: $CHECKLIST not approved. Set 'Overall Decision: OK' first."
        exit 1
    fi
fi
```

Skip this gate ONLY when there is **neither** `${MOR_KIT_ROOT:-mor-kit/changes}/` **nor** `openspec/changes/` folder in the project (this skill is being used outside the spec-driven workflow).

The plugin's PreToolUse hook also enforces this at the harness level. This skill-level check is defense-in-depth: if the hook is bypassed (e.g., disabled in user settings), this check still refuses to proceed.

*This pre-flight requirement is added by the Mor overlay, not part of upstream Superpowers.*
