---
updated: <YYYY-MM-DD>
status: draft
---

# User Flows

> This doc holds user-facing interaction flows (WHAT the user does + system response).
> For technical sequences (controller → service → DB) see each feature's SYS-SPEC in
> [20-design/10-features/](../20-design/10-features/).
> For feature IDs and actors see [FEATURE-LIST.md](./FEATURE-LIST.md).

---

## Flow Index

<!-- hint: one row per feature that has a user-facing flow -->
<!-- hint: for small projects, skip the index and write flows as sections directly below -->

| Feature | Flow file |
|---|---|
| FR-001 · <placeholder: feature name> | [flows/FR-001-<slug>.md](./flows/FR-001-<slug>.md) |
| FR-002 · <placeholder: feature name> | [flows/FR-002-<slug>.md](./flows/FR-002-<slug>.md) |
| FR-003 · <placeholder: feature name> | — (inline below) |

---

## Inline Flows (small project option)

<!-- hint: use this section ONLY when the project has ≤ 4 simple flows -->
<!-- hint: remove this section and use the index + separate flow files for larger projects -->

### FR-NNN · <placeholder: Feature Name>

```text
<placeholder: Actor> does <action>
-> <placeholder: system step>
-> <placeholder: system step>
-> <placeholder: outcome / screen shown>
```

<!-- example (delete before use):
```text
Admin opens /history page
-> UI requests GET /api/v1/items
-> Backend validates session
-> UI renders paginated list
```
-->
