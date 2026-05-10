# Plugin `spec` Self-Contained Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> ⚠️ **PLAN-REVIEW-GATE REQUIRED:** Per `feedback_plan_review_gate` user memory rule, before executing this plan you MUST generate a developer review checklist (`/spec:review`), tick all applicable items, and set `Overall Decision: OK`. Implementation skills will refuse to proceed until gate is open.

> 🌀 **Bootstrap paradox notice:** This plan removes OpenSpec dependency from the `spec` plugin, but the plan-review-gate currently expects `openspec/changes/<name>/review-checklist.md`. Workaround: scaffold this plan's change folder at `openspec/changes/spec-self-contained-redesign/` for the duration of execution; after Phase 7 ships, the migration script auto-converts it to `spec/changes/`.

**Goal:** Refactor the `spec` plugin so that a single `/plugin install spec@mor-duongmh` makes every command operational in any project — no `/spec:setup`, no `npx openspec init`, no schema copy. Replace OpenSpec CLI usage with native bash scaffolding under a plugin-owned folder convention `spec/changes/`.

**Architecture:** Plugin owns the change-folder lifecycle end-to-end. Scaffold engine writes `spec/changes/<name>/{proposal,design,tasks,.meta}.md` directly. Schema validation is a bash regex pass over `tasks.md` against rules R1–R6 (see Appendix B). The PreToolUse hook is rewritten to look for `spec/changes/` plus a `.mor-spec` marker file (RSpec/Jasmine collision guard). All paths honor `MOR_SPEC_ROOT` env override. The Google-Doc-driven review checklist mechanism (`fetch-checklist.sh`, `generate-checklist.sh`) is preserved unchanged in core logic; only path defaults shift.

**Tech Stack:** Bash 4+ (scripts, hooks, tests), `jq` (JSON read/write), `curl` (existing fetch), `awk` / `grep -E` (validation rules), `find` + cross-platform `stat` (mtime sort), Markdown (skills, commands, templates). No new runtime dependencies — `openspec` and `npx @fission-ai/openspec` are removed.

**Folder convention:** `spec/changes/<name>/` (active) and `spec/changes/archive/<name>/` (archived). Marker file `spec/changes/.mor-spec` distinguishes plugin-owned `spec/` from RSpec-style test directories. Override via `MOR_SPEC_ROOT=mor/changes` env var.

**Source paths:**
- Plugin root: `/Users/haiduong/Documents/work/claude-plugins/plugins/spec/`
- Reference plugin: `/Users/haiduong/Documents/work/claude-plugins/plugins/superpowers/` (vendor + tests pattern)

---

## File Structure

### New files
- `plugins/spec/scripts/scaffold-change.sh`
- `plugins/spec/scripts/list-changes.sh`
- `plugins/spec/scripts/validate-tasks.sh`
- `plugins/spec/scripts/migrate-from-openspec.sh`
- `plugins/spec/scripts/lib/common.sh` — cross-platform helpers
- `plugins/spec/templates/proposal.md.tpl`
- `plugins/spec/templates/design.md.tpl`
- `plugins/spec/templates/tasks.md.tpl`
- `plugins/spec/skills/spec-propose/SKILL.md`
- `plugins/spec/skills/spec-apply/SKILL.md`
- `plugins/spec/skills/spec-archive/SKILL.md`
- `plugins/spec/skills/spec-explore/SKILL.md`
- `plugins/spec/tests/test-helper.sh`
- `plugins/spec/tests/run-all.sh`
- `plugins/spec/tests/test-scaffold-change.sh`
- `plugins/spec/tests/test-list-changes.sh`
- `plugins/spec/tests/test-validate-tasks.sh`
- `plugins/spec/tests/test-generate-checklist.sh`
- `plugins/spec/tests/test-fetch-checklist.sh`
- `plugins/spec/tests/test-migrate-from-openspec.sh`
- `plugins/spec/tests/test-pre-tool-gate.sh`
- `plugins/spec/tests/test-session-start.sh`
- `plugins/spec/tests/integration/test-skill-flows.sh`
- `plugins/spec/tests/test-e2e.sh`
- `.github/workflows/spec-tests.yml`
- `docs/superpowers/specs/2026-05-10-spec-self-contained-design.md` — frozen decisions

