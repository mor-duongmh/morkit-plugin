---
name: "morkit:init"
description: Bootstrap the AI-optimized docs/ set for a project (brownfield or greenfield) — scout the codebase and create the taxonomy (00-overview … 90-operations) + anchors + root CLAUDE.md/AGENTS.md pointer. First-time setup. LLM-driven, no Python.
category: Documentation
tags: [docs, init, bootstrap, taxonomy, ai-agent]
---

Invoke the `writing-docs` skill using the Skill tool with the **`init`** operation. Pass through any arguments the user provided (treat the whole invocation as `init` mode — prepend `init` to the args before handing off).

This is the first-time documentation bootstrap — run it once per project (brownfield or greenfield). It generates a `docs/` set optimized for AI agents:
- Scout the codebase (read-only) and create the taxonomy (`00-overview` … `90-operations`)
- Generate anchors (MAP files + cross-links + minimal front-matter) so agents load minimal context per task
- Write a thin pointer block into the root `CLAUDE.md` (and `AGENTS.md` when Codex is detected) through an approve gate

Flags pass through to the skill: `[path]` target dir (default: cwd) · `--scope project|module` · `--yes` (skip the post-scout gate) · `--agents` (also write `AGENTS.md`).

Output goes to `docs/` at the target project root. No Python — fully LLM-driven.

After the docs exist, maintain them with `/morkit:docs update` (refresh against code changes) or `/morkit:docs summarize` (quick SOURCE-MAP + DOCUMENT-MAP refresh).
