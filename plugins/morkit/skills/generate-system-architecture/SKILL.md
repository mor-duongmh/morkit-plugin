---
name: generate-system-architecture
description: "Generate or update system architecture document (arc42-lite, 8 sections) with embedded Mermaid component diagram. Init renders system-architecture.md from ProjectModel; update applies a Delta filtered for arch scope (CMP/LAY/INX/QG); sync scans the codebase (services / packages / Dockerfile / k8s / import graph) and proposes Add/Deprecate per Component."
category: documentation
keywords: [architecture, arc42, mermaid, components, layers, c4]
argument-hint: "init|update|sync|apply-sync [options]"
metadata:
  author: morkit
  version: "1.0.0"
---

# Generate System Architecture Skill

Sub-skill that owns `docs/system-architecture.md`. Single-language output (JP / EN / VN).
Embeds a Mermaid `flowchart LR` with subgraphs per Layer.

## Environment (plugin context)

```bash
MORKIT_PLUGIN_ROOT="${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:?must be set by Claude Code or MORKIT_PLUGIN_ROOT must be set by Codex}}"
VENV="${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data}}/docs-hero/.venv"
PY="${VENV}/bin/python3"
ARCH_SCRIPTS="${MORKIT_PLUGIN_ROOT}/skills/generate-system-architecture/scripts"
ORCH_SCRIPTS="${MORKIT_PLUGIN_ROOT}/skills/docs-hero-orchestrator/scripts"
PROJECT_DOCS_DIR="${PWD}/docs"
PROJECT_META="${PWD}/.docs-hero-meta.json"
```

## Modes

| Mode | Purpose |
|---|---|
| `init` | Render `docs/system-architecture.md` from a ProjectModel JSON |
| `update` | Apply Delta filtered for arch scope (CMP / LAY / INX / QG) |
| `sync` | Scan codebase (services / packages / Dockerfile / k8s / imports), write proposal — DOES NOT touch docs |
| `apply-sync` | Read proposal (with user-checked boxes) → convert to Delta |

## Init Workflow

```bash
"$PY" "$ARCH_SCRIPTS/render_system_architecture.py" \
  --project-model "$PROJECT_MODEL" \
  --language EN \
  --output "$PROJECT_DOCS_DIR/system-architecture.md"
```

Section IDs (stable for diff engine):

```
CMP-{id}        # Per-component H3 anchor in §5 (e.g. CMP-001)
LAY-{id}        # Per-layer (referenced inline in §5 table)
INX-{id}        # Per-interaction (referenced inline in §6 table)
QG-{id}         # Per-quality-goal (referenced inline in §1.2 table)
ARCH-DIAGRAM    # Single Mermaid block in §5 (delimited <!-- ARCH-DIAGRAM-START/END -->)
```

## Update Workflow

The orchestrator pre-filters Delta to arch scope, then runs the standard
diff-engine flow (`detect_manual_edits → compute_diff → apply_patch`).

## Sync Workflow (2-step)

### Step 1: propose

```bash
"$PY" "$ARCH_SCRIPTS/system_architecture_sync_propose.py" \
  --codebase-paths "$CODEBASE_PATHS" \
  --existing-doc "$PROJECT_DOCS_DIR/system-architecture.md" \
  --output "${PWD}/.tmp/arch-sync-proposal.md"
```

Detects Components from:
- Top-level dir conventions: `apps/*`, `services/*`, `packages/*`
- Container manifests: `Dockerfile`, `docker-compose.yml`, `k8s/*.yaml`
- Reuses `parse_codebase_routes.py` (services owning HTTP endpoints) and
  `parse_codebase_models.py` (datastore Components from ORM scans)
- Coarse `depends_on` edges via directory-level imports (any file in
  `services/A/**` importing `services/B/**` → CMP-A → CMP-B)

Diffs against documented Components, writes a markdown proposal with
`[ ]` checkboxes. **No doc changes.**

### Step 2: apply-sync

```bash
"$PY" "$ARCH_SCRIPTS/system_architecture_sync_apply.py" \
  --proposal "${PWD}/.tmp/arch-sync-proposal.md" \
  --output "${PWD}/.tmp/arch-delta.json"
```

Parses checked items, emits Delta JSON for the standard update flow.

## File Ownership

This skill owns:
- `docs/system-architecture.md`

It does **not** modify:
- `docs/srs.md`
- `docs/api-docs.md`
- `docs/database-design.md`
- `docs/code-standards.md`
- `docs/codebase-summary.md`
- `docs/design-guidelines.md`

## References

- `templates/system-architecture-template.md` — arc42-lite skeleton
- arc42 reference: <https://docs.arc42.org/home/>
