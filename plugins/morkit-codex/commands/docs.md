---
name: "morkit:docs"
description: Generate an AI-optimized project documentation set in docs/ (taxonomy + anchors). Modes: init | update | summarize. LLM-driven, no Python.
category: Documentation
tags: [docs, documentation, taxonomy, ai-agent]
---

Invoke the `writing-docs` skill. Pass through any arguments the user provided.

The skill generates/maintains a `docs/` documentation set optimized for AI agents:
- `init` — scout the codebase and create the taxonomy (`00-overview` … `90-operations`)
- `update` — refresh existing docs against code changes
- `summarize` — quick refresh of SOURCE-MAP + DOCUMENT-MAP

Output goes to `docs/` at the target project root. Anchors (MAP files + cross-links + minimal front-matter) let agents load minimal context per task. `init`/`update` also write a thin pointer block into the root `CLAUDE.md` (and `AGENTS.md` when Codex is detected) through an approve gate. No Python — fully LLM-driven.