### Modified files
- `plugins/spec/scripts/generate-checklist.sh` — default path hint `openspec/changes` → `spec/changes`
- `plugins/spec/hooks/pre-tool-checklist-gate.sh` — folder convention + marker check + skill matchers
- `plugins/spec/hooks/session-start.sh` — auto-prompt migration when `openspec/changes/` residual detected
- `plugins/spec/skills/spec-review/SKILL.md` — path resolution `openspec/changes/` → `spec/changes/`
- `plugins/spec/commands/propose.md` — invoke `spec-propose`
- `plugins/spec/commands/apply.md` — invoke `spec-apply`
- `plugins/spec/commands/archive.md` — invoke `spec-archive`
- `plugins/spec/commands/brainstorm.md` — invoke `spec-explore`
- `plugins/spec/commands/review.md` — path mention update
- `plugins/spec/commands/setup.md` — convert to deprecation notice (deleted in v3)
- `plugins/spec/README.md` — rewrite, drop OpenSpec mentions
- `claude-plugins/README.md` — workflow diagram + commands table update
- `plugins/spec/.claude-plugin/plugin.json` — major version bump 2.0.0

### Deleted files
- `plugins/spec/skills/spec-setup/SKILL.md`
- `plugins/spec/skills/openspec-propose/SKILL.md`
- `plugins/spec/skills/openspec-apply-change/SKILL.md`
- `plugins/spec/skills/openspec-archive-change/SKILL.md`
- `plugins/spec/skills/openspec-explore/SKILL.md`

### Conventions
- All scripts begin with `#!/usr/bin/env bash` and `set -euo pipefail`.
- All scripts must be executable (`chmod +x`).
- `lib/common.sh` is sourced by scripts AND tests; never auto-runs.
- Each script honors `MOR_SPEC_ROOT` env (default `spec/changes`).
- `${CLAUDE_PLUGIN_ROOT}` fallback: derive from script location when env empty.
- Cross-platform `stat`: `stat -f %m` (BSD) with `stat -c %Y` (GNU) fallback.
- Atomic write: `jq ... > $tmp && mv $tmp $target`.
- Test files exit non-zero on failure; aggregator runs them in subshells.

---

## Phase 0: Decision freeze (no logic, no tests)

**Files:**
- Create: `docs/superpowers/specs/2026-05-10-spec-self-contained-design.md`

**Decisions to capture:**
- [ ] Folder convention: `spec/changes/<name>/` (active) + `spec/changes/archive/<name>/` (archived)
- [ ] Marker file: `spec/changes/.mor-spec` containing `format_version: 1`
- [ ] Env override: `MOR_SPEC_ROOT` honored by every script
- [ ] Backward compat: hard cutover with migration script + 1-version dual-read in hook
- [ ] Schema validation: bash regex (R1–R6) — see Appendix B
- [ ] `/spec:setup` lifecycle: deprecation message in v2, deleted in v3
- [ ] OpenSpec CLI: removed entirely from skills

**Steps:**
- [ ] Write design doc capturing all decisions above
- [ ] Open PR for the design doc only (no code yet) — get team consensus
- [ ] Merge after sign-off

---

## Phase 1: Scaffold engine

### Task 1.1: `scaffold-change.sh` + templates

**Files:**
- Create: `plugins/spec/scripts/scaffold-change.sh`
- Create: `plugins/spec/scripts/lib/common.sh`
- Create: `plugins/spec/templates/proposal.md.tpl`
- Create: `plugins/spec/templates/design.md.tpl`
- Create: `plugins/spec/templates/tasks.md.tpl`
- Create: `plugins/spec/tests/test-helper.sh`
- Create: `plugins/spec/tests/test-scaffold-change.sh`

**TDD steps:**
- [ ] Write `test-helper.sh`: assert_equal, assert_contains, assert_file_exists, assert_exit_code, assert_json_path, isolated_tmpdir
- [ ] Write `test-scaffold-change.sh` with all 15 cases from Appendix B § 1 (pos/neg/edge/cross-platform)
- [ ] Run tests — expect all to fail
- [ ] Implement `lib/common.sh` (cross-platform stat, kebab-case validator, plugin-root resolver)
- [ ] Implement `scaffold-change.sh` (parse args, validate name, mkdir atomic, render templates, write `.meta.json`, ensure `.mor-spec` marker)
- [ ] Implement template files with placeholder substitution
- [ ] Run tests — expect 15/15 pass on macOS
- [ ] Run tests in Ubuntu Docker — expect 15/15 pass
- [ ] Commit

