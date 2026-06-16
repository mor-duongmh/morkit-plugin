---
updated: <YYYY-MM-DD>
status: draft
---

# Invariants

> This doc holds rules that MUST NOT be broken by any code change.
> Verification for each INV-### is in [30-test/TEST-MATRIX.md](../../30-test/TEST-MATRIX.md).
> For per-feature business rules (BR-###) see each [SYS-SPEC](../10-features/).

---

## Access Control

<!-- hint: rules about who may read/write what; tie to NFR-### in FEATURE-LIST if applicable -->

- INV-001: <placeholder: rule, e.g. Every write endpoint must reject unauthenticated requests before any data mutation>  *(why: prevent unauthorized state changes)*
- INV-002: <placeholder: rule, e.g. Module-level access is enforced in the service layer, not only in the UI>  *(why: UI filtering alone is bypassable)*

---

## Data Integrity

<!-- hint: rules about data shape, mapping, and consistency guarantees -->

- INV-010: <placeholder: rule, e.g. Records with status=SKIP must be excluded from all public list queries>  *(why: SKIP rows are internal bookkeeping, not user-visible history)*
- INV-011: <placeholder: rule, e.g. Foreign key X must resolve to a row in table Y before insert>  *(source: `<MigrationFile>`)*
- INV-012: <placeholder: rule, e.g. Enum value Z must map to a known constant in the domain model>  *(why: unmapped values cause silent rendering errors)*

---

## Async / Background Jobs

<!-- hint: rules about what must NOT happen synchronously -->

- INV-020: <placeholder: rule, e.g. Heavy export/processing work must be enqueued as a background job; never run inline in the HTTP request>  *(why: request timeout + resource exhaustion)*
- INV-021: <placeholder: rule, e.g. Job reservation must succeed before the API returns 200; partial state is not acceptable>

---

## External Integrations

<!-- hint: rules about webhooks, third-party calls, or inbound events -->

- INV-030: <placeholder: rule, e.g. Webhook endpoint must validate authorization header before parsing or mutating any data>  *(why: untrusted input; source: `<WebhookController>`)*
- INV-031: <placeholder: rule, e.g. Bounce update must only apply when sent_at <= event_at to avoid updating unsent records>

---

## Settings / Configuration

<!-- hint: rules about tenant/app-level settings persistence and defaults -->

- INV-040: <placeholder: rule, e.g. A missing settings row must fall back to the domain default — never return a null/empty object to callers>  *(why: callers assume a valid value object)*
- INV-041: <placeholder: rule, e.g. Partial update payloads must preserve existing field values for absent keys>  *(why: separate UI cards submit disjoint subsets)*

---

## Legacy / Planned-for-Removal

<!-- hint: rules that protect legacy code from accidental expansion -->

- INV-050: <placeholder: rule, e.g. Routes marked for deletion must not be used as the baseline for new feature work>  *(why: they will be removed; new work must target current paths)*
- INV-051: <placeholder: rule, e.g. Do not remove or alter a legacy route without confirming all active callers are migrated>
