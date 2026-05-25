---
updated: <YYYY-MM-DD>
status: draft
source_files: [<glob or path, e.g. "src/**/*.ts">]
---

# Source Map

> This doc holds the concern → file → symbol → keyword index.
> For business/feature scope see [SCOPE](SCOPE.md). For dependencies see
> [DEPENDENCY-MAP](DEPENDENCY-MAP.md).

## Concern → Source

<!-- hint: One row per architectural concern (route, controller, service, repo, UI, etc.). -->
<!-- hint: Files column: comma-separated paths or a directory glob. -->
<!-- hint: Responsibility column: one sentence — what this layer does, not how. -->

| Concern | Files | Responsibility |
|---|---|---|
| <placeholder: e.g. "Route config"> | `<path/to/routes.file>` | Defines URL routes and maps them to handlers |
| <placeholder: e.g. "Page controller"> | `<path/to/controller.file>` | Bootstraps the page and passes initial data to the frontend |
| <placeholder: e.g. "API controllers"> | `<path/to/api/controllers/>` | Thin HTTP handlers that delegate to application services |
| <placeholder: e.g. "Application services"> | `<path/to/services/>` | Orchestrate use-case logic and validate inputs |
| <placeholder: e.g. "Domain model"> | `<path/to/domain/>` | Entities, value objects, commands, and results |
| <placeholder: e.g. "Repository"> | `<path/to/repository.file>` | Reads and writes persistent data |
| <placeholder: e.g. "Frontend entry"> | `<path/to/main.ts>` | Creates and mounts the SPA |
| <placeholder: e.g. "Frontend router"> | `<path/to/router.ts>` | Defines client-side routes |

## Key Symbols

<!-- hint: List the most important entry-point symbols an agent would search for. -->
<!-- hint: Symbol = class method, function, or exported constant. -->
<!-- hint: One row per symbol; keep to the ~10 most load-bearing ones. -->

| Symbol | File | Purpose |
|---|---|---|
| `<ClassName::methodName>` | `<path/to/file>` | <placeholder: e.g. "Page entry point"> |
| `<ClassName::methodName>` | `<path/to/file>` | <placeholder: e.g. "Main list API handler"> |
| `<ClassName::methodName>` | `<path/to/file>` | <placeholder: e.g. "Core use-case orchestrator"> |
| `<ClassName::methodName>` | `<path/to/file>` | <placeholder: e.g. "Persists entity to DB"> |

## Code Search Keywords

<!-- hint: Grep-able strings that reliably locate this module's code. -->
<!-- hint: Include: module name variants, key table names, key class/function names. -->
<!-- hint: An agent uses these to find relevant files without reading the whole repo. -->

```text
<placeholder: module-name-kebab>
<placeholder: module_name_snake>
<placeholder: ModuleNamePascal>
<placeholder: KEY_TABLE_NAME>
<placeholder: key_setting_or_config_key>
<placeholder: AnotherDistinctiveSymbol>
```

## Source Boundaries

<!-- hint: Mirror SCOPE's boundaries but expressed as file/code ownership. -->
<!-- hint: Cross-link SCOPE instead of repeating business rules. -->
<!-- hint: See [SCOPE](SCOPE.md) for the business boundary these code rules enforce. -->

**This module owns:**

- <placeholder: e.g. "All files under `src/feature/` and `src/api/feature/`">
- <placeholder: e.g. "UI components scoped to this feature">

**This module depends on (does not own):**

- <placeholder: e.g. "Shared auth utilities in `src/shared/auth/`">
- <placeholder: e.g. "Records produced by `<other-module>`">

**This module must not own:**

- <placeholder: e.g. "Source rules for `<sibling-module>` — changes there break contracts here">
