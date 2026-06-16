---
updated: <YYYY-MM-DD>
status: draft
---

# Common Change Playbooks

> End-to-end steps for recurring change types. For file locations start from [../../00-overview/SOURCE-MAP.md](../../00-overview/SOURCE-MAP.md). For constraints check [../../20-design/00-core/INVARIANTS.md](../../20-design/00-core/INVARIANTS.md) first.

---

<!-- hint: one ## per change type; steps are numbered e2e (code → test → doc update) -->
<!-- hint: every playbook MUST end with a "Update docs" step naming which file to update -->

## Add A New `<Entity / Field / Filter>`

1. Add the field/constant to `<Model or Schema file>`.
2. Update `<Command or DTO>` to accept the new value.
3. Apply the new field in `<Repository or Query method>`.
4. Expose it in `<API controller or handler>`.
5. Add/update UI component in `<Component file>`.
6. Add unit test covering the happy path and a missing-value case.
7. Run `<test command>` per [../../30-test/TEST-RUNBOOK.md](../../30-test/TEST-RUNBOOK.md).
8. Update `<../../20-design/10-features/FEATURE-SYS-SPEC.md>` (request/response shape section).

---

## Change `<Existing Behavior / Business Rule>`

1. Read the relevant `<FEATURE-SYS-SPEC.md>` to understand current contract.
2. Update domain/service logic in `<ServiceClass>`.
3. Update `<Repository>` if persistence changes.
4. Update or add tests in `<test path>`.
5. Run targeted tests per [../../30-test/TEST-RUNBOOK.md](../../30-test/TEST-RUNBOOK.md).
6. Update `<../../20-design/10-features/FEATURE-SYS-SPEC.md>` (behavior or rules section).

---

## Add A New `<Module / Integration / Webhook>`

1. Register constants/keys in `<constants file>`.
2. Add DB seed/migration row if a lookup table is involved.
3. Implement handler/service in `<path>`.
4. Wire route/endpoint in `<router or config file>`.
5. Add auth/permission check — verify against [../../20-design/00-core/INVARIANTS.md](../../20-design/00-core/INVARIANTS.md).
6. Write integration test covering auth failure and success cases.
7. Run tests per [../../30-test/TEST-RUNBOOK.md](../../30-test/TEST-RUNBOOK.md).
8. Update [../../00-overview/SOURCE-MAP.md](../../00-overview/SOURCE-MAP.md) (new concern → file mapping) and `<FEATURE-SYS-SPEC.md>`.

---

## Remove / Deprecate `<Feature or Route>`

1. Search all callers: see [CODE-SEARCH-GUIDE.md](CODE-SEARCH-GUIDE.md) for route/symbol recipes.
2. Confirm no active caller exists (routes, frontend links, batch jobs, external clients).
3. Mark deprecated or delete code and tests.
4. Remove or archive DB rows/migrations if safe.
5. Update [../../00-overview/SOURCE-MAP.md](../../00-overview/SOURCE-MAP.md) and `<FEATURE-SYS-SPEC.md>` (mark removed/archived).
