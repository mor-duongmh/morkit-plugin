---
updated: <YYYY-MM-DD>
status: draft
---

# Architecture — <placeholder: Project / Module Name>

> arc42-lite (8 sections). Deployment view → [90-operations/](../../90-operations/).
> For invariants see [INVARIANTS.md](./INVARIANTS.md).
> For feature specs see [../10-features/](../10-features/).

---

## 1. Introduction & Goals

<placeholder: 2–3 sentences describing the system's purpose and primary capability>

### Quality Goals

<!-- hint: list 3–5 top quality goals; order by priority -->

| ID | Goal | Priority | Description |
|---|---|---|---|
| QG-001 | <placeholder: e.g. Security> | High | <placeholder: e.g. All data mutations require authenticated session> |
| QG-002 | <placeholder: e.g. Reliability> | High | <placeholder: e.g. Async jobs must not block request threads> |
| QG-003 | <placeholder: e.g. Maintainability> | Mid | <placeholder: e.g. Controllers are thin; business logic lives in services> |

### Stakeholders

| Role | Concern |
|---|---|
| <placeholder: e.g. Admin user> | <placeholder: e.g. Correct data, access control enforced> |
| <placeholder: e.g. Developer> | <placeholder: e.g. Clear seam between layers, testable services> |
| <placeholder: e.g. Ops team> | <placeholder: e.g. Observable errors, async jobs don't pile up> |

---

## 2. Constraints

| Type | Constraint | Rationale |
|---|---|---|
| Technical | <placeholder: e.g. Must run on PHP 8.x / Node 20 / Python 3.11> | <placeholder: existing infra> |
| Technical | <placeholder: e.g. No new global state in controllers> | <placeholder: testability> |
| Organizational | <placeholder: e.g. No breaking API changes without versioning> | <placeholder: downstream consumers> |

---

## 3. Context & Scope

<!-- hint: list external actors and systems; details of each interface → 30-api/API-MAP.md -->

```text
<placeholder: External actor / system>  -->  [<placeholder: entry point>]  <placeholder: system boundary>
<placeholder: External actor / system>  -->  [<placeholder: entry point>]
[<placeholder: system boundary>]  -->  <placeholder: external data store / service>
```

<!-- example (delete before use):
```text
Browser (Admin)  -->  [Vue SPA]  [API Layer]
External mailer  -->  [Webhook endpoint]
[API Layer]      -->  PostgreSQL · Redis · S3
```
-->

---

## 4. Solution Strategy

<!-- hint: top-level technology and pattern choices; deep rationale → ADR/ -->

- **Tech stack**: <placeholder: e.g. Vue 2 + PHP (CakePHP) / React + Node / Django + React>
- **Layer pattern**: <placeholder: e.g. Controller → Application Service → Repository; thin controllers>
- **Async strategy**: <placeholder: e.g. Heavy work reserved as BatchManagement jobs; no sync heavy processing>
- **Auth approach**: <placeholder: e.g. Session-based / JWT / API token; see INVARIANTS § Access Control>

<!-- optional (web projects only) — delete section if not applicable:
- **Frontend routing**: <placeholder: client-side SPA router / SSR / file-based routing>
- **API contract**: <placeholder: REST / GraphQL / tRPC; versioning strategy>
-->

---

## 5. Building Block View

<!-- hint: CMP-### IDs used by Runtime View; keep list short — major components only -->

### Components

| ID | Name | Kind | Tech | Depends on |
|---|---|---|---|---|
| CMP-001 | <placeholder: e.g. Frontend SPA> | UI | <placeholder: e.g. Vue 2 / React> | CMP-002 |
| CMP-002 | <placeholder: e.g. API Controllers> | Controller | <placeholder: e.g. PHP / Express> | CMP-003 |
| CMP-003 | <placeholder: e.g. Application Services> | Service | <placeholder: e.g. PHP / TypeScript> | CMP-004 |
| CMP-004 | <placeholder: e.g. Repositories> | Repository | <placeholder: e.g. ORM / raw SQL> | CMP-005 |
| CMP-005 | <placeholder: e.g. Database> | Datastore | <placeholder: e.g. PostgreSQL / MySQL> | — |

### Layers

| ID | Name | Components |
|---|---|---|
| LAY-001 | Presentation | CMP-001 |
| LAY-002 | API / Controller | CMP-002 |
| LAY-003 | Application / Domain | CMP-003 |
| LAY-004 | Infrastructure | CMP-004, CMP-005 |

---

## 6. Runtime View

<!-- hint: cover the 2–3 most important flows; full per-feature sequences → SYS-SPEC -->

```text
<placeholder: Actor> triggers <placeholder: action>
-> CMP-001 calls CMP-002 via <placeholder: HTTP GET /api/v1/...>
-> CMP-002 validates input, builds command
-> CMP-003 applies business rules, queries CMP-004
-> CMP-004 reads CMP-005
-> result propagates back to CMP-001
```

<!-- example (delete before use):
```text
Admin opens list page
-> CMP-001 calls GET /api/v1/items (CMP-002)
-> CMP-002 builds ListCommand, calls CMP-003
-> CMP-003 checks access control, calls CMP-004
-> CMP-004 queries pp_items in CMP-005
-> paginated result returned to CMP-001
```
-->

---

## 7. Crosscutting Concepts

<!-- hint: rules that apply across ALL components; enforcement details → INVARIANTS.md -->

- **Authentication / Access Control**: <placeholder: e.g. Session cookie validated by middleware; module-level ACL in service layer. See [INVARIANTS.md](./INVARIANTS.md) § Access Control>
- **Error handling**: <placeholder: e.g. Controllers catch service exceptions and return structured JSON error responses>
- **Async / Background jobs**: <placeholder: e.g. Heavy operations enqueued as jobs; controllers return job ID immediately>
- **Logging / Observability**: <placeholder: e.g. Structured logs in JSON; errors include request ID>
- **Configuration & Secrets**: <placeholder: e.g. Environment variables only; no secrets in source>

<!-- optional (web projects only):
- **Frontend routing**: <placeholder: base path, redirect rules, hidden routes>
- **API versioning**: <placeholder: e.g. /api/v1/ prefix; breaking changes increment version>
-->
