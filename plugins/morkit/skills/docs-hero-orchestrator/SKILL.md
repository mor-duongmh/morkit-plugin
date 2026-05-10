---
name: docs-hero
description: "Generate or update full project documentation suite (SRS / API / DB / system-architecture / code-standards / codebase-summary / design-guidelines — user picks via /morkit:init multi-select gate). Orchestrates 7 sub-skills with conflict-minimal updates from OpenSpec changes, brainstorm plans, or codebase scans. Standards: BrSE ITO Japan (SRS), arc42-lite (arch), Conventional Commits (standards), MADR (guidelines). Supports init / update / sync."
category: documentation
keywords: [docs, srs, api, database, arch, standards, codebase, adr, brse, openspec, arc42, madr, conventional-commits, ito, japan]
argument-hint: "init|update|sync|apply-sync|rebuild-meta [options]"
metadata:
  author: docs-hero
  version: "2.0.0"
---

# Docs Hero Orchestrator

Single entry point for the documentation generation pipeline. Coordinates seven
sub-skills (`generate-srs`, `generate-api-docs`, `generate-db-design`,
`generate-system-architecture`, `generate-code-standards`,
`generate-codebase-summary`, `generate-design-guidelines`) with shared parsers,
the diff engine, atomic write, and a session lock.

## Outputs at a glance

| Flag | Doc | Standard | Update | Sync |
|---|---|---|---|---|
| `srs` | `docs/srs.md` (+ `screen-specs/SCREEN-*.md`) | BrSE ITO Japan | ✅ | ❌ |
| `api` | `docs/api-docs.md` | REST + cURL + errors | ✅ | ✅ |
| `db` | `docs/database-design.md` | Tables + Mermaid ERD | ✅ | ✅ |
| `arch` | `docs/system-architecture.md` | arc42-lite + Mermaid | ✅ | ✅ |
| `standards` | `docs/code-standards.md` | Conventional Commits + auto-style | ✅ | ✅ |
| `summary` | `docs/codebase-summary.md` | README-style | ✅ | ✅ |
| `guidelines` | `docs/design-guidelines.md` (+ `adr/{id}-{slug}.md`) | MADR | ✅ | ❌ (manual) |

`guidelines` does not participate in `update` flow's auto-iteration (it's
omitted from `_DOC_FILES`); use explicit `--from-plan` / `--from-openspec`
deltas with `entity_type ∈ {DPR, PTN, ADR}` to push changes manually.

## Environment (plugin context)

This skill runs as a Claude Code plugin. Path resolution uses these variables:

```bash
# Plugin root (set by Claude Code at runtime)
CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:?must be set by Claude Code}"

# Python venv (created by /morkit:setup)
VENV="${HOME}/.claude/plugins/data/docs-hero/.venv"
PY="${VENV}/bin/python3"

# Skill scripts (within plugin)
ORCH_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/docs-hero-orchestrator/scripts"
SRS_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-srs/scripts"
API_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-api-docs/scripts"
DB_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-db-design/scripts"
ARCH_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-system-architecture/scripts"
STD_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-code-standards/scripts"
SUM_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-codebase-summary/scripts"
GUI_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-design-guidelines/scripts"

# Project paths (always relative to user's cwd, NOT plugin root)
PROJECT_DOCS_DIR="${PWD}/docs"
PROJECT_META="${PWD}/.docs-hero-meta.json"
PROJECT_LOCK="${PWD}/.docs-hero.lock"
PROJECT_TMP="${PWD}/.tmp"
```

**Pre-flight check** every mutating operation must perform:

```bash
test -d "$VENV" || { echo "ERROR: venv missing. Run /morkit:setup first." >&2; exit 1; }
```

## Operations

| Command | Purpose |
|---|---|
| `/docs-hero init` | Create docs from inputs (PDF/Excel/Docx/OpenSpec + codebase) |
| `/docs-hero update --from-plan {path}` | Apply changes from a brainstorm plan.md |
| `/docs-hero update --from-openspec [name]` | Apply 1 OpenSpec change |
| `/docs-hero sync` | Generate sync proposals (codebase → docs) — read-only |
| `/docs-hero apply-sync --proposal {path}` | Apply approved sync proposal |
| `/docs-hero rebuild-meta` | Bootstrap `.docs-hero-meta.json` from existing docs |

