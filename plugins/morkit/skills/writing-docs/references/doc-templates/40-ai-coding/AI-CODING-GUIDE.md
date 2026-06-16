---
updated: <YYYY-MM-DD>
status: draft
---

# AI Coding Guide

> Meta-index for AI agents. This doc links; it does not duplicate. Entry points → [../../00-overview/SOURCE-MAP.md](../../00-overview/SOURCE-MAP.md). Do-not-break rules → [../../20-design/00-core/INVARIANTS.md](../../20-design/00-core/INVARIANTS.md). Read order → [../../00-overview/DOCUMENT-MAP.md](../../00-overview/DOCUMENT-MAP.md).

---

## Before Editing

Read in this order:

1. [../../00-overview/SOURCE-MAP.md](../../00-overview/SOURCE-MAP.md) — locate files for your task
2. [../../20-design/00-core/INVARIANTS.md](../../20-design/00-core/INVARIANTS.md) — constraints that must not break
3. Relevant feature spec in [../../20-design/10-features/](../../20-design/10-features/)
4. [../30-test/TEST-RUNBOOK.md](../30-test/TEST-RUNBOOK.md) — how to verify your change

---

## Safe Change Workflow

<!-- hint: keep steps generic — specific entry points live in SOURCE-MAP, not here -->

```text
1. Identify the change type (see COMMON-CHANGE-PLAYBOOKS.md for the matching playbook).
2. Locate affected files via SOURCE-MAP.md (concern → file → symbol).
3. Check INVARIANTS.md — confirm no invariant is violated.
4. Make the change; follow the playbook steps end-to-end.
5. Run tests per TEST-RUNBOOK.md (targeted, not full suite if slow).
6. Update affected docs (the playbook's last step names which doc).
```

Detailed per-change steps → [COMMON-CHANGE-PLAYBOOKS.md](COMMON-CHANGE-PLAYBOOKS.md)
Search recipes → [CODE-SEARCH-GUIDE.md](CODE-SEARCH-GUIDE.md)
Code-time pitfalls → [KNOWN-PITFALLS.md](KNOWN-PITFALLS.md)
System/business risks → [RISK-REGISTER.md](RISK-REGISTER.md)

---

## Notes For Agents

<!-- hint: project-specific gotchas an agent must keep in mind across ALL tasks -->

- <note, e.g. "Two systems coexist in the codebase — current (table A) and legacy (table B). Use current for new work.">
- <note, e.g. "Access-control must be enforced server-side; frontend filtering is cosmetic only.">
- <note, e.g. "Partial payload updates are intentional — do not overwrite absent fields with null.">
