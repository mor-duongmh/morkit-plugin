# Changelog

All notable changes to the Mor claude-plugins marketplace are tracked here.

## [mor-kit@1.0.0] — 2026-05-10

**Plugin rename:** `spec@mor-duongmh` → `mor-kit@mor-duongmh`. Marketplace install:

```
/plugin uninstall spec@mor-duongmh
/plugin install mor-kit@mor-duongmh
```

### Breaking changes

- **Plugin renamed:** `spec` → `mor-kit`. All slash commands, env vars, paths, and skill names follow.
- **Folder convention:** `spec/changes/<name>/` → `mor-kit/changes/<name>/`. Marker file `.mor-spec` → `.mor-kit`. Env override `MOR_SPEC_ROOT` → `MOR_KIT_ROOT`.
- **Removed commands** (replaced by superpowers):
  - `/spec:apply` → `/superpowers:execute-plan` or `/superpowers:subagent-driven-development`
  - `/spec:brainstorm` → `/superpowers:brainstorm`
  - `/spec:setup` → no replacement; plugin is self-contained
- **Removed skills:** `spec-apply`, `spec-explore`, `spec-setup`. Their functionality is provided by upstream `superpowers` (executing-plans, subagent-driven-development, brainstorming).
- **Skill renames** (drop redundant `spec-` prefix):
  - `spec-propose` → `propose` (invoked as `mor-kit:propose`)
  - `spec-review` → `review` (invoked as `mor-kit:review`)
  - `spec-archive` → `archive` (invoked as `mor-kit:archive`)

### Changed

- `pre-tool-checklist-gate.sh`: matcher list now gates only `superpowers:executing-plans`, `superpowers:subagent-driven-development`, plus legacy `openspec-apply-change` for v1 grace period.
- `superpowers` overlay skills (`executing-plans`, `subagent-driven-development`): updated to use `${MOR_KIT_ROOT:-mor-kit/changes}/` with dual-read fallback to legacy `openspec/changes/`.
- All scripts, tests, hooks, README, and CI workflow paths updated for `mor-kit/` convention.

### Migration

```bash
# At your project root, for each project that used spec@mor-duongmh:
bash ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-from-openspec.sh --dry-run   # preview
bash ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-from-openspec.sh             # execute
```

Migration script handles `openspec/changes/` → `mor-kit/changes/` and creates the new marker. Already-on-`spec/changes/` (intermediate v2, never released) projects: rename folder manually `mv spec/changes mor-kit/changes && mv mor-kit/changes/.mor-spec mor-kit/changes/.mor-kit`.

### Files

- Plugin folder: `plugins/spec/` → `plugins/mor-kit/`
- Plugin manifest version: `0.3.0` → `1.0.0` (rename = major reset)
- Marketplace entry: `name: "spec"` → `name: "mor-kit"`

---

## [superpowers@5.0.7+mor.1] — 2026-05-10

### Changed (overlay only — vendored upstream unchanged)

- `overlay/skills/executing-plans/SKILL.md`: Pre-flight gate updated to dual-read `${MOR_SPEC_ROOT:-spec/changes}/` first, fall back to `openspec/changes/` (with deprecation warning). NUL-delimited path handling for safety with paths containing spaces.
- `overlay/skills/subagent-driven-development/SKILL.md`: Same dual-read update.

These changes mirror the dual-read logic in `pre-tool-checklist-gate.sh` so the skill-level defense layer continues to enforce the gate after a project migrates from v1 to v2 of the `spec` plugin.

No upstream `obra/superpowers` files modified. Vendored version remains pinned at upstream `5.0.7`.

---

## [spec@2.0.0] — 2026-05-10 — UNRELEASED, superseded by mor-kit@1.0.0

> Note: spec@2.0.0 was an intermediate self-contained iteration that never shipped. The same architecture (no OpenSpec CLI, native scaffold) is now in `mor-kit@1.0.0` with renamed folder/env/marker. Below is preserved for historical reference.

### Breaking changes

