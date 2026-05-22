---
updated: <YYYY-MM-DD>
status: draft
source_files: [<glob-or-path-to-controllers-and-services>]
---

# Feature List

> This doc holds WHAT the system does (catalog of features + NFRs).
> For HOW each feature works see [20-design/10-features/](../20-design/10-features/).
> For user-facing flows see [USER-FLOWS.md](./USER-FLOWS.md).
> For NFR test coverage see [30-test/TEST-MATRIX.md](../30-test/TEST-MATRIX.md).

---

## Legend

### Status

| Value | Meaning |
|---|---|
| Active | Shipped and in use |
| Hidden | Code exists, UI entry point removed / commented |
| Planned | Scoped, not yet built |
| Legacy | Still live, marked for eventual removal |
| Deprecated | Disabled, kept only for migration |

### Priority (optional — omit column if not used)

| Value | Meaning |
|---|---|
| P0 | Must-have / blocking release |
| P1 | Important, ship in milestone |
| P2 | Nice-to-have, deferred |

---

## Actors / Roles

<!-- hint: list every human/system that directly triggers a feature -->

| Role | Description | Permissions |
|---|---|---|
| <placeholder: e.g. Admin> | <placeholder: description> | <placeholder: e.g. full read/write on X> |
| <placeholder: e.g. EndUser> | <placeholder: description> | <placeholder: e.g. read-only> |
| <placeholder: e.g. ExternalSystem> | <placeholder: description> | <placeholder: e.g. webhook POST only> |

---

## Functional Features

<!-- hint: one row per distinct user-facing or system feature; link Spec to the SYS-SPEC file -->
<!-- hint: Sources column → specific file/class names found by scout (feeds source_files front-matter) -->

| ID | Feature | Module / Area | Status | Actor | User Value | Spec | Sources |
|---|---|---|---|---|---|---|---|
| FR-001 | <placeholder: feature name> | <placeholder: module> | Active | <placeholder: role> | <placeholder: value sentence> | [SYS-SPEC](../20-design/10-features/<FEATURE>-SYS-SPEC.md) | `<Controller.php>`, `<Service.ts>` |
| FR-002 | <placeholder: feature name> | <placeholder: module> | Planned | <placeholder: role> | <placeholder: value sentence> | — | — |
| FR-003 | <placeholder: feature name> | <placeholder: module> | Legacy | <placeholder: role> | <placeholder: value sentence> | [SYS-SPEC](../20-design/10-features/<FEATURE>-SYS-SPEC.md) | `<LegacyController.php>` |

<!-- hint: add rows; keep "Hidden" features — they affect change impact analysis -->

---

## Non-Functional Requirements

<!-- hint: NFR-### IDs are global; TEST-MATRIX.Ref column points back to these -->

| ID | Category | Requirement | Verify → TEST-MATRIX |
|---|---|---|---|
| NFR-001 | <placeholder: e.g. Security> | <placeholder: rule, e.g. All write endpoints require authentication> | [TEST-MATRIX](../30-test/TEST-MATRIX.md#NFR-001) |
| NFR-002 | <placeholder: e.g. Performance> | <placeholder: rule, e.g. List API responds within 500 ms at P95> | [TEST-MATRIX](../30-test/TEST-MATRIX.md#NFR-002) |
| NFR-003 | <placeholder: e.g. Access Control> | <placeholder: rule> | [TEST-MATRIX](../30-test/TEST-MATRIX.md#NFR-003) |

---

## Feature Notes

<!-- hint: optional — use for small behaviors not worth a full SYS-SPEC yet -->
<!-- hint: remove this section once every note graduates to its own SYS-SPEC -->

- **<placeholder: feature or behavior>**: <placeholder: one-line note, e.g. "Redirect on root path → first visible menu item">
- **<placeholder: edge case>**: <placeholder: note>