### Task 1.2: `list-changes.sh`

**Files:**
- Create: `plugins/spec/scripts/list-changes.sh`
- Create: `plugins/spec/tests/test-list-changes.sh`

**TDD steps:**
- [ ] Write `test-list-changes.sh` with 12 cases from Appendix B § 2
- [ ] Run tests — expect failure
- [ ] Implement `list-changes.sh` (scan folder, read `.meta.json`, sort by mtime, output JSON or text)
- [ ] Run tests — expect 12/12 pass on both OS
- [ ] Commit

### Task 1.3: `validate-tasks.sh`

**Files:**
- Create: `plugins/spec/scripts/validate-tasks.sh`
- Create: `plugins/spec/tests/test-validate-tasks.sh`

**TDD steps:**
- [ ] Write `test-validate-tasks.sh` with 15 cases (each rule R1–R6 has positive + negative)
- [ ] Run tests — expect failure
- [ ] Implement `validate-tasks.sh` with rule registry: R1 (header), R2 (task headings), R3 (Files block), R4 (checkbox per task), R5 (≥3 checkboxes total), R6 (schema_version match)
- [ ] Add `--explain` and `--rule` flags
- [ ] Run tests on both OS — expect 15/15 pass
- [ ] Commit

---

## Phase 2: Skills refactor

### Task 2.1: `spec-propose` skill

**Files:**
- Create: `plugins/spec/skills/spec-propose/SKILL.md`
- Delete: `plugins/spec/skills/openspec-propose/SKILL.md`

**Steps:**
- [ ] Draft skill content: AskUserQuestion for name+description → call `scaffold-change.sh` → AI fill artifacts → call `validate-tasks.sh` → call `generate-checklist.sh` → report
- [ ] Document required-input handling (refuse to scaffold without clear description)
- [ ] Add pre-flight check: refuse if `spec/changes/<name>/` already exists (use `--force` to override)
- [ ] Delete old `openspec-propose/SKILL.md`
- [ ] Manual smoke: invoke skill in scratch project, verify 4 files created
- [ ] Commit

### Task 2.2: `spec-apply` skill

**Files:**
- Create: `plugins/spec/skills/spec-apply/SKILL.md`
- Delete: `plugins/spec/skills/openspec-apply-change/SKILL.md`

**Steps:**
- [ ] Port pre-flight Step 0 from `openspec-apply-change` (review-checklist gate)
- [ ] Update path: `openspec/changes/` → `spec/changes/`
- [ ] Replace `npx openspec list` with `bash ${CLAUDE_PLUGIN_ROOT}/scripts/list-changes.sh --json`
- [ ] Replace `npx openspec instructions` with read tasks.md directly
- [ ] Implement task selection: first unchecked `- [ ]` group
- [ ] Implement progress tracking: tick checkbox after each completion via Edit
- [ ] Delete old `openspec-apply-change/SKILL.md`
- [ ] Smoke test in scratch project
- [ ] Commit

### Task 2.3: `spec-archive` skill

**Files:**
- Create: `plugins/spec/skills/spec-archive/SKILL.md`
- Delete: `plugins/spec/skills/openspec-archive-change/SKILL.md`

**Steps:**
- [ ] Replace `npx openspec list` with `list-changes.sh`
- [ ] Replace `npx openspec archive` with `mv` to `spec/changes/archive/<name>/`
- [ ] Update `.meta.json.archived_at` (atomic jq write)
- [ ] AskUserQuestion to confirm archive target
- [ ] Delete old skill
- [ ] Smoke test
- [ ] Commit

### Task 2.4: `spec-explore` skill

**Files:**
- Create: `plugins/spec/skills/spec-explore/SKILL.md`
- Delete: `plugins/spec/skills/openspec-explore/SKILL.md`

**Steps:**
- [ ] Copy 304-line content from old skill
- [ ] Strip `openspec` CLI mentions; replace with "spec artifacts"
- [ ] Update path examples to `spec/changes/`
- [ ] Verify "stance, not workflow" section unchanged
- [ ] Delete old skill
- [ ] Commit

### Task 2.5: Modify `spec-review` skill