- **Folder convention changed:** `openspec/changes/<name>/` → `spec/changes/<name>/`. The plugin now scaffolds artifacts directly without an OpenSpec `init` step.
- **Removed `/spec:setup`** from active workflow. The command is preserved as a deprecation no-op in v2 and will be deleted in v3.
- **Removed all OpenSpec CLI dependency:**
  - `npx -y @fission-ai/openspec@latest new change` → `scripts/scaffold-change.sh`
  - `npx -y @fission-ai/openspec@latest list` → `scripts/list-changes.sh`
  - `npx -y @fission-ai/openspec@latest schema validate` → `scripts/validate-tasks.sh`
  - `npx -y @fission-ai/openspec@latest archive` → `mv` to `spec/changes/archive/<name>/`
- **Skills renamed:**
  - `openspec-propose` → `spec-propose`
  - `openspec-apply-change` → `spec-apply`
  - `openspec-archive-change` → `spec-archive`
  - `openspec-explore` → `spec-explore`
- **Plugin install once = ready.** Marketplace install now provides every command in any project. No per-project setup, no schema copy, no folder structure pre-requisite.

### Added

- `scripts/scaffold-change.sh` — native scaffold with kebab-case validation, atomic creation, `.meta.json`, marker file
- `scripts/list-changes.sh` — list active and/or archived changes as JSON or text
- `scripts/validate-tasks.sh` — bash regex schema validator with rules R1-R6 and `--explain` / `--rule` flags
- `scripts/migrate-from-openspec.sh` — automated migration with `--dry-run` and `--keep-openspec`
- `scripts/lib/common.sh` — cross-platform shared helpers (`stat`, ISO timestamps, kebab validator, atomic writes)
- `templates/{proposal,design,tasks}.md.tpl` — change folder templates
- `tests/` — 11 test files, ~164 assertions, with cross-platform CI matrix (macOS + Ubuntu)
- `.github/workflows/spec-tests.yml` — CI workflow matrix
- `.mor-spec` marker file in `spec/changes/` — distinguishes plugin-owned `spec/` from RSpec/Jasmine test folders
- `MOR_SPEC_ROOT` env var — override the default `spec/changes/` path

### Changed

- `hooks/pre-tool-checklist-gate.sh`: now checks `${MOR_SPEC_ROOT:-spec/changes}` with 1-version dual-read fallback to legacy `openspec/changes/` (with deprecation warning); skill matcher list extended with new skill names while preserving v1 compatibility
- `hooks/session-start.sh`: detects legacy `openspec/changes/` and suggests migration; quiet on RSpec-style `spec/` without `spec/changes/`
- `scripts/generate-checklist.sh`: usage hint and help text updated to mention new convention; core fetch logic unchanged
- `skills/spec-review/SKILL.md`: path resolution honors `MOR_SPEC_ROOT`
- `skills/spec-explore/SKILL.md`: rewritten to use `list-changes.sh` instead of OpenSpec CLI; "stance, not workflow" preserved
- `skills/spec-{propose,apply,archive}/SKILL.md`: rewritten to call native scripts
- `commands/{propose,apply,archive,brainstorm,review,setup}.md`: all updated for v2 conventions
- `plugins/spec/.claude-plugin/plugin.json`: version → `2.0.0`, description rewritten

### Removed

- `skills/spec-setup/`
- `skills/openspec-propose/`
- `skills/openspec-apply-change/`
- `skills/openspec-archive-change/`
- `skills/openspec-explore/`

### Migration guide

Run at your project root:

```bash
# Preview
bash ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-from-openspec.sh --dry-run

# Execute (preserves archive/, removes empty openspec/)
bash ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-from-openspec.sh
```

The hook has a 1-version dual-read fallback. Even without migrating, `/spec:apply` continues to work against legacy `openspec/changes/` until the v3 release. You'll see a deprecation warning in stderr.

### Known issues / deferred to v2.1

- Python `jsonschema` validator fallback (currently bash regex only)
- Schema rule version files (`schemas/superpowers-driven/rules.v1.json`) — currently embedded in script
- `/spec:doctor` diagnostic command for residual `openspec/`, conflict markers, env mismatch
- Drift detection for upstream Superpowers skill renames

### Files

- Plan: [`docs/superpowers/plans/2026-05-10-spec-self-contained.md`](docs/superpowers/plans/2026-05-10-spec-self-contained.md)
- Design: [`docs/superpowers/specs/2026-05-10-spec-self-contained-design.md`](docs/superpowers/specs/2026-05-10-spec-self-contained-design.md)
