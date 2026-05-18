---
name: generate-srs
description: "Generate or update Software Requirements Specification (SRS) following BrSE standards for ITO Japan. Renders the BrSE template-updated structure (13 sections + 2 appendices: Doc Control, Overview, Business Flow with UC detail, FR detail, Business Rules, Roles & Permissions, NFR with IPA-6 categories + Security/PII, Data Items with retention, External Interfaces, Reports, Acceptance/UAT, Traceability, Open Q&A, Constraints/Assumptions/Risks, Screen Index, Glossary). Init mode generates srs.md + per-screen specs from ProjectModel JSON; update mode applies a Delta to existing docs preserving manual edits."
category: documentation
keywords: [srs, brse, requirements, japanese-ito, screen-design, ipa-nfr, traceability, acceptance-criteria]
argument-hint: "init|update [options]"
metadata:
  author: docs-hero
  version: "2.0.0"
---

# Generate SRS Skill

Sub-skill for generating SRS + per-screen design specs. Owns `morkit/output/docs/srs.md` and
`docs/screen-specs/SCREEN-*.md`. Single-language output (JP / EN / VN).

## Environment (plugin context)

```bash
MORKIT_PLUGIN_ROOT="${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:?must be set by Claude Code or MORKIT_PLUGIN_ROOT must be set by Codex}}"
VENV="${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data}}/docs-hero/.venv"
PY="${VENV}/bin/python3"
SRS_SCRIPTS="${MORKIT_PLUGIN_ROOT}/skills/generate-srs/scripts"
SRS_TEMPLATES="${MORKIT_PLUGIN_ROOT}/skills/generate-srs/templates"
ORCH_SCRIPTS="${MORKIT_PLUGIN_ROOT}/skills/docs-hero-orchestrator/scripts"
PROJECT_DOCS_DIR="${PWD}/docs"
PROJECT_META="${PWD}/.docs-hero-meta.json"
```

## Output Structure (template-updated)

13 numbered sections + 2 appendices:

| § | Section | Entities |
|---|---------|---------|
| 0 | Document Control Rules | (status & priority definitions) |
| 1 | Overview | TargetRelease, Reference (REF), OpenQuestion (Q), Stakeholder |
| 2 | Current State & Business Flow | Issue (ISSUE), UseCase (UC) with detail |
| 3 | Functional Requirements | FunctionalRequirement (FR) with validation/permission/audit/AC/test viewpoints + Implementation Status dashboard |
| 4 | Business Rules | BusinessRule (BR) |
| 5 | Roles & Permissions | Role (ROLE), PermissionEntry matrix |
| 6 | Non-Functional Requirements | NFR (IPA-6 categories), SecurityPiiItem |
| 7 | Data Items | EntityDef (ENT), DataItem (DATA), DataRetention |
| 8 | External Interfaces | ExternalInterface (INT) + file-interface detail |
| 9 | Reports & Files | Report (RPT), ReportItem |
| 10 | Acceptance Criteria & UAT | AcceptanceCriterion (AC), UatCriterion |
| 11 | Traceability Matrix | TraceabilityRow (auto-derived from FR if absent) |
| 12 | Open Issues & Q&A | OpenQuestion (Q) |
| 13 | Constraints, Assumptions & Risks | Constraint (CONS), Assumption (ASM), Risk (RISK) |
| A | Screen Index | Screen (SCREEN) |
| B | Glossary | GlossaryEntry |

## Modes

## Modes

| Mode | Purpose |
|---|---|
| `init` | Render SRS + screen specs from a ProjectModel JSON |
| `update` | Apply Delta filtered for SRS scope (FR/NFR/SCREEN/DATA/INT/UC/BR/ROLE/RPT/AC/Q/CONS/ASM/ENT/REF/RISK/ISSUE) |

## Implementation Status (§3 dashboard + per-FR badge)

Every `FunctionalRequirement` carries two status fields:

- `doc_status` (existing): document-review state — Draft / In Review / Reviewed / Approved / Deferred
- `impl_status` (new): implementation progress — `NotStarted` ⬜ / `InProgress` 🟡 / `Done` 🟢 / `Verified` 🔵 / `Blocked` 🔴

`render_srs.py` renders both as separate columns in §3.1 FR list and as separate
rows in §3.2 FR detail, plus an "Implementation Status Snapshot" table at the
top of §3 (counts + % per status). Optional `evidence_refs` (list of
`{kind, ref, note}` where `kind ∈ openspec | commit | test | code | manual`) are
shown in the FR detail as an Evidence row when present.

The orchestrator populates `impl_status` + `evidence_refs` BEFORE calling this
skill (see `commands/init.md` "Status detection" step). This skill is render-only
— it does not scan the repo itself.

## Init Workflow

```bash
"$PY" "$SRS_SCRIPTS/render_srs.py" \
  --project-model "$PROJECT_MODEL" \
  --template "$SRS_TEMPLATES/srs-template.md" \
  --language JP \
  --output "$PROJECT_DOCS_DIR/srs.md"

# Per screen:
"$PY" "$SRS_SCRIPTS/render_screen_spec.py" \
  --project-model "$PROJECT_MODEL" \
  --screen-id SCREEN-001 \
  --template "$SRS_TEMPLATES/screen-spec-template.md" \
  --language JP \
  --output "$PROJECT_DOCS_DIR/screen-specs/SCREEN-001-${SLUG}.md"

# Mockup annotation when image provided at assets/screens/SCREEN-001-{slug}.png:
#   1. Use Read tool on the image (Claude vision native)
#   2. Apply prompt from references/screen-vision-prompt.md
#   3. Save vision JSON to .tmp/mockup-SCREEN-001.json
#   4. Run annotate_mockup.py to draw numbered circles
"$PY" "$SRS_SCRIPTS/annotate_mockup.py" \
  --image "${PWD}/assets/screens/SCREEN-001-login.png" \
  --items "${PWD}/.tmp/mockup-SCREEN-001.json" \
  --output "${PWD}/assets/screens/SCREEN-001-login-annotated.png"
```

## Update Workflow

The orchestrator pre-filters the Delta to SRS-relevant entity types
(FR, NFR, SCREEN, DATA, INT) and runs the standard diff-engine flow:

```bash
"$PY" "$ORCH_SCRIPTS/detect_manual_edits.py" \
  --doc "$PROJECT_DOCS_DIR/srs.md" \
  --meta "$PROJECT_META" \
  --output "${PWD}/.tmp/srs-edits.json"

"$PY" "$ORCH_SCRIPTS/compute_diff.py" \
  --delta "${PWD}/.tmp/srs-delta.json" \
  --doc "$PROJECT_DOCS_DIR/srs.md" \
  --manual-edits "${PWD}/.tmp/srs-edits.json" \
  --output "${PWD}/.tmp/srs-plan.json"

"$PY" "$ORCH_SCRIPTS/apply_patch.py" \
  --plan "${PWD}/.tmp/srs-plan.json" \
  --doc "$PROJECT_DOCS_DIR/srs.md" \
  --meta "$PROJECT_META"
```

Sub-skill responsibility on update: re-resolve mockups for any new/changed
screens, then re-run `render_screen_spec.py` for those screens.

## Sync Mode

**Not supported.** Requirements cannot be inferred from code — only init + update.

## File Ownership

This skill owns:
- `morkit/output/docs/srs.md`
- `docs/screen-specs/SCREEN-*.md`
- `assets/screens/*-annotated.png`

It does **not** modify:
- `morkit/output/docs/api-docs.md`
- `morkit/output/docs/database-design.md`
- Original mockup images at `assets/screens/SCREEN-*.{png,jpg,webp}`

## References

- `templates/srs-template.md` — full SRS structure (BrSE standard)
- `templates/screen-spec-template.md` — per-screen detail with numbered items
- `references/brse-srs-standard.md` — IPA non-functional categories + numbering
- `references/screen-vision-prompt.md` — Claude vision prompt for mockup analysis
