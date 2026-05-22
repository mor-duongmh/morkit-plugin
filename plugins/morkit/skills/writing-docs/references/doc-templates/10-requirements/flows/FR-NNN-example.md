---
updated: <YYYY-MM-DD>
status: draft
feature: FR-<NNN>
---

# Flow: <placeholder: Feature Name>

> This doc holds the user-facing flow for FR-<NNN>.
> For technical sequence (controller → service → DB) see
> [20-design/10-features/<FEATURE>-SYS-SPEC.md](../../20-design/10-features/<FEATURE>-SYS-SPEC.md).
> Feature definition: [FEATURE-LIST.md](../FEATURE-LIST.md#FR-NNN).

---

## Happy Path

<!-- hint: use plain text + arrows; no Mermaid -->
<!-- hint: start with the actor action; end with the observable outcome -->

```text
<placeholder: Actor> <placeholder: action, e.g. opens /some-route>
-> <placeholder: UI/system step>
-> <placeholder: API call or internal step>
-> <placeholder: backend validates / processes>
-> <placeholder: response / outcome shown to user>
```

<!-- example (delete before use):
```text
Admin opens /items page
-> UI calls GET /api/v1/items with current filter params
-> Backend validates session and access scope
-> Backend returns paginated item list
-> UI renders table with status, date, and action buttons
```
-->

---

## Alternate / Error Paths

<!-- hint: list meaningful deviations; skip trivial HTTP errors unless they affect UX -->

| Condition | Path |
|---|---|
| <placeholder: e.g. Session expired> | <placeholder: e.g. Backend returns 401 → UI redirects to login> |
| <placeholder: e.g. Validation fails> | <placeholder: e.g. UI shows inline error; no API call made> |
| <placeholder: e.g. Resource not found> | <placeholder: e.g. Backend returns 404 → UI shows empty state> |

---

## Touchpoints

<!-- hint: link to the canonical doc for each touchpoint type; do not duplicate content here -->

| Type | Name | Reference |
|---|---|---|
| UI screen | <placeholder: ScreenName.vue / PageComponent> | [UI-MAP](../../20-design/40-ui/UI-MAP.md) |
| API endpoint | <placeholder: e.g. GET /api/v1/items> | [API-MAP](../../20-design/30-api/API-MAP.md) |
| DB table | <placeholder: e.g. pp_items> | [DATA-MAP](../../20-design/20-data/DATA-MAP.md) |
