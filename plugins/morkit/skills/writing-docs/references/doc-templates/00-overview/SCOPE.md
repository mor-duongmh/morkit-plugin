---
updated: <YYYY-MM-DD>
status: draft
---

# Scope

> This doc holds the business/feature boundary. For the code boundary see
> [SOURCE-MAP](SOURCE-MAP.md). For navigation see [DOCUMENT-MAP](DOCUMENT-MAP.md).

## In Scope

<!-- hint: Describe what this project/module is responsible for. Be explicit. -->
<!-- hint: List page routes, UI surfaces, API groups, data stores, and behaviors owned here. -->
<!-- hint: e.g. "Page route `/admin/users/*`", "CRUD for `users` table", "JWT auth flow" -->

<placeholder: project/module name> covers:

- <placeholder: e.g. "Page routes under `/feature/*`">
- <placeholder: e.g. "REST endpoints under `/api/v1/feature/`">
- <placeholder: e.g. "Read/write access to `<table_name>` table">
- <placeholder: e.g. "UI for managing X">

## Out Of Scope

<!-- hint: Be explicit about what this module does NOT handle. -->
<!-- hint: Name sibling modules or shared services that own those concerns instead. -->

- <placeholder: e.g. "Business rules that produce records consumed here">
- <placeholder: e.g. "Email template authoring owned by <other-module>">
- <placeholder: e.g. "Infrastructure/queue configuration beyond job reservation">

## Boundaries

<!-- hint: State what this module MUST own and MUST NOT own as hard rules. -->
<!-- hint: These become guardrails for AI agents making changes. -->

**Must own:**

- <placeholder: e.g. "All read/display logic for `<entity>`">
- <placeholder: e.g. "Validation of inputs entering `<service layer>`">

**Must NOT own:**

- <placeholder: e.g. "Decisions about when a <sibling module> triggers an action">
- <placeholder: e.g. "Schema changes to tables shared with <other-module>">

## Legacy / Deprecated Boundary

<!-- hint: Optional section. Include if there are routes/features marked for deletion. -->
<!-- hint: Keeping this section prevents agents from accidentally reviving deleted behavior. -->
<!-- hint: Remove this section entirely if no legacy boundary exists. -->

<placeholder: e.g. "Routes under `/api/v1/feature/legacy/*` are marked for deletion.
Keep docs so agents do not revive behavior without a product decision.">
