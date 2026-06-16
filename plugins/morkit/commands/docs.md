---
name: "morkit:docs"
description: Maintain an existing AI-optimized project documentation set in docs/ (taxonomy + anchors). Modes: update | summarize. For first-time setup use /morkit:init. LLM-driven, no Python.
category: Documentation
tags: [docs, documentation, taxonomy, ai-agent]
---

Invoke the `writing-docs` skill using the Skill tool. Pass through any arguments the user provided.

**First-time setup → use `/morkit:init`** (it scouts the codebase and creates the taxonomy). This command maintains a `docs/` set that already exists:
- `update` — refresh existing docs against code changes
- `summarize` — quick refresh of SOURCE-MAP + DOCUMENT-MAP

Output goes to `docs/` at the target project root. Anchors (MAP files + cross-links + minimal front-matter) let agents load minimal context per task. `update` also refreshes the thin pointer block in the root `CLAUDE.md` (and `AGENTS.md` when Codex is detected) through an approve gate. No Python — fully LLM-driven.