## Routing Logic

Parse first arg:
- `init` → init flow (collect inputs → parse → user picks subset of 7 outputs → render)
- `update` → parse `--from-{plan,openspec}` → Delta → diff engine → apply (iterates `_DOC_FILES`; `guidelines` is intentionally excluded)
- `sync` → fan out to sub-skills' `*_sync_propose.py` for `api`/`db`/`arch`/`standards`/`summary` (no doc mutation; `srs` and `guidelines` skip)
- `apply-sync` → call sub-skill's `*_sync_apply.py` to convert proposal → Delta → run update
- `rebuild-meta` → meta-manager rebuild
- empty → AskUserQuestion (5 operations)

Allowed `--outputs` values: `srs`, `api`, `db`, `arch`, `standards`, `summary`, `guidelines` (comma-separated, multi-select).

## Init Flow

**Doc-type selection (REQUIRED before dispatch):** when invoked via `/docs-hero:init`
without an explicit `--outputs` flag, the caller (slash command) MUST ask the user
via AskUserQuestion which doc types to generate (multi-select: SRS / API docs /
DB design) and pass the resolved comma-separated list as `--outputs`. Never
default silently to all three — the user picks. See `commands/init.md` for the
exact question template.

```bash
# Pre-flight
test -d "$VENV" || { echo "ERROR: run /morkit:setup first." >&2; exit 1; }
mkdir -p "$PROJECT_TMP"

# 1. Parse inputs → ProjectModel JSON
"$PY" "$ORCH_SCRIPTS/parse_inputs.py" \
  --inputs "$INPUT_DIR" \
  --output "$PROJECT_TMP/raw-bundle.json"

# 1b. Implementation status detection (LLM-driven, populates FR.impl_status
#     + FR.evidence_refs in project-model.json BEFORE the plan is written).
#     Order of evidence (later signals upgrade earlier ones):
#       a. openspec/changes/{id}/ archived         → Done   (kind=openspec)
#       b. openspec/changes/{id}/ pending          → InProgress (kind=openspec)
#       c. openspec/specs mention                  → InProgress (kind=openspec)
#       d. FR-ID in source files / git log --grep  → InProgress (kind=code|commit)
#       e. FR-ID in test files                     → Verified  (kind=test)
#     Manual override (impl_status already set in inputs) wins over auto-detect.
#     FRs with no signal stay NotStarted.

# 2. Gap & Risk analysis → docs-plan.md (LLM-driven, REQUIRED gate)
#    Claude reads project-model.json + raw inputs and writes
#    $PROJECT_TMP/docs-plan.md with sections in this order:
#      §0 Project Overview — what it is, phase, stack, stakeholders
#         mentioned, doc maturity, source input quality (per-input notes
#         on completeness/conflicts), entity counts, render strategy.
#      §1 Per-doc plan — sections × source entities for each selected
#         output (srs / api / db).
#      §2 Gaps — severity-tagged: blocker | warning | info.
#      §3 Risks — scope creep, conflicts, undocumented deps, etc.
#      §4 Implementation Status Snapshot — counts by status + per-FR
#         table from step 1b. Mirrors what SRS §3 will render.
#      §5 Recommended action per gap — ask user / placeholder <TBD: ...> /
#         drop section / proceed with explicit assumption.
#
#    Then present a summary via AskUserQuestion:
#      [Proceed | Revise plan | Abort]
#    Only on "Proceed" continue. On "Revise plan" capture user
#    feedback and rewrite docs-plan.md, re-prompt.

# 2b. Honor plan decisions BEFORE dispatch:
#     For each gap whose action is "placeholder", Claude edits
#     project-model.json in place to set the affected field to
#     "<TBD: <reason>>" so sub-skills emit the placeholder verbatim
#     instead of guessing. For "drop section" decisions, the relevant
#     entities are removed from project-model.json. For "assumption"
#     decisions the assumption is written into the entity's
#     description prefixed with "[ASSUMPTION] ".

# 3. Dispatch to sub-skills (CLAUDE_PLUGIN_ROOT inherited from env)
#    $OUTPUTS = user-selected subset, e.g. "srs,api" or "srs,api,db"
"$PY" "$ORCH_SCRIPTS/dispatch_coordinator.py" init \
  --project-model "$PROJECT_TMP/project-model.json" \
  --language EN \
  --outputs "$OUTPUTS" \
  --docs-dir "$PROJECT_DOCS_DIR"

# 4. Aggregate report
"$PY" "$ORCH_SCRIPTS/aggregate_report.py" \
  --docs-dir "$PROJECT_DOCS_DIR" \
  --output "$PROJECT_TMP/init-report.md"

# 4b. Claude appends a "Gaps & Risks" section to init-report.md by
#     copying the unresolved entries from docs-plan.md (those whose
#     action was "placeholder" or "assumption"). Resolved gaps are
#     omitted.

# 5. Spawn docs-hero agent for QA review (Skill tool: docs-hero)
#    The QA agent must cross-check that every blocker/warning gap
#    from docs-plan.md is either resolved in the rendered docs or
#    explicitly carried forward as a <TBD: ...> placeholder.
```

