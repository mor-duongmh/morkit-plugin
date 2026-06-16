# Update Workflow

`/morkit:docs update [path]`

Refresh an existing doc taxonomy against code changes. Manual/on-demand (no auto-sync). Uses front-matter `source_files` to find what drifted.

## Examples

```bash
# Refresh every doc that drifted since its `updated` date (shows drift list, asks scope)
/morkit:docs update

# Skip the scope-confirm gate — update all stale docs in one pass
/morkit:docs update --yes

# Maintain docs for a project in another directory
/morkit:docs update ../api-service

# Monorepo: refresh per-module docs, also write AGENTS.md, no gate
/morkit:docs update --scope module --agents --yes
```

Flow: drift list shown → confirm scope → re-scout changed areas → **bridge active change-specs (intent)** → content docs updated (code + spec, canonical rule) → MAP/anchors re-derived → root `CLAUDE.md` (and `AGENTS.md` when Codex detected) pointer refreshed through an approve gate → report (incl. drift).

## Preconditions
- `docs/` already holds a new-style taxonomy (`00-overview/` exists). If not → tell user to run `/morkit:init`.

## Steps

1. **Detect drift candidates.** For each doc with front-matter `source_files`, check whether those paths changed since the doc's `updated` date (git log / mtime). Build a list of stale docs.
2. **Scope confirm.** Present the stale list; ask which to update (default: all). Allow `--yes` to skip.
3. **Re-scout only the changed areas** (not the whole repo) — morkit-native dispatch, read-only.
3b. **Bridge active change-specs (read intent).** Fold each *active* morkit change into docs so the authored WHAT/WHY isn't lost when the change is archived — complementary to the code scout in Step 3 (code = HOW; specs = WHAT/WHY).
   - **Eligible change** = a folder under `${MORKIT_ROOT:-morkit/output/spec}/` NOT under `archive/` (`.meta.json.archived == false`) AND whose `tasks.md` is fully ticked (no `- [ ]`). Skip changes with pending tasks by default (incomplete spec must not pollute docs); may surface them as a warning. **Never read `archive/`.** Process eligible changes **oldest-first** (by `.meta.json.created_at`) so newer intent layers on top of older.
   - **Read the change artifacts:** `proposal.md`, `design.md`, `tasks.md` (always present — native morkit `propose` generates these). `spec.md` (or `specs/<cap>/spec.md`) exists only for OpenSpec-style / `morkit-driven`-schema changes — native `propose` does NOT generate it.
   - **WHAT source — spec.md when present, else fallback:** if `spec.md`/`specs/` exists, use its `### Requirement`/`#### Scenario` rows (table below) verbatim. **If absent (native change):** derive the WHAT from `proposal.md` Capabilities + "What changes" bullets, and test cases from `tasks.md` TDD test steps ("write failing test" lines). Fold the derived WHAT into the SAME targets (FEATURE-LIST / flows / TEST-MATRIX) — without WHEN/THEN scenario IDs, use the behavior bullets.
   - **Fold by the canonical-source rule** — who is the source of truth per doc:

   | Source | Canonical for | Folds into docs |
   |---|---|---|
   | CODE (Step 3 scout) | HOW (what exists) | SYS-SPEC behavior, SOURCE-MAP, DATA/API/UI-MAP |
   | `design.md` Decisions + alternatives | WHY | `20-design/ADR/NNN-slug.md` (MADR) |
   | `design.md` Risks / Trade-offs | WHY | `40-ai-coding/RISK-REGISTER` + `KNOWN-PITFALLS` |
   | `design.md` Tech Stack | WHY (intended) | `00-overview/STACK` (reconcile vs real manifest) |
   | `design.md` Non-Goals | WHY | `00-overview/SCOPE` (Out of Scope) |
   | `spec.md` `### Requirement` (SHALL) | WHAT | `10-requirements/FEATURE-LIST` (FR-###) |
   | `spec.md` `#### Scenario` WHEN/THEN | WHAT | `10-requirements/flows/FR-NNN-*` + `30-test/TEST-MATRIX` (1 scenario = 1 row) |
   | `spec.md` SHALL detail | WHAT | `20-design/.../SYS-SPEC` Business Rules (BR-###) |
   | `proposal.md` Why + Capabilities | WHY/WHAT | SCOPE + FR descriptions |
   | `tasks.md` Files (Create/Modify/Test) | anchors (hint) | SYS-SPEC Source Anchors + SOURCE-MAP (verify files exist) |

   - **Drift flag.** When a bridged requirement/scenario has NO matching code evidence (scout found no symbol/route/test for it), write it but set that doc's front-matter `status: drift` and annotate "⚠ spec asserts X — not found in code". Collect these into a **Drift list** for the Step 8 report. Code wins direct conflicts; specs never silently overwrite code-derived truth.
   - **FR-### dedup.** FEATURE-LIST is the single registry allocating FR-###. Match each capability by kebab slug against existing FR rows: existing → MODIFY in place (keep the FR-###); new → allocate the next FR-###. Never create a duplicate FR for one capability. Spec delta ops (spec.md only): `ADDED`→new FR · `MODIFIED`→update FR · `RENAMED`→rename, keep ID · `REMOVED`→mark Deprecated (carry Reason/Migration). Native (no spec.md): treat proposal Capabilities as ADD/MODIFY by slug match.
   - **Sequencing.** Run this bridge BEFORE `/morkit:archive` — once archived, a change is out of scope here and its intent is lost to docs.
4. **Update content docs first** (apply the canonical-source rule from Step 3b where code-scout and change-specs cover the same doc), then re-derive affected MAP/anchor files (same Scout → Content → MAP order, scoped).
5. **New components?** If scout finds a component with no folder yet (e.g. a DB was added), create the conditional folder + its doc.
6. **Bump `updated`** on every touched file; preserve manual edits outside the regenerated sections where possible.
6b. **Refresh agent-instructions** (`references/agent-instructions.md`): rebuild the root agent-instruction pointer block your harness auto-loads (`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex; + the other if detected) from the current docs. Expect state `[C]` — replace ONLY inside the marker; if the marker is gone, treat as `[B]` (append at end). No-op if unchanged. Approve gate per file.
7. **Validate** (same checks as init Stage 5): size, cross-links, front-matter, traceability. Confirm every `status: drift` doc is listed for review.
8. **Report**: docs updated, docs newly created, **change-specs bridged (N changes, M FR touched)**, **drift list** (spec assertions lacking code evidence), links fixed, agent-instructions touched, remaining gaps.

## Notes
- Auto-sync / diff-engine is intentionally out of scope (KISS). This is a guided manual refresh.
- Never silently overwrite a heavily hand-edited doc — if a doc diverged a lot from its `source_files`, surface it and ask.
- **Bridge reads active changes only** (`morkit/output/spec/`, not `archive/`); run `docs update` BEFORE `/morkit:archive` so each change's WHAT/WHY lands in docs first. Code stays canonical for HOW — specs are flagged as drift, never trusted blindly.
- A change **archived with pending tasks** (via archive's "archive anyway" override) is never bridge-eligible — its intent won't reach `docs/`. Bridge it (or finish its tasks) before archiving.
