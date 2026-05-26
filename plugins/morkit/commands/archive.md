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

**Tip:** run `/morkit:docs update` BEFORE archiving — it bridges this change's `proposal`/`design`/`tasks`/`spec` into `docs/` (decisions→ADR, requirements→FEATURE-LIST, scenarios→TEST-MATRIX). Once archived, the change is out of scope for the docs bridge and its WHAT/WHY won't reach `docs/`.
