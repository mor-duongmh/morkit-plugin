---
updated: <YYYY-MM-DD>
status: draft
---

# Dependency Map

> This doc holds dependency listings. Schema details live in
> [DATA-MAP](../20-design/20-data/DATA-MAP.md) (if generated). For code ownership see
> [SOURCE-MAP](SOURCE-MAP.md).

## Internal Dependencies

<!-- hint: Dependencies on other modules, shared libraries, or utilities inside this repo. -->
<!-- hint: Direction: "X depends on Y" → row is X, direction is "depends on". -->
<!-- hint: e.g. "Feature service depends on shared UserContext for auth-aware queries." -->

| Dependency | Direction | Purpose |
|---|---|---|
| `<placeholder: shared store / context>` | `<this module>` depends on | <placeholder: e.g. "Provides authenticated user identity"> |
| `<placeholder: shared layout component>` | `<this module>` depends on | <placeholder: e.g. "Shell layout and navigation chrome"> |
| `<placeholder: shared repository>` | Service depends on | <placeholder: e.g. "Persists settings shared across modules"> |
| `<placeholder: domain value object>` | Infrastructure depends on | <placeholder: e.g. "Maps type keys to module IDs"> |

## External Dependencies

<!-- hint: Third-party libraries, SaaS services, or external APIs this module calls. -->
<!-- hint: Include version only if a specific version matters for behavior. -->

| Dependency | Type | Purpose |
|---|---|---|
| `<placeholder: e.g. axios>` | npm library | <placeholder: e.g. "HTTP client for API calls"> |
| `<placeholder: e.g. AWS SQS>` | cloud service | <placeholder: e.g. "Async job queue for export tasks"> |
| `<placeholder: e.g. SendGrid>` | external API | <placeholder: e.g. "Transactional email delivery"> |

<!-- hint: Remove this section if the module has no meaningful external dependencies. -->

## Data Dependencies

<!-- hint: List data stores (tables, collections, caches, buckets) this module reads or writes. -->
<!-- hint: Do NOT put schema details here — cross-link DATA-MAP instead. -->
<!-- hint: e.g. "users table — read for auth lookups" -->

| Store | Use |
|---|---|
| `<placeholder: table_or_collection_name>` | <placeholder: e.g. "Primary read/write store for this feature"> |
| `<placeholder: table_or_collection_name>` | <placeholder: e.g. "Read-only: module label metadata"> |
| `<placeholder: table_or_collection_name>` | <placeholder: e.g. "Write: async job reservation"> |
| `<placeholder: settings_store>` | <placeholder: e.g. "Tenant-level configuration persistence"> |

<!-- hint: For full schema see [DATA-MAP](../20-design/20-data/DATA-MAP.md). -->

## Cross-Module Dependencies

<!-- hint: Describe producer/consumer relationships across module boundaries. -->
<!-- hint: Name the modules and the shared artifact (table, event, contract). -->
<!-- hint: End with a "When adding X, update Y too" instruction — this guides AI agents. -->

<placeholder: e.g. "Records in `<table>` are produced by modules such as
`<module-a>`, `<module-b>`, and `<module-c>` via shared services.
This module reads those records but does not produce them.">

When adding a new <placeholder: e.g. "producing module">, update both:

- `<placeholder: e.g. "src/shared/TypeKey.ts — add the new type key">` 
- `<placeholder: e.g. "`<lookup_table>` DML and localized labels">`
