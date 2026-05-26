# Anchor Conventions

How docs become "anchors" an AI agent can latch onto, decomposed and linked so the agent loads minimal context per task.

## The 4 anchor mechanisms

| Mechanism | Role | Usage |
|---|---|---|
| **MAP files** | Index/navigation: agent reads a MAP first to know which files to load | Primary. DOCUMENT-MAP (read paths), SOURCE-MAP (concern→file→symbol→keyword), DESIGN-MAP, DATA/API/UI-MAP |
| **Cross-links** | Relative-path links between docs + read-path sequences | Primary. Every doc links related docs instead of duplicating |
| **Front-matter** | Lightweight machine-readable metadata; lays groundwork for `update` mode | Minimal — see below |
| **IDs** | Stable grep-able codes for cross-reference | Selective — see ID policy |

> The reference example used only MAP + cross-links + keyword tables (0 front-matter, 0 IDs) and was already clean. Keep front-matter and IDs **minimal** — add only where they earn their keep.

## Front-matter (minimal)

```yaml
---
updated: <YYYY-MM-DD>
status: draft | stable | planned | drift
source_files: [<path or glob>]   # only where the doc maps to specific code
---
```
- `status` values: `draft`/`stable` (normal lifecycle) · `planned` (intent seeded ahead of code, e.g. greenfield ARCHITECTURE) · `drift` (a bridged spec claim with no code evidence yet — flagged by `docs update` for review).
- `source_files` is the seed for future `update`/sync — include it on docs derived from code (SOURCE-MAP, SYS-SPEC, DATA-MAP, API-MAP, UI-MAP, FEATURE-LIST). Omit it on seeded greenfield docs (no code yet).
- Omit `source_files` where it has no meaning (GLOSSARY, DOCUMENT-MAP).
- Do NOT add `owner`/`related` unless the project asks — keep it to these 3 fields.

## ID policy + traceability loop

Enable IDs only at these anchors:
- `FR-###` / `NFR-###` → `10-requirements/FEATURE-LIST.md`
- `INV-###` → `20-design/00-core/INVARIANTS.md`
- `BR-###` → local per `*-SYS-SPEC.md` (scoped to that file, not global)

Traceability (close the loop):
```
FR-### (FEATURE-LIST) -> *-SYS-SPEC (per feature) -> BR-### (rules in that spec)
NFR-### (FEATURE-LIST) + INV-### (INVARIANTS) -> TEST-MATRIX.Ref (verified by)
```
TEST-MATRIX has a `Ref` column pointing back to FR/NFR/INV codes.

## DRY boundary rule (every doc)

Each doc opens with a one-line boundary + cross-link:
```
> This doc holds X. For Y see [other-doc](relative/path).
```
One fact lives in one place; everywhere else links to it. Known overlaps and their owners:
- business/scope boundary → SCOPE; code boundary → SOURCE-MAP (cross-link, don't repeat)
- data dependency list → DEPENDENCY-MAP; schema detail → DATA-MAP
- "when you change X": code→SYS-SPEC/Change-Impact · tests→TEST-RUNBOOK · e2e process→COMMON-CHANGE-PLAYBOOKS
- known bug in source → KNOWN-PITFALLS (SYS-SPEC/Known-Issues links to it)
- entry-points/do-not-break → SOURCE-MAP/INVARIANTS (AI-CODING-GUIDE links, doesn't copy)
- read order / source locations → DOCUMENT-MAP (README root links, stays thin)

## Flows

Use `text` + arrows, not Mermaid (agent can grep, no render needed):
```text
Actor does X
-> system step
-> ...
```

## Pointer docs (`*-REFERENCE`)

`90-reference/*-REFERENCE.md` must NOT duplicate content. They point to source + give a grep anchor string. Stay stale-proof:
```
| Item | Source Anchor (grep string) |
| pp_users | `CREATE TABLE pp_users` |
```

## File naming

- Folders: numbered prefix (`00-`, `10-`, …) for ordering.
- MAP/anchor docs: `UPPER-KEBAB` (DOCUMENT-MAP, SOURCE-MAP, FEATURE-LIST).
- Feature specs: `<FEATURE>-SYS-SPEC.md`. ADRs: `NNN-slug.md`. Flows: `flows/FR-NNN-<slug>.md`.
