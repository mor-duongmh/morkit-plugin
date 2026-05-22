---
updated: <YYYY-MM-DD>
status: draft
---

# Test Matrix

> This doc is where NFR/INV requirements are verified. For test run instructions see [TEST-RUNBOOK.md](TEST-RUNBOOK.md). For FR/NFR/INV definitions see [../../10-requirements/FEATURE-LIST.md](../../10-requirements/FEATURE-LIST.md) and [../../20-design/00-core/INVARIANTS.md](../../20-design/00-core/INVARIANTS.md).

---

<!-- hint: Ref column links back to FR-### / NFR-### from FEATURE-LIST or INV-### from INVARIANTS -->
<!-- hint: Status values: pass | fail | todo | skip -->
<!-- hint: add one row per distinct test case, not per feature -->

| Ref | Feature | Case | Expected Result | Status |
|---|---|---|---|---|
| FR-001 | <feature name> | <case, e.g. "happy path"> | <expected, e.g. "returns 200 with correct payload"> | todo |
| FR-001 | <feature name> | <case, e.g. "missing required field"> | <expected, e.g. "returns 400 with validation error"> | todo |
| NFR-001 | <non-functional, e.g. "Auth"> | <case, e.g. "unauthenticated request"> | <expected, e.g. "returns 401"> | todo |
| INV-001 | <invariant name> | <case, e.g. "action that would violate invariant"> | <expected, e.g. "rejected / no mutation occurs"> | todo |
| <placeholder> | <placeholder> | <placeholder> | <placeholder> | todo |
