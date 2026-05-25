---
updated: <YYYY-MM-DD>
status: draft
source_files: [<glob-to-routes-or-controllers>]
---

# API Map

<!-- BOUNDARY: Endpoint index lives here. Full request/response schemas → ../../90-reference/REFERENCE.md.
     Auth & security rules → ../../20-design/00-core/ARCHITECTURE.md. -->
> This doc holds endpoint inventory, key query params, and error conventions.
> Full request/response schemas → [REFERENCE](../90-reference/REFERENCE.md).

---

## Endpoints

<!-- hint: group by resource/feature domain; one table per group -->

### <Resource Group A>
<!-- Example group: "User Management", "Orders", "Webhooks" -->

| Method | Path | Handler (→ file) | Purpose | Auth |
|---|---|---|---|---|
| GET | `/api/v1/<resource>` | `<HandlerClass>` (→ `<path/to/file>`) | <placeholder> | <JWT / API-key / none> |
| POST | `/api/v1/<resource>` | `<HandlerClass>` (→ `<path/to/file>`) | <placeholder> | <placeholder> |
| GET | `/api/v1/<resource>/:id` | `<HandlerClass>` (→ `<path/to/file>`) | <placeholder> | <placeholder> |
| PUT | `/api/v1/<resource>/:id` | `<HandlerClass>` (→ `<path/to/file>`) | <placeholder> | <placeholder> |
| DELETE | `/api/v1/<resource>/:id` | `<HandlerClass>` (→ `<path/to/file>`) | <placeholder> | <placeholder> |

### <Resource Group B>
<!-- hint: add more groups as needed; keep each table ≤ 10 rows, split if longer -->

| Method | Path | Handler (→ file) | Purpose | Auth |
|---|---|---|---|---|
| POST | `/api/v1/<resource>/export` | `<HandlerClass>` (→ `<path/to/file>`) | <placeholder> | <placeholder> |
| POST | `/webhooks/<event>` | `<HandlerClass>` (→ `<path/to/file>`) | <placeholder — incoming webhook> | <static-token / HMAC> |

---

## Request / Query Params

<!-- hint: add one subsection per endpoint that has non-trivial params -->

### `GET /api/v1/<resource>` — list/filter params

| Param | Type | Default | Notes |
|---|---|---|---|
| `page` | int | `1` | <placeholder> |
| `pageSize` | int | `20` | <placeholder — max allowed if any> |
| `<filter_param>` | string | null | <placeholder — describe filtering behavior> |
| `<date_param>` | string (ISO 8601) | null | <placeholder — parsing rules> |
| `<search_param>` | string | null | <placeholder — LIKE / full-text / exact> |

### `POST /api/v1/<resource>` — request body

<!-- hint: list required vs optional fields; reference schema anchor in REFERENCE.md for full shape -->
| Field | Type | Required | Notes |
|---|---|---|---|
| `<field>` | string | yes | <placeholder> |
| `<field_2>` | int | no | <placeholder — default if omitted> |

---

## Error / Status Conventions

<!-- hint: document project-wide conventions; add per-endpoint deviations as notes in the table above -->

| Scenario | HTTP Status | Response shape |
|---|---|---|
| Validation failure | 400 | `{ "error": "<message>" }` <!-- adjust to actual shape --> |
| Unauthenticated | 401 | <placeholder> |
| Forbidden (wrong tenant / role) | 403 | <placeholder> |
| Resource not found | 404 | <placeholder> |
| Unprocessable input | 422 | <placeholder> |
| Server error | 500 | <placeholder — masked in prod?> |

Additional conventions:
<!-- hint: note any known quirks, e.g. "some endpoints return 200 even on validation error" -->
- <placeholder — list deviations from standard REST conventions if any>
