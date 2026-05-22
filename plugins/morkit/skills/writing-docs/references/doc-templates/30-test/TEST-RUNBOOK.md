---
updated: <YYYY-MM-DD>
status: draft
---

# Test Runbook

> This doc covers HOW TO RUN tests. For test scope and priorities see [TEST-STRATEGY.md](TEST-STRATEGY.md). For starting the app locally see [../../90-operations/LOCAL-RUNBOOK.md](../../90-operations/LOCAL-RUNBOOK.md).

---

## How To Run

<!-- hint: one block per stack/language; use exact commands that work from repo root -->

**Backend**

```bash
# example: cd into project root or container, then run targeted tests
<enter-container-or-cd-command>
<test-runner-command> <path/to/test>
```

**Frontend**

```bash
# example: from frontend directory
cd <frontend-dir>
npm run lint
npm run test:unit
```

---

## Manual Verification

<!-- hint: list URLs/routes a developer should open after a change; use text block, not Mermaid -->

```text
<base-url>/<route-1>
<base-url>/<route-2>
```

Steps:
1. Log in as `<role, e.g. "admin user with access control enabled">`.
2. Navigate to `<page>` and verify `<expected state>`.
3. Apply filters and confirm results match `<criteria>`.

---

## Minimal Verification By Change Type

<!-- hint: keep this table tight — one row per change type, Required Checks must be actionable -->

| Change Type | Required Checks |
|---|---|
| <e.g. "UI-only layout change"> | <e.g. "Open page, check empty state, non-empty state, pagination"> |
| <e.g. "Filter query change"> | <e.g. "Verify query params sent to API, check backend filter logic"> |
| <e.g. "Backend list query"> | <e.g. "Test with access allowed/denied, apply each filter, check pagination"> |
| <e.g. "Export change"> | <e.g. "Trigger export, verify job created with correct options"> |
| <e.g. "Auth / permission change"> | <e.g. "Test with authorized and unauthorized user, expect 401/403"> |

---

## Current Gaps

<!-- hint: honest list of what is NOT tested yet; agents use this to know where to be careful -->

- No automated tests for `<controller | route | component>`.
- `<Area>` tested manually only; no fixture setup exists yet.
