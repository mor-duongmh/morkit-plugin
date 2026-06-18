---
name: "morkit:archive"
description: Archive a completed spec change after implementation is complete. Moves the change folder from active to archive subfolder and updates .meta.json.archived. Self-contained — no OpenSpec CLI required.
category: Workflow
tags: [spec, archive, finalize]
---

Invoke the `archive` skill using the Skill tool. Pass through any arguments (change name) the user provided.

The skill will:
- List active changes via `${CLAUDE_PLUGIN_ROOT}/scripts/list-changes.sh`
- Prompt the user to select a change (or use argument)
- Sanity-check task completion (warn if pending `- [ ]` remain)
- `mv ${MORKIT_ROOT:-morkit/output/spec}/<name> ${MORKIT_ROOT:-morkit/output/spec}/archive/<name>`
- Update `.meta.json.archived = true` and add `archived_at` timestamp

Run this once a change is fully implemented and merged.

**Docs bridge gate:** if docs-hero is set up (venv + `.docs-hero-meta.json`), `/morkit:archive` now **prompts** to bridge this change into `docs/` (via `/morkit:docs-update`) before moving — because once archived, the change is out of bridge scope and its WHAT/WHY won't reach `docs/`. Spec-only projects (no docs-hero) skip the prompt and archive directly. You can also bridge manually anytime with `/morkit:docs-update` (or `/morkit:sync`).
