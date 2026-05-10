# Design: Plugin `spec` Self-Contained — Frozen Decisions

> Companion doc to [`2026-05-10-spec-self-contained.md`](../plans/2026-05-10-spec-self-contained.md). This file captures **immutable decisions** made before implementation. Changes here = re-trigger plan-review-gate.

## Context

Plugin `spec@mor-duongmh` v1 requires per-project `/spec:setup` to install OpenSpec schema + run `npx openspec init`. This violates the principle "marketplace install once = ready in any project." v2 refactor removes the OpenSpec dependency entirely.

## Decisions

### D1 — Folder convention
Plugin owns folder `spec/changes/<name>/` (active) and `spec/changes/archive/<name>/` (archived). Marker file `spec/changes/.mor-spec` distinguishes plugin-owned `spec/` from RSpec/Jasmine test directories.

### D2 — Marker file
File: `spec/changes/.mor-spec`
Content (JSON):
```json
{ "format_version": 1, "plugin": "spec@mor-duongmh", "created_at": "<ISO 8601>" }
```
Hooks and scripts use marker presence to decide whether to act. Without marker, fail-open (plugin not in use).

### D3 — Env override
Single env var: `MOR_SPEC_ROOT` (default `spec/changes`). Honored by every script and the hook. Document in README + `--help`.

### D4 — Backward compatibility
**Hard cutover** with safety net:
- `migrate-from-openspec.sh` automated converter (idempotent, `--dry-run` supported).
- `pre-tool-checklist-gate.sh` v2 has 1-version dual-read mode: if `openspec/changes/` exists and `spec/changes/` doesn't, fall back with deprecation warning. Removed in v3.
- `session-start.sh` auto-prompts migration when residual `openspec/changes/` detected.

### D5 — Schema validation
Native bash regex over `tasks.md` against rules R1–R6:
- R1: header `> **For agentic workers:** REQUIRED SUB-SKILL`
- R2: at least one `^## Task \d+:`
- R3: every `## Task` block contains `**Files:**`
- R4: every `## Task` block contains ≥1 `- [ ]` or `- [x]`
- R5: total checkbox count ≥ 3
- R6: `.meta.json.schema_version` matches validator version

OpenSpec CLI (`schema validate`) is removed. Future Python `jsonschema` fallback deferred to v2.1.

### D6 — `/spec:setup` lifecycle
- v2: keep command, output deprecation notice "Plugin self-contained — no setup required. Removed in v3."
- v3: delete command + skill entirely.

### D7 — OpenSpec CLI removal
All `npx -y @fission-ai/openspec@latest` invocations removed from skills:
- `openspec new change` → `scaffold-change.sh`
- `openspec list` → `list-changes.sh`
- `openspec status / instructions` → direct read of `tasks.md`
- `openspec schema validate` → `validate-tasks.sh`
- `openspec archive` → `mv` to `archive/` subfolder

### D8 — Plugin version bump
v1.x → v2.0.0 (breaking change). Marketplace points to v2 stable after RC validation.

### D9 — Skill renaming
| Old (v1) | New (v2) |
|---|---|
| `openspec-propose` | `spec-propose` |
| `openspec-apply-change` | `spec-apply` |
| `openspec-archive-change` | `spec-archive` |
| `openspec-explore` | `spec-explore` |
| `spec-review` | `spec-review` (unchanged) |
| `spec-setup` | DELETED |

Hook matcher list updated to include both old + new names for 1 transition version.

### D10 — Test infrastructure
- Test runner: bash `run-all.sh` aggregator, glob `test-*.sh`, subshell isolation, summary report.
- CI matrix: `os: [ubuntu-latest, macos-latest]`.
- Coverage gates: ≥80% logic branch per script, every R1–R6 has positive + negative.
- Integration tests under `tests/integration/`.
- E2E smoke: `test-e2e.sh` exercises full lifecycle.

## Non-decisions (deferred to v2.1+)

- Python `jsonschema` validator fallback
- Schema rule version files (`schemas/superpowers-driven/rules.v1.json`)
- `/spec:doctor` diagnostic command
- Drift detection for upstream Superpowers skill renames
- GUI for review-checklist tick UX

## Sign-off

This doc is the contract. Implementation MUST adhere. Any divergence requires this doc to be updated first and the plan re-reviewed.
