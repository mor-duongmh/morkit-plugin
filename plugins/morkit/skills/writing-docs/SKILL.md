---
name: writing-docs
description: Generate an AI-agent-optimized project documentation set (taxonomy + anchors) in docs/. Use to init, update, or summarize docs that AI agents can navigate with minimal context. LLM-driven, no Python.
license: MIT
---

# Writing Docs

Generate and maintain a project documentation set in `docs/` optimized for AI agents: a structured taxonomy, anchor files (MAP), and small decomposed files linked via cross-references — so an agent loads only the minimal context needed per task.

**IMPORTANT:** This skill writes documentation ONLY. Do NOT implement or modify application code. No Python — fully LLM-driven via morkit-native dispatch (Task tool / `dispatching-parallel-agents`).

## Entry Points

This skill implements three modes, reached via two commands:
- **`/morkit:init`** → first-time bootstrap (always passes `init`).
- **`/morkit:docs`** → maintenance of existing docs (`update` / `summarize`).

## Default (No Arguments)

If invoked without a clear mode, use the **AskUserQuestion tool** to present:

| Operation | Description |
|-----------|-------------|
| `update` | Refresh existing docs against code changes |
| `summarize` | Quick refresh of SOURCE-MAP + DOCUMENT-MAP |

Header "Docs Operation", question "What would you like to do?". Do NOT auto-run anything. If there is no `docs/` taxonomy yet (first-time setup), tell the user to run **`/morkit:init`**.

## Routing

Parse the first word of the arguments:
- `init` → load `references/init-workflow.md` (entered via `/morkit:init`)
- `update` → load `references/update-workflow.md`
- `summarize` → load `references/summarize-workflow.md`
- empty / unclear → AskUserQuestion (above)

Flags: `[path]` target dir (default: cwd) · `--scope project|module` · `--yes` (skip the post-scout gate) · `--agents` (also write `AGENTS.md`).

`init` and `update` finish by generating/refreshing the root agent-instruction file your harness auto-loads (`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex; + the other when detected) per `references/agent-instructions.md`.

## Shared Context

Output lives in `docs/` at the **target project root** (NOT `morkit/output/` — these are project docs every agent and human looks for). **One exception:** the root agent-instruction files `CLAUDE.md` / `AGENTS.md` are written at the project (and per-module) root as a thin pointer into `docs/` — see `references/agent-instructions.md`.

Taxonomy (core-6 always; create the rest only when scout finds the matching component):
```
docs/
├── 00-overview/      DOCUMENT-MAP, SCOPE, SOURCE-MAP, DEPENDENCY-MAP, GLOSSARY, STACK
├── 10-requirements/  FEATURE-LIST, USER-FLOWS (+ flows/)
├── 20-design/        DESIGN-MAP · 00-core/(ARCHITECTURE, INVARIANTS) ·
│                     10-features/*-SYS-SPEC · 20-data/ · 30-api/ · 40-ui/ · ADR/ · 90-reference/
├── 30-test/          TEST-STRATEGY, TEST-RUNBOOK, TEST-MATRIX
├── 40-ai-coding/     AI-CODING-GUIDE, CODE-SEARCH-GUIDE, COMMON-CHANGE-PLAYBOOKS,
│                     KNOWN-PITFALLS, RISK-REGISTER, CODE-STANDARDS
└── 90-operations/    LOCAL-RUNBOOK, TROUBLESHOOTING
```
Extension folders (only on explicit signal/request): `00-review`, `50-migration`, `60-security`, `70-performance`, `80-release`.

Conventions (full detail: `references/taxonomy.md` + `references/anchor-conventions.md`; skeletons: `references/doc-templates/`):
- **Anchors:** MAP files + cross-links (primary) · minimal front-matter (`updated` / `status` / `source_files`) · IDs (`FR-###`/`NFR-###` in FEATURE-LIST, `INV-###` in INVARIANTS → TEST-MATRIX.Ref, `BR-###` local per SYS-SPEC).
- Each file targets ~100 LOC (hard cap 800 → split). Flows use `text` + arrows (no Mermaid by default).
- Every doc opens with a boundary line: `> This doc holds X. For Y see [other-doc].` (DRY).

## Constraints
- LLM-driven only — no Python, no external CLI dependency. Keep morkit self-contained.
- Generation order is ALWAYS **Scout → Content → MAP → agent-instructions** (never write a MAP before its content exists; agent-instructions last because the pointer links to the MAP/guide it just produced).
- Create a folder/file only when the project actually has the matching component (no empty folders).
- All output stays in `docs/` EXCEPT `CLAUDE.md` / `AGENTS.md` at the root — those are written only through the marker-block + approve gate in `references/agent-instructions.md` (never touch content outside the marker block).
