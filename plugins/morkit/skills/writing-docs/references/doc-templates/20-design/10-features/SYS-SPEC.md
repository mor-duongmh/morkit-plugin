---
updated: <YYYY-MM-DD>
status: active
feature: FR-<NNN>
source_files: [<glob-or-specific-files-for-this-feature>]
---

# <placeholder: Feature Name> — System Specification

> This doc holds the technical HOW for FR-<NNN>.
> For user-facing flow see [10-requirements/flows/FR-NNN-<slug>.md](../../10-requirements/flows/FR-NNN-<slug>.md).
> For invariants that apply here see [00-core/INVARIANTS.md](../00-core/INVARIANTS.md).
> For data shapes see [20-data/DATA-MAP.md](../20-data/DATA-MAP.md).

---

## Purpose

<placeholder: 2–3 sentences — what this feature does and why it exists>

---

## Source Anchors

<!-- hint: list every file that implements this feature; used for future sync/update mode -->

| Layer | Source |
|---|---|
| UI component | `<placeholder: path/to/Component.vue or Page.tsx>` |
| API client | `<placeholder: path/to/apiMap.js or api-client.ts>` |
| Controller | `<placeholder: path/to/FeatureController.php or route-handler.ts>` |
| Application service | `<placeholder: path/to/FeatureApplicationService.php or feature-service.ts>` |
| Repository / query | `<placeholder: path/to/FeatureRepository.php or feature-repo.ts>` |
| Domain model | `<placeholder: path/to/FeatureModel.php or feature.entity.ts>` |

---

## Behavior / Flow

<!-- hint: technical sequence — controller → service → repo → DB; not user-facing (that's in flows/) -->

```text
<placeholder: entrypoint, e.g. FeatureController.handle()>
-> <placeholder: build command object from request params>
-> <placeholder: ApplicationService validates access / business rules>
-> <placeholder: Repository queries / mutates DB>
-> <placeholder: result object assembled>
-> <placeholder: JSON response returned to client>
```

<!-- example (delete before use):
```text
ItemListController.index()
-> build ListItemsCommand from query params
-> ItemListApplicationService checks module access (INV-002)
-> ItemRepository.findItems() queries pp_items WHERE status != SKIP (INV-010)
-> ItemListResult.toArray() serialized as JSON
```
-->

---

## Business Rules

<!-- hint: BR-### IDs are local to this file only — not globally unique across SYS-SPECs -->

| ID | Rule |
|---|---|
| BR-001 | <placeholder: rule, e.g. If moduleId is provided it must be in the user's visible module set> |
| BR-002 | <placeholder: rule, e.g. Results ordered by created_at DESC> |
| BR-003 | <placeholder: rule, e.g. Date filter requires both date and time to be supplied as a pair> |

---

## Change Impact

<!-- hint: checklist of what to verify when this feature is modified -->

When changing this feature, check:

- <placeholder: e.g. API client parameter names in `apiMap.js`>
- <placeholder: e.g. Command object setters / getters>
- <placeholder: e.g. Repository query conditions and sort order>
- <placeholder: e.g. Result / DTO serialization shape consumed by UI>
- <placeholder: e.g. Related features that mirror these filters (e.g. export)>
- <placeholder: e.g. Access-control filtering in service layer>

---

<!-- OPTIONAL SECTIONS — uncomment and fill only when applicable; remove comment markers when used -->

<!--
## Filters / Inputs

<!-- hint: optional — include when feature has non-trivial filter/input mapping -->

| UI Field | Query Param / Body Key | Backend Setter | Notes |
|---|---|---|---|
| <placeholder: UI label> | `<placeholder: param>` | `<placeholder: setter>` | <placeholder: validation note> |

-->

<!--
## Data Shapes

<!-- hint: optional — include when shape is complex or not obvious from DATA-MAP -->

Request body / query params:
```json
{
  "<placeholder: field>": "<placeholder: type and description>"
}
```

Response item shape:
```json
{
  "<placeholder: field>": "<placeholder: type and description>"
}
```

-->

<!--
## Response / Output Contract

<!-- hint: optional — include when UI depends on specific field names or types -->

| Field | Type | Usage |
|---|---|---|
| `<placeholder: field>` | `<placeholder: type>` | <placeholder: how UI uses it> |

-->

<!--
## Known Issues / Source Mismatch

<!-- hint: optional — document discrepancies between spec and actual source -->
<!-- hint: link pitfalls to 40-ai-coding/KNOWN-PITFALLS.md — do not duplicate -->

- <placeholder: e.g. Controller returns `stepId` but UI renders with `:key="item.id"` — verify before editing row identity>
  See: [40-ai-coding/KNOWN-PITFALLS.md](../../40-ai-coding/KNOWN-PITFALLS.md)

-->

<!--
## Status & Deprecation Note

<!-- hint: optional — include only for Legacy or Planned features (status != active) -->

**Status**: <placeholder: Legacy | Planned>

<placeholder: context — e.g. "Routes marked 削除予定; do not use as baseline for new work. Callers must be confirmed before removal.">

See invariant [INV-050](../00-core/INVARIANTS.md).

-->
