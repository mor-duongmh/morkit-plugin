<!--
Design Guidelines Template — Principles + Patterns + ADRs (MADR-style)
Format: Markdown, hỗ trợ JP / EN / VN
Source: ProjectModel only (manual — no codebase scan).
Numbering: DPR-001 (DesignPrinciple), PTN-001 (PatternGuideline), ADR-001
-->

# Design Guidelines — {{PROJECT_NAME}}

| Field | Value |
|---|---|
| Project | {{PROJECT_NAME}} |
| Version | {{VERSION}} |
| Date | {{DATE}} |
| Standards | MADR (ADRs) |
| Language | {{LANG}} |

> This document is **manual** — there is no codebase sync. Add / edit
> entries in the ProjectModel JSON, then re-run `/morkit:init` (or
> `/morkit:update-doc`) to regenerate.

---

## 1. Design Principles

High-level principles the team agrees to follow.

| ID | Name | Statement |
|---|---|---|
| DPR-001 | _TBD_ | _TBD_ |

---

## 2. Patterns We Use / Avoid

| ID | Name | Category | When to Use | When to Avoid |
|---|---|---|---|---|
| PTN-001 | _TBD_ | arch | _TBD_ | _TBD_ |

---

## 3. Architecture Decision Records (ADRs)

ADRs follow the [MADR](https://adr.github.io/madr/) template. Each ADR
also gets a per-decision stub at `docs/adr/{id}-{slug}.md`.

### ADR-001: _TBD_

| Field | Value |
|---|---|
| Status | proposed |
| Date | {{DATE}} |

#### Context
_TBD_

#### Decision
_TBD_

#### Consequences
_TBD_

---

## 4. Anti-patterns

Patterns the team has explicitly chosen NOT to use.

- _TBD_

---

## 5. Review Checklist

Quick checklist for code reviewers.

- [ ] Follows the design principles in §1
- [ ] Uses an approved pattern from §2 (or justifies a new one in PR description)
- [ ] No anti-patterns from §4
- [ ] If introducing an architectural change → new ADR added in §3

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | {{DATE}} | morkit (auto) | Initial generation |
