---
updated: <YYYY-MM-DD>
status: draft
source_files: [<glob-to-frontend-src>]
---

<!-- OPTIONAL: This entire file is OPTIONAL. Skip for backend-only projects. -->
<!-- Create this file only when scout detects UI components / frontend app. -->

# UI Map

<!-- BOUNDARY: Component index and route→component wiring lives here.
     Design tokens / style rules → ../../00-core/ARCHITECTURE.md or a dedicated DESIGN-SYSTEM.md.
     API calls made by the UI → ../30-api/API-MAP.md. -->
> This doc maps app structure, routes, and key components.
> API endpoints called → [API-MAP](../30-api/API-MAP.md).

---

## App Structure

<!-- hint: list bootstrap / config files at the app root; omit every component file here -->

| File | Purpose |
|---|---|
| `<entry-file>` | <!-- e.g. main.ts / main.jsx --> App bootstrap, provider setup |
| `<root-component>` | <!-- e.g. App.vue / App.tsx --> Root shell, global layout |
| `<router-file>` | Route definitions |
| `<store-file>` | <!-- e.g. store/index.ts --> Global state (if any) |
| `<api-map-file>` | <!-- e.g. api/apiMap.js --> Central API endpoint constants |
| `<i18n-file>` | Internationalisation setup (if any) |

---

## Routes → Components

<!-- hint: one row per route; for nested routers add a sub-table or indent with group comment -->

| Route | Component (→ file) | Notes |
|---|---|---|
| `/` | `<RootLayout>` (→ `<path>`) | <!-- e.g. redirects to first menu item --> |
| `/<resource>` | `<ListPage>` (→ `<path>`) | <!-- main list / index view --> |
| `/<resource>/:id` | `<DetailPage>` (→ `<path>`) | <!-- detail / edit view --> |
| `/<settings>` | `<SettingsPage>` (→ `<path>`) | <placeholder> |

---

## Key Components

<!-- hint: only components with non-obvious responsibilities; skip simple presentational atoms -->

### <Feature Group A>
<!-- Example group: "List / Table", "Modals", "Forms" -->

| Component | Purpose |
|---|---|
| `<ComponentName>` (→ `<path>`) | <placeholder — what it fetches, manages, or orchestrates> |
| `<ComponentName2>` (→ `<path>`) | <placeholder> |

### <Feature Group B>

| Component | Purpose |
|---|---|
| `<ComponentName>` (→ `<path>`) | <placeholder> |

---

## UI Constraints / Gotchas

<!-- hint: things that bite developers; validation rules baked into UI, disabled states, render quirks -->
- <placeholder — e.g. "Filter modal only emits when all required fields are filled">
- <placeholder — e.g. "Date range: start date cannot be older than N days from today">
- <placeholder — e.g. "Export button disabled when list is empty (visual only — backend also guards)">
- <placeholder — e.g. "Component X renders user content with v-html / dangerouslySetInnerHTML — sanitise upstream">
- <placeholder — e.g. "Route params are synced to URL query string; page/pageSize are NOT persisted in URL">
