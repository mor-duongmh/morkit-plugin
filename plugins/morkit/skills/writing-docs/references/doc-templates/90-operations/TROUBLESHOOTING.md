---
updated: <YYYY-MM-DD>
status: draft
---

# Troubleshooting

> Runtime diagnostics. For code-time mistakes to prevent in the first place see [../../40-ai-coding/KNOWN-PITFALLS.md](../../40-ai-coding/KNOWN-PITFALLS.md).

---

<!-- hint: one ## per observable symptom (what the user/dev sees), not per root cause -->
<!-- hint: Check: list = ordered from cheapest/fastest to most invasive -->

## `<Symptom: e.g. "List page returns empty results">`

Check:

- `<table>` has rows with the expected `<key_column>` values.
- `<constant or mapping file>` maps those values to the correct `<id or key>`.
- `<lookup or config table>` has matching rows.
- Access control is not filtering out all records — check `<auth/permission service or method>`.

---

## `<Symptom: e.g. "API returns 403 / 401 unexpectedly">`

Check:

- Token/session is valid and not expired.
- `<AuthMiddleware or Guard>` is applied on the route.
- User role/permission includes the required scope — check `<permission config or service>`.
- Environment variable `<AUTH_SECRET or similar>` is set correctly in `.env.local`.

---

## `<Symptom: e.g. "Background job created but never completes">`

Check:

- Worker process is running — see [LOCAL-RUNBOOK.md](LOCAL-RUNBOOK.md) start commands.
- Job record in `<jobs_table>` has `status = queued` (not already failed).
- Serialized args match what the job executor expects — check `<executor class or handler>`.
- Logs for the worker process show the error: `<log path or command>`.

---

## `<Symptom: e.g. "Form submission does not persist">`

Check:

- Network request payload contains the expected fields (browser DevTools → Network).
- `<DTO or Command>` parses those fields — check nullable / optional handling.
- `<Service>` calls `<Repository.save()>` — add a breakpoint or log if uncertain.
- DB row was actually updated: run the relevant query from [LOCAL-RUNBOOK.md](LOCAL-RUNBOOK.md).

---

## `<Symptom: e.g. "Frontend build or lint fails after a dependency change">`

Check:

- `node_modules` is up to date: run `<npm|pnpm|yarn> install`.
- Imported symbol still exists in the updated package — check its changelog.
- No circular import introduced — check `<lint rule or tool>` output.
