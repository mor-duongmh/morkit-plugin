# mor-kit — Mor's spec-driven workflow toolkit

> **Self-contained.** Install once via marketplace — every command works in any project. No per-project setup, no OpenSpec init, no schema copy.

This plugin focuses on **scaffolding** + **review-checklist gating**. Brainstorming, plan execution, and TDD are handled by the `superpowers` plugin (no duplication).

## Install

```
/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install mor-kit@mor-duongmh
/plugin install superpowers@mor-duongmh
```

## Workflow

```
   /superpowers:brainstorm   (think before committing)
          │
          ▼
   /mor-kit:propose [desc]
   ├─ Scaffolds mor-kit/changes/<name>/
   ├─ Generates proposal.md, design.md, tasks.md (TDD), .meta.json
   └─ Auto-runs /mor-kit:review → review-checklist.md (PENDING)
          │
          ▼
   🚦 HUMAN GATE
   Open review-checklist.md, tick items, set "Overall Decision: OK"
          │
          ▼ (PreToolUse hook + skill pre-flight enforce)
          ▼
   /superpowers:execute-plan  ─or─  /superpowers:subagent-driven-development
          ▼
   /mor-kit:archive   (after merge)
```

## Folder convention

Plugin scaffolds under `mor-kit/changes/<name>/`:
- `proposal.md` — what & why
- `design.md` — how, including Tech Stack
- `tasks.md` — Superpowers header + TDD steps with `**Files:**` and `- [ ]` checkboxes
- `.meta.json` — `{ name, created_at, schema_version, archived }`
- `review-checklist.md` — generated from canonical Google Doc (the human gate)

Marker `mor-kit/changes/.mor-kit` identifies plugin-owned content. **Override path:** `MOR_KIT_ROOT=path/to/changes` in your shell.

## Slash commands

| Command | Purpose |
|---|---|
| `/mor-kit:propose [desc]` | Scaffold a new change with all artifacts |
| `/mor-kit:review [name]` | (Re)generate review-checklist from Google Doc |
| `/mor-kit:archive [name]` | Move completed change to archive subfolder |

For brainstorming and execution, use the `superpowers` plugin:
- `/superpowers:brainstorm`
- `/superpowers:execute-plan`
- `/superpowers:subagent-driven-development`

## About `schemas/superpowers-driven/`

Reference documentation — the schema contract retained for context. Plugin runtime does NOT read these files; `validate-tasks.sh` implements rules R1-R6 directly in bash.

## Schema rules (validated automatically)

`tasks.md` must satisfy:
- **R1:** Header `> **For agentic workers:** REQUIRED SUB-SKILL ...`
- **R2:** ≥1 `## Task <N>:` heading
- **R3:** Every task block contains `**Files:**`
- **R4:** Every task block contains ≥1 `- [ ]` or `- [x]` checkbox
- **R5:** Total checkbox count ≥ 3
- **R6:** Sibling `.meta.json.schema_version` matches validator's

Run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate-tasks.sh --explain` for full descriptions.

## Migrating from spec@mor-duongmh

Previous plugin name was `spec`. v1 used `openspec/changes/`. v2 used `spec/changes/`. `mor-kit@1.0.0` uses `mor-kit/changes/`.

Run the migration helper at the project root:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-from-openspec.sh --dry-run    # preview
bash ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-from-openspec.sh              # execute
```

Behavior:
- `openspec/changes/<name>/` → `mor-kit/changes/<name>/`
- Archive subfolder preserved
- `.mor-kit` marker added
- Empty `openspec/` directory removed (`--keep-openspec` to preserve)
- Hook has dual-read fallback for legacy `openspec/changes/`

## Commands removed in v1.0.0 (vs spec@mor-duongmh v0.x)

| Removed | Replacement |
|---|---|
| `/spec:setup` | Not needed — self-contained |
| `/spec:apply` | `/superpowers:execute-plan` or `/superpowers:subagent-driven-development` |
| `/spec:brainstorm` | `/superpowers:brainstorm` |

## Tests

```bash
cd plugins/mor-kit/tests
bash run-all.sh
```

Test coverage: 9 test files, 137+ assertions, including cross-platform `stat`/`date` cases. CI runs the matrix on macOS + Ubuntu.

## License

[MIT](../../LICENSE) © Mor.
