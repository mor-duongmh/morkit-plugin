# Taxonomy

Defines the `docs/` folder taxonomy, what each group holds, and when to create each folder.

## Core groups (always created)

| Group | Role |
|---|---|
| `00-overview/` | Entry docs: navigation map, scope, source map, dependency map, glossary, tech stack |
| `10-requirements/` | Feature catalog (WHAT) + user-facing flows |
| `20-design/` | Architecture, invariants, per-feature specs (HOW), data/API/UI maps, ADRs |
| `30-test/` | Test strategy, runbook, traceability matrix |
| `40-ai-coding/` | Guides optimized for AI agents: coding guide, search recipes, change playbooks, pitfalls, risks, code standards |
| `90-operations/` | Local runbook + troubleshooting |

## 20-design sub-taxonomy

| Sub-folder | Tier | Create when |
|---|---|---|
| `00-core/` | core | always — ARCHITECTURE (arc42-lite), INVARIANTS |
| `10-features/` | core | always — one `*-SYS-SPEC.md` per feature (incl. cross-cutting: batch/webhook/integration, use `status`/tag) |
| `20-data/` | conditional | project has a DB / data store / ORM / migrations → DATA-MAP |
| `30-api/` | conditional | project exposes API / endpoints → API-MAP |
| `40-ui/` | conditional | project has a UI / frontend → UI-MAP |
| `ADR/` | conditional | there are deliberate architecture decisions worth recording → `NNN-slug.md` (MADR) |
| `90-reference/` | optional | deep-dive reference needed → `*-REFERENCE.md` (pointer docs, never duplicate content) |

## File tiers (apply throughout)

- **core** — always generate (every project).
- **conditional** — generate only when scout finds the matching component. No empty folders.
- **optional** — generate only on explicit signal/request.

## Conditional detection (scout signals → folder)

| Signal found by scout | Create |
|---|---|
| schema / migrations / ORM models | `20-design/20-data/DATA-MAP` |
| routes / controllers / API handlers | `20-design/30-api/API-MAP` |
| UI components / frontend app | `20-design/40-ui/UI-MAP` |
| lint / format / commit convention config | `40-ai-coding/CODE-STANDARDS` |
| package manifest (deps, scripts) | `00-overview/STACK` |

## Extension folders (optional, only on signal/request)

`00-review` · `50-migration` · `60-security` · `70-performance` · `80-release`.
The skill knows these but does NOT scaffold them by default.

## Scale: project-level vs per-module

The reference example (`references/example/mail-history-admin/`) is **module-scoped**. The skill supports both:

- **project-level** — one taxonomy under `docs/`. Each module/feature is a `*-SYS-SPEC` in `20-design/10-features/`.
- **per-module** — each module gets its own taxonomy (e.g. `docs/m/<module>/00-overview/…`). Fits monorepos / large multi-module apps.

**ALWAYS ask the user** which scale (AskUserQuestion) unless `--scope project|module` is passed. Monorepo markers (`pnpm-workspace.yaml`, `packages/*`, `apps/*`, `go.work`, lerna) are hints to surface in the question, not an auto-decision.

## File size

Target ~100 LOC per file (like the reference example). Hard cap 800 LOC → split into sub-files and link from the group's MAP/README.