## Update Flow

```bash
# Pre-flight + lock
test -d "$VENV" || { echo "ERROR: run /morkit:setup first." >&2; exit 1; }
"$PY" "$ORCH_SCRIPTS/lock_manager.py" acquire --lock "$PROJECT_LOCK" || exit 1
trap '"$PY" "$ORCH_SCRIPTS/lock_manager.py" release --lock "$PROJECT_LOCK"' EXIT

# 1. Parse delta source
"$PY" "$ORCH_SCRIPTS/parse_plan.py"     --plan "$PLAN_PATH"           --output "$PROJECT_TMP/delta.json"
# OR
"$PY" "$ORCH_SCRIPTS/parse_openspec.py" --change-dir "$OPENSPEC_DIR"  --output "$PROJECT_TMP/delta.json"

# 2. dispatch_coordinator update mode automates: filter delta by entity_type per doc,
#    detect manual edits, compute diff, apply patch.
"$PY" "$ORCH_SCRIPTS/dispatch_coordinator.py" update \
  --delta "$PROJECT_TMP/delta.json" \
  --docs-dir "$PROJECT_DOCS_DIR" \
  --meta "$PROJECT_META"

# 3. Aggregate + spawn docs-hero agent
```

## Sync Flow (2-step)

Step 1 — propose (read-only, no lock):
```bash
"$PY" "$API_SCRIPTS/api_sync_propose.py" \
  --codebase-paths "$CODEBASE_PATHS" \
  --existing-doc "$PROJECT_DOCS_DIR/api-docs.md" \
  --output "$PROJECT_TMP/api-sync-proposal.md"

"$PY" "$DB_SCRIPTS/db_sync_propose.py" \
  --codebase-paths "$CODEBASE_PATHS" \
  --existing-doc "$PROJECT_DOCS_DIR/database-design.md" \
  --output "$PROJECT_TMP/db-sync-proposal.md"
# SRS sync not supported (requirements cannot be inferred from code)
```

Step 2 — apply-sync (after user ticks checkboxes):
```bash
"$PY" "$API_SCRIPTS/api_sync_apply.py" \
  --proposal "$PROJECT_TMP/api-sync-proposal.md" \
  --output "$PROJECT_TMP/api-delta.json"

# Then run standard update flow with the resulting delta
"$PY" "$ORCH_SCRIPTS/dispatch_coordinator.py" update \
  --delta "$PROJECT_TMP/api-delta.json" \
  --docs-dir "$PROJECT_DOCS_DIR" \
  --meta "$PROJECT_META"
```

## Lock Acquisition (mutating ops only)

Before any mutate:
1. `"$PY" "$ORCH_SCRIPTS/lock_manager.py" acquire --lock "$PROJECT_LOCK"`
2. If lock exists + valid (PID alive, < 1h) → exit
3. If stale → cleanup + acquire
4. On exit → release

Read-only ops (sync propose, rebuild-meta verify) skip the lock.

## File Ownership

The orchestrator owns:
- `.docs-hero-meta.json` (sidecar, gitignored)
- `.docs-hero.lock` (transient, gitignored)
- Coordination scripts in `scripts/`

Sub-skills own their respective doc files (see each `SKILL.md`).

## References

- Templates: each sub-skill's `templates/`
- Phase specs: `plans/260503-2222-generate-prd-skill/phase-*.md`
- Schema: `scripts/lib/normalized_schema.py` (Pydantic single source of truth)
- Diff engine: `scripts/compute_diff.py` + `scripts/apply_patch.py`
