---
updated: <YYYY-MM-DD>
status: draft
---

# Test Strategy

> This doc defines WHAT and WHY to test. For HOW to run tests see [TEST-RUNBOOK.md](TEST-RUNBOOK.md). For per-requirement traceability see [TEST-MATRIX.md](TEST-MATRIX.md).

---

## Existing Coverage

<!-- hint: list test files found during scout; note which layers are covered (unit/integration/e2e) -->

Covered:

- `<path/to/existing/test-file>` — <!-- unit | integration | e2e -->
- `<path/to/existing/test-file>` — <!-- unit | integration | e2e -->

Gaps:

- No tests for `<controller | service | module>`.
- No frontend component tests found.

---

## Priority Test Areas

<!-- hint: rank by risk of data loss, security, or silent regression — not by feature size -->

| Area | Risk | Preferred Coverage |
|---|---|---|
| <area, e.g. "Access control on list endpoint"> | <risk, e.g. "Data leakage"> | <coverage, e.g. "Service test with allowed/denied ids"> |
| <placeholder> | <placeholder> | <placeholder> |

---

## Test Levels

<!-- hint: describe what belongs at each layer for this project; skip layers that do not apply -->

**Unit**
- Domain models, value objects, pure utility functions.
- Example scope: `<ModelName>`, `<UtilFunction>`.

**Integration**
- Service ↔ repository interactions; DB queries with test fixtures.
- Example scope: `<ServiceName>` + real (or in-memory) DB.

**End-to-end**
- Critical user journeys through the full stack.
- Example scope: `<JourneyName>` from UI → API → DB.

---

## Manual Test Focus

<!-- hint: steps a human should verify that are hard/slow to automate -->

- <scenario: e.g. "User with restricted access sees only permitted records.">
- <scenario: e.g. "Export result matches applied filters.">
- <scenario: e.g. "Partial form submission does not overwrite unsubmitted fields.">
