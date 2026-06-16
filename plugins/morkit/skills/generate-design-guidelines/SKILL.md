---
name: generate-design-guidelines
description: "Generate or update design-guidelines.md (Design Principles + Patterns + ADRs in MADR format). Init renders from ProjectModel and emits per-ADR stubs at docs/adr/NNN-slug.md; update applies a Delta filtered for guidelines scope (DPR/PTN/ADR). Sync mode is intentionally not supported — guidelines are manual."
category: documentation
keywords: [design-guidelines, adr, madr, principles, patterns, architecture-decisions]
argument-hint: "init|update [options]"
metadata:
  author: morkit
  version: "1.0.0"
---

# Generate Design Guidelines Skill

Sub-skill that owns `docs/design-guidelines.md` and `docs/adr/*.md`.
Single-language output (JP / EN / VN). **No sync mode** — design guidelines
cannot be inferred from code.

## Environment (plugin context)

```bash
CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:?must be set by Claude Code}"
VENV="${HOME}/.claude/plugins/data/docs-hero/.venv"
PY="${VENV}/bin/python3"
GUI_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-design-guidelines/scripts"
ORCH_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/docs-hero-orchestrator/scripts"
PROJECT_DOCS_DIR="${PWD}/docs"
PROJECT_META="${PWD}/.docs-hero-meta.json"
```

## Modes

| Mode | Purpose |
|---|---|
| `init` | Render `docs/design-guidelines.md` from a ProjectModel JSON; also write per-ADR stubs under `docs/adr/` |
| `update` | Apply Delta filtered for guidelines scope (DPR / PTN / ADR) |
| `sync` | **Not supported** — guidelines are manual |

## Init Workflow

```bash
"$PY" "$GUI_SCRIPTS/render_design_guidelines.py" \
  --project-model "$PROJECT_MODEL" \
  --language EN \
  --output "$PROJECT_DOCS_DIR/design-guidelines.md" \
  --adr-dir "$PROJECT_DOCS_DIR/adr"
```

Section IDs (stable for diff engine):

```
DPR-{id}       # Per design principle (inline in §1)
PTN-{id}       # Per pattern guideline (inline in §2)
ADR-{id}       # Per ADR — H3 anchor in §3 + standalone file at docs/adr/{id}-{slug}.md
```

## File Ownership

This skill owns:
- `docs/design-guidelines.md`
- `docs/adr/*.md` (one stub per ADR)

It does **not** modify:
- `docs/srs.md`, `docs/api-docs.md`, `docs/database-design.md`
- `docs/system-architecture.md`, `docs/code-standards.md`,
  `docs/codebase-summary.md`

## Why no sync

Design principles, patterns, and architecture decisions cannot be
reliably inferred from source code — they reflect intent that lives in
discussion threads / ADR documents authored by humans. Use `init` /
`update` only.

## References

- `templates/design-guidelines-template.md`
- MADR: <https://adr.github.io/madr/>