**Files:**
- Modify: `plugins/spec/skills/spec-review/SKILL.md`

**Steps:**
- [ ] Update Step 1 path resolution: `openspec/changes/` → `${MOR_SPEC_ROOT:-spec/changes}/`
- [ ] Update example output strings
- [ ] Smoke test variant detection still works
- [ ] Commit

### Task 2.6: Delete `spec-setup` skill

**Files:**
- Delete: `plugins/spec/skills/spec-setup/SKILL.md`

**Steps:**
- [ ] Delete file
- [ ] Verify nothing else references the skill (grep)
- [ ] Commit

---

## Phase 3: Commands rewrite

### Task 3.1: Rewrite command stubs

**Files:**
- Modify: `plugins/spec/commands/propose.md`
- Modify: `plugins/spec/commands/apply.md`
- Modify: `plugins/spec/commands/archive.md`
- Modify: `plugins/spec/commands/brainstorm.md`
- Modify: `plugins/spec/commands/review.md`
- Modify: `plugins/spec/commands/setup.md`

**Steps:**
- [ ] Update `propose.md`: invoke `spec-propose`
- [ ] Update `apply.md`: invoke `spec-apply`
- [ ] Update `archive.md`: invoke `spec-archive`
- [ ] Update `brainstorm.md`: invoke `spec-explore`
- [ ] Update `review.md`: change path mention
- [ ] Convert `setup.md` to deprecation notice: "Plugin self-contained — no setup required. Removed in v3."
- [ ] Verify all command frontmatter parses cleanly
- [ ] Commit

---

## Phase 4: Hook adjustments

### Task 4.1: `pre-tool-checklist-gate.sh`

**Files:**
- Modify: `plugins/spec/hooks/pre-tool-checklist-gate.sh`
- Create: `plugins/spec/tests/test-pre-tool-gate.sh`

**TDD steps:**
- [ ] Write `test-pre-tool-gate.sh` with 17 cases from Appendix B § 7
- [ ] Run tests — expect failure on path-related cases
- [ ] Update path: `openspec/changes` → `${MOR_SPEC_ROOT:-spec/changes}`
- [ ] Add marker check: `[[ -f "$CWD/spec/changes/.mor-spec" ]] || exit 0`
- [ ] Add dual-read mode: if `openspec/changes/` exists and `spec/changes/` doesn't, fall back with deprecation warning (1-version transition)
- [ ] Update skill matcher cases: include `spec:spec-apply`, drop `openspec-apply-change` after 1 version
- [ ] Run tests — expect 17/17 pass on both OS
- [ ] Commit

### Task 4.2: `session-start.sh`

**Files:**
- Modify: `plugins/spec/hooks/session-start.sh`
- Create: `plugins/spec/tests/test-session-start.sh`

**TDD steps:**
- [ ] Write 5 cases from Appendix B § 8
- [ ] Run tests — expect partial fail
- [ ] Add migration auto-prompt: detect `openspec/changes/` without `spec/changes/` → suggest `migrate-from-openspec.sh`
- [ ] Drop the old "schema not installed" suggestion
- [ ] Ensure non-blocking exit < 2s
- [ ] Run tests — expect 5/5 pass
- [ ] Commit

### Task 4.3: Modify `generate-checklist.sh`

**Files:**
- Modify: `plugins/spec/scripts/generate-checklist.sh`
- Create: `plugins/spec/tests/test-generate-checklist.sh`
- Create: `plugins/spec/tests/test-fetch-checklist.sh`

**TDD steps:**
- [ ] Write `test-generate-checklist.sh` (11 cases) and `test-fetch-checklist.sh` (8 cases) from Appendix B § 4 and § 5
- [ ] Update default path hint in usage text
- [ ] Confirm core logic unchanged (script already accepts arbitrary `<change-dir>`)
- [ ] Run tests — expect 19/19 pass on both OS
- [ ] Commit

---

## Phase 5: Migration tooling

### Task 5.1: `migrate-from-openspec.sh`

**Files:**
- Create: `plugins/spec/scripts/migrate-from-openspec.sh`
- Create: `plugins/spec/tests/test-migrate-from-openspec.sh`

