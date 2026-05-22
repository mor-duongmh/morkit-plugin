---
updated: <YYYY-MM-DD>
status: draft
---

# Reference

<!-- POINTER DOC — DO NOT duplicate content here.
     This file only points to authoritative sources and provides grep anchors.
     Summaries live in the MAP files: DATA-MAP / API-MAP / UI-MAP.
     If you find yourself pasting DDL, JSON schemas, or full class listings here — STOP and link instead. -->

> Pointer doc — no content is maintained here.
> Summaries → [DATA-MAP](../20-data/DATA-MAP.md) · [API-MAP](../30-api/API-MAP.md) · [UI-MAP](../40-ui/UI-MAP.md).

---

## Schema Sources

<!-- hint: list every file/folder that is the authoritative home of DB schema -->

- Schema DDL: `<path/to/schema.sql>` <!-- e.g. docker/mysql/data/schema.sql -->
- Migrations: `<path/to/migrations/>` <!-- e.g. db/migrations/ -->
- Seed / DML: `<path/to/seeds/>` <!-- e.g. db/seeds/ -->
- ORM models: `<glob>` <!-- e.g. src/models/**/*.ts -->

### Schema Anchors (grep strings)

| Item | Source Anchor (grep string) |
|---|---|
| `<table_name>` | `CREATE TABLE <table_name>` |
| `<table_name_2>` | `CREATE TABLE <table_name_2>` |
| `<enum_or_type>` | `CREATE TYPE <enum_or_type>` |
| `<migration_topic>` | `-- <migration_topic>` <!-- e.g. specific migration comment --> |

---

## API / Route Sources

<!-- hint: authoritative files for route registration and handler definitions -->

- Routes: `<path/to/routes>` <!-- e.g. app/Config/routes.php, src/routes/index.ts -->
- Controllers: `<glob>` <!-- e.g. src/controllers/**/*.ts -->
- OpenAPI spec (if any): `<path>` <!-- e.g. docs/openapi.yaml -->

### Route Anchors (grep strings)

| Item | Source Anchor (grep string) |
|---|---|
| `<route_group>` | `<grep-anchor>` <!-- e.g. "/api/v1/users" --> |
| `<handler_name>` | `<ClassName or function name>` |

---

## Frontend Sources

<!-- hint: only needed if project has a UI; delete section for backend-only projects -->

- Entry: `<path/to/main>` <!-- e.g. src/main.ts -->
- Router: `<path/to/router>` <!-- e.g. src/router/index.ts -->
- API map: `<path/to/apiMap>` <!-- e.g. src/api/apiMap.js -->
- Key components: `<glob>` <!-- e.g. src/components/**/*.vue -->

### Component Anchors (grep strings)

| Item | Source Anchor (grep string) |
|---|---|
| `<ComponentName>` | `<ComponentName>` |
| `<store_module>` | `<store-slice-name or Vuex module name>` |

---

## Other Source Anchors

<!-- hint: add any domain-specific grep targets that don't fit above categories -->

| Item | Source Anchor (grep string) |
|---|---|
| `<constant_or_enum>` | `<CONSTANT_NAME>` |
| `<config_key>` | `<config_key_string>` |
