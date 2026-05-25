---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Note:** Tell your human partner that Superpowers works much better with access to subagents. The quality of its work will be significantly higher if run on a platform with subagent support (such as Claude Code or Codex). If subagents are available, use morkit:subagent-driven-development instead of this skill.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. If concerns: Raise them with your human partner before starting
4. If no concerns: Create TodoWrite and proceed

### Step 1.5: Pre-Implementation Validation

**Before writing any code, read the project's reference docs (when present in `./docs/`)** so your implementation matches the codebase's stated conventions, structure, and architecture:

- `docs/codebase-summary.md` — repo layout, tech stack, entry points (where things live)
- `docs/code-standards.md` — naming, formatting, lint, commit conventions (how to write things)
- `docs/system-architecture.md` — components, layers, interactions (how things fit together)

If a doc is missing, skip it silently — do NOT block on missing docs and do NOT generate them as a side effect. If a doc exists but conflicts with the plan, surface the conflict to your human partner before proceeding.

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use morkit:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice
- **Recommended before push:** run `/morkit:deep-review --diff` on the
  local diff to catch risk / security / pattern issues before opening
  the PR. The `finishing-a-development-branch` skill calls this out
  under Option 2 (Push and Create PR).

After PR is merged, close out the morkit change:
```bash
/morkit:archive <change-name>
```
This moves `morkit/output/spec/<name>/` to `morkit/output/spec/archive/<name>/`
so future `/morkit:propose` runs don't see it as active.

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
- **morkit:using-git-worktrees** - REQUIRED: Set up isolated workspace before starting
- **morkit:writing-plans** - Creates the plan this skill executes
- **morkit:finishing-a-development-branch** - Complete development after all tasks

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


---

## Pre-flight: developer review checklist must be approved (Mor overlay)

**BEFORE starting any work in this skill** — especially before reading the plan, dispatching subagents, or making any code change — verify the morkit change has an approved review checklist.

```bash
# Resolve the changes folder: canonical morkit dir, with legacy openspec fallback.
SEARCH_ROOT="${MORKIT_ROOT:-morkit/output/spec}"
[ -d "$SEARCH_ROOT" ] || SEARCH_ROOT="openspec/changes"

# Detect most recent non-archive change. No change found → nothing to gate.
CHANGE_DIR="$(find "$SEARCH_ROOT" -mindepth 1 -maxdepth 1 -type d ! -name 'archive' \
                -exec stat -f "%m %N" {} \; 2>/dev/null \
              | sort -rn | head -1 | awk '{print $2}')"
[ -n "$CHANGE_DIR" ] || exit 0
CHECKLIST="$CHANGE_DIR/review-checklist.md"

if [ ! -f "$CHECKLIST" ]; then
    echo "✗ STOP: $CHECKLIST does not exist. Run /morkit:review."
    exit 1
fi
if ! grep -qE '^[[:space:]]*Overall Decision:[[:space:]]*OK[[:space:]]*$' "$CHECKLIST"; then
    echo "✗ STOP: $CHECKLIST not approved. Set 'Overall Decision: OK' first."
    exit 1
fi
```

Skip this gate ONLY when neither `morkit/output/spec/` nor `openspec/changes/` exists (this skill is being used outside the spec-driven workflow).

The plugin's PreToolUse hook also enforces this at the harness level. This skill-level check is defense-in-depth: if the hook is bypassed (e.g., disabled in user settings), this check still refuses to proceed.

*This pre-flight requirement is added by the Mor overlay, not part of upstream Superpowers.*
