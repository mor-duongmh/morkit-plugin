---
name: "mor-kit:review"
description: Generate or refresh the developer review checklist (human gate) for an OpenSpec change. Blocks /superpowers:executing-plans and Superpowers implementation skills until "Overall Decision: OK" is set.
category: Workflow
tags: [spec, review, gate, checklist, human]
---

Invoke the `review` skill using the Skill tool. Pass through any arguments the user provided.

Args:
- `[change-name]` (optional) — pick a specific change folder; otherwise the most recent active change is used
- `--refresh` (optional) — force re-fetch the canonical Google Doc (bypasses 24h cache)
- `--variant <id>` (optional) — override auto-detected variant: `BE-Feature`, `BE-BugFix`, `BE-Refactor`, `FE-Feature`, `FE-BugFix`, `FE-Refactor`

The skill will:
- Locate the target change directory under `${MOR_KIT_ROOT:-mor-kit/changes}/`
- Generate `review-checklist.md` from the Mor Developer Review Checklist Google Doc (with cache fallback)
- Auto-detect the variant unless overridden
- Show the path to the generated file and remind the user to fill it out and set `Overall Decision: OK`

The plugin's PreToolUse hook will refuse `/superpowers:executing-plans`, `/superpowers:executing-plans`, and `/superpowers:subagent-driven-development` for the change until the file shows `Overall Decision: OK`.

**Usage:**
```
/mor-kit:review                    # active change, auto-detect variant
/mor-kit:review my-change          # specific change
/mor-kit:review --refresh          # force re-fetch
/mor-kit:review --variant FE-BugFix
```