**TDD steps:**
- [ ] Write 8 test cases from Appendix B § 6
- [ ] Implement: detect `openspec/changes/`, refuse if `spec/changes/` already exists, `mv` content + create `.mor-spec` marker, preserve archive subfolder
- [ ] Add `--dry-run` flag
- [ ] Add `--keep-openspec` flag (don't delete `openspec/` dir, only move `changes/`)
- [ ] Run tests — expect 8/8 pass
- [ ] Commit

---

## Phase 6: Documentation

### Task 6.1: Plugin README

**Files:**
- Modify: `plugins/spec/README.md` (rewrite)

**Steps:**
- [ ] Drop all OpenSpec mentions
- [ ] Add "Quickstart" section: install → `/spec:propose` → done
- [ ] Document `spec/changes/` convention + marker file
- [ ] Document `MOR_SPEC_ROOT` env override
- [ ] Add "Migrating from v1" section linking to `migrate-from-openspec.sh`
- [ ] Commit

### Task 6.2: Marketplace README

**Files:**
- Modify: `claude-plugins/README.md`

**Steps:**
- [ ] Update workflow diagram: drop `/spec:setup`
- [ ] Update commands table: remove `/spec:setup` row, update `/spec:propose` description
- [ ] Drop "Auto-suggestion" `openspec/.spec-setup-skip` mention
- [ ] Add v2 release notes section
- [ ] Commit

### Task 6.3: Plugin manifest version bump

**Files:**
- Modify: `plugins/spec/.claude-plugin/plugin.json`

**Steps:**
- [ ] Bump version to `2.0.0`
- [ ] Update description to reflect self-contained nature
- [ ] Commit

---

## Phase 7: CI + Release

### Task 7.1: CI workflow

**Files:**
- Create: `.github/workflows/spec-tests.yml`

**Steps:**
- [ ] Configure matrix: `os: [ubuntu-latest, macos-latest]`
- [ ] Run `plugins/spec/tests/run-all.sh`
- [ ] Run E2E test: `plugins/spec/tests/test-e2e.sh`
- [ ] Cache `npx` for performance (still used by superpowers plugin)
- [ ] Commit

### Task 7.2: Test aggregator + integration + E2E

**Files:**
- Create: `plugins/spec/tests/run-all.sh`
- Create: `plugins/spec/tests/integration/test-skill-flows.sh`
- Create: `plugins/spec/tests/test-e2e.sh`

**Steps:**
- [ ] Implement `run-all.sh`: glob `test-*.sh`, run each in subshell, aggregate exit + summary
- [ ] Implement `test-skill-flows.sh`: 6 integration scenarios from Appendix B § 9
- [ ] Implement `test-e2e.sh`: full lifecycle smoke (Appendix B § 10)
- [ ] All tests passing on CI matrix before release
- [ ] Commit

### Task 7.3: Release candidate

**Steps:**
- [ ] Tag `v2.0.0-rc.1` on a release branch
- [ ] Recruit 2–3 beta testers (internal Mor team)
- [ ] Run beta for 1 week minimum
- [ ] Collect feedback, fix critical issues
- [ ] Tag `v2.0.0` only after green RC

### Task 7.4: Release notes + migration guide

**Files:**
- Create: `claude-plugins/CHANGELOG.md` entry (or update existing)

**Steps:**
- [ ] Write breaking-change notice with migration steps
- [ ] Document `openspec/changes/` → `spec/changes/` migration
- [ ] Document `/spec:setup` deprecation
- [ ] Document `MOR_SPEC_ROOT` env override
- [ ] Document RSpec/Jasmine coexistence via `.mor-spec` marker
- [ ] Commit

---

## Sequencing & Dependencies

Strict order: **Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7**.

- Phase 0 unblocks all subsequent phases (decisions frozen).
- Phase 1 must complete before Phase 2 (skills depend on scripts).
- Phase 4 must follow Phase 2 (hook matchers reference new skill names).
- Phase 5 (migration) and Phase 6 (docs) can overlap.
- Phase 7 RC must run before stable tag.

**Effort total:** 15–18h realistic (buffer 25–30h). Phase 1 timeboxed: if scaffold engine exceeds 6h, re-evaluate scope.

---

## Appendix A — Risk Register

| ID | Risk | L×I | Post-mit | Mitigation summary |
|---|---|---|---|---|
| R1.1 | Bash cross-platform (macOS BSD vs Linux GNU) | 12 | 4 | `lib/common.sh` dual-stat helpers; CI matrix on both OS; avoid `find -printf`, `xargs -d`, `sort -V` |
| R1.2 | Schema regex misses edge cases | 12 | 6 | Rule spec; per-rule test pos+neg; `--explain` flag; future Python+jsonschema fallback |
| R1.3 | Concurrent scaffold race | 4 | 2 | `mkdir` atomic check; `flock` for archive |
| R1.4 | `.meta.json` corruption | 6 | 2 | Atomic `tmp+mv`; graceful skip in `list-changes.sh` |
| R1.5 | `${CLAUDE_PLUGIN_ROOT}` empty | 6 | 1 | Fallback derives from script location |
| R2.1 | Breaking change for OpenSpec users | 20 | 6 | Auto-prompt migration in `session-start.sh`; dual-read 1 version; major bump + release notes; `migrate-from-openspec.sh --dry-run` |
| R2.2 | `spec/` collides with RSpec/Jasmine | 12 | 4 | `.mor-spec` marker; `MOR_SPEC_ROOT` env; doc; auto-detect in tests |
| R2.3 | Lost OpenSpec dependency graph | 9 | 4 | `validate-tasks.sh` warns missing design.md; document gap as accepted |
| R2.4 | Lost `openspec list --json` for external tools | 4 | 1 | `list-changes.sh --json` schema-compatible |
| R2.5 | `/spec:setup` removal surprise | 8 | 1 | Keep as deprecation notice in v2; remove in v3 |
| R3.1 | Coupling with `superpowers` skill names | 8 | 3 | CI test matchers exist; document in `sync-superpowers.sh`; overlay enforces gate |
| R3.2 | Schema versioning without CLI | 6 | 2 | `.meta.json.schema_version`; rule files versioned |
| R3.3 | `spec/` folder name lock-in | 8 | 3 | `MOR_SPEC_ROOT` env; format_version in marker |
| R3.4 | Plugin bloat reinventing OpenSpec | 6 | 4 | Stay minimal; document scope; do not clone full OpenSpec |
| R4.1 | Test coverage insufficient | 16 | 5 | Bump effort 2h→6.5h; matrix tests; Appendix B coverage |
| R4.2 | Release rollout no canary | 12 | 3 | RC tag; 1-week beta; rollback via marketplace tag |
| R4.3 | Documentation gap | 6 | 1 | Migration FAQ; `/spec:doctor`; pin notice |
| R5.1 | Plan-review-gate paradox | 5 | 1 | Bootstrap via `openspec/changes/` for this plan only; migrate after Phase 7 |
| R5.2 | Effort blow-out | 12 | 6 | Phase 1 timeboxed; ship incrementally; communicate buffer |

**Top 3 priority actions:** R2.1 (migration end-to-end), R4.1 (test coverage 6.5h), R2.2 (`spec/` collision marker + env override).

---

## Appendix B — Test Coverage Matrix

98 cases across 12 test files, ~6.5h effort, CI matrix macOS + Ubuntu.

### § 1 — `test-scaffold-change.sh` (15 cases)
- P: 1.1 happy path; 1.2 `.meta.json` schema; 1.3 templates render
- N: 1.4 space in name; 1.5 uppercase; 1.6 leading digit; 1.7 empty; 1.8 reserved `archive`; 1.9 already exists
- E: 1.10 RSpec `spec/` coexistence; 1.11 `MOR_SPEC_ROOT` override; 1.12 `CLAUDE_PLUGIN_ROOT` fallback; 1.13 atomic creation; 1.14 macOS date; 1.15 Linux date

### § 2 — `test-list-changes.sh` (12 cases)
- P: 2.1 empty; 2.2 single; 2.3 multiple sort mtime desc; 2.4 active+archive split; 2.5 JSON vs text
- N: 2.6 no folder (no error); 2.7 missing meta (warn)
- E: 2.8 corrupt JSON; 2.9 1000 entries < 2s; 2.10 perm denied
- X: 2.11 macOS stat; 2.12 Linux stat

### § 3 — `test-validate-tasks.sh` (15 cases)
- P: 3.1 valid full; 3.2 valid minimal
- N: 3.3 R1 missing header; 3.4 R2 missing task; 3.5 R3 missing Files; 3.6 R4 no checkbox; 3.7 R5 < 3 checkboxes
- E: 3.8 partial done; 3.9 nested checkboxes; 3.10 CRLF; 3.11 unicode; 3.12 large file < 1s; 3.13 `--explain`; 3.14 `--rule` flag
- X: 3.15 BSD vs GNU grep regex

**Validation rules:**
- R1: header line `> **For agentic workers:** REQUIRED SUB-SKILL`
- R2: at least 1 line matching `^## Task \d+:`
- R3: every `## Task` block contains `**Files:**`
- R4: every `## Task` block contains ≥1 `- [ ]` or `- [x]`
- R5: total checkbox count ≥ 3
- R6: `.meta.json.schema_version` matches validator version

### § 4 — `test-generate-checklist.sh` (11 cases)
- P: 4.1 generate; 4.2 BE-Feature detect; 4.3 FE-BugFix detect; 4.4 variant override; 4.5 `--refresh`
- N: 4.6 bad path; 4.7 unreachable + no cache
- E: 4.8 stale cache fallback; 4.9 already approved confirmation; 4.10 env override
- X: 4.11 macOS vs Linux curl

### § 5 — `test-fetch-checklist.sh` (8 cases)
- P: 5.1 fresh fetch; 5.2 cache hit; 5.3 `--refresh` force
- N: 5.4 no network no cache
- E: 5.5 stale fallback; 5.6 HTML response sanity check
- X: 5.7 macOS mtime; 5.8 Linux mtime

### § 6 — `test-migrate-from-openspec.sh` (8 cases)
- P: 6.1 single change; 6.2 archive preserve; 6.3 empty no-op; 6.4 no openspec no-op
- N: 6.5 conflict refuse; 6.6 `--dry-run` no FS writes
- E: 6.7 symlink preserve; 6.8 perm denied

### § 7 — `test-pre-tool-gate.sh` (17 cases)
- P: 7.1 openspec-apply-change OK; 7.2 spec:spec-apply OK; 7.3 executing-plans OK
- N: 7.4 PENDING; 7.5 missing checklist
- E: 7.6 non-Skill tool fail-open; 7.7 unrelated skill; 7.8 no spec/changes; 7.9 no jq; 7.10 empty stdin; 7.11 malformed JSON; 7.12 multiple changes pick newest; 7.13 archive subfolder skip; 7.14 trailing whitespace; 7.15 no space `OK` (rule edge)
- X: 7.16 macOS stat; 7.17 Linux stat

### § 8 — `test-session-start.sh` (5 cases)
- P: 8.1 openspec residual prompt; 8.2 spec/changes quiet; 8.3 clean project quiet
- N: 8.4 timeout < 2s
- E: 8.5 RSpec coexistence quiet

### § 9 — `tests/integration/test-skill-flows.sh` (6 scenarios)
- 9.1 spec-propose creates 4 files; 9.2 spec-review variant override; 9.3 spec-apply pre-flight refuse; 9.4 spec-apply proceed + tick; 9.5 spec-archive move; 9.6 spec-explore read-only

### § 10 — `test-e2e.sh` (1 happy path + 1 migration)
Bootstrap → scaffold → list → validate → checklist → gate blocks → approve → gate allows → archive → migration smoke.

### Quality gates (must pass before merge)
- [ ] ≥80% logic branch coverage per script
- [ ] Every R1–R6 rule has positive + negative test
- [ ] Cross-platform branches verified on CI matrix
- [ ] `pre-tool-checklist-gate.sh` 100% scenario coverage
- [ ] `test-e2e.sh` clean pass
- [ ] Migration test on 3 fixture projects (active-only, mixed, archive-only)

---

## Appendix C — Open decisions deferred

These are explicit non-blockers for v2; revisit in v2.1 or later:
- **Python `jsonschema` fallback for `validate-tasks.sh`** — use when `python3` is available for stricter validation.
- **Schema rule versioning files** (`schemas/superpowers-driven/rules.v1.json`) — currently embedded in script; extract when v2 schema bump appears.
- **`/spec:doctor` command** — diagnose residual `openspec/`, conflict markers, env mismatch; planned for v2.1.
- **Drift detection for upstream `superpowers` skill renames** — extend `sync-superpowers.sh` test suite to grep for matcher list in gate; planned for v2.1.
- **GUI for review-checklist tick UX** — out of scope; CLI flip stays canonical.
