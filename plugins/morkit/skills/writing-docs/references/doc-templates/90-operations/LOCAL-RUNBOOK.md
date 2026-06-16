---
updated: <YYYY-MM-DD>
status: draft
---

# Local Runbook

> Starting the app locally. For running tests see [../../30-test/TEST-RUNBOOK.md](../../30-test/TEST-RUNBOOK.md). For runtime problems see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## Start

<!-- hint: one block per service; use exact commands from repo root -->

**Backend**

```bash
# example: Docker-based project
docker compose up -d

# example: native
<package-manager> install
<start-command>
```

**Frontend**

```bash
cd <frontend-dir>
cp .env.example .env.local   # first time only
<npm|pnpm|yarn> install
<npm|pnpm|yarn> start
```

**Other services** (queue workers, cron, etc.)

```bash
# example: start background worker
<worker-start-command>
```

---

## Access / URLs

<!-- hint: use text block, not Mermaid -->

```text
Frontend:   http://localhost:<port>/
Backend:    http://localhost:<port>/api/
Admin UI:   http://localhost:<port>/admin/
<other>:    http://localhost:<port>/<path>
```

---

## Useful DB / Data Checks

<!-- hint: sql or CLI commands a dev runs to inspect state during local development -->

```sql
-- Recent records
SELECT id, <key_column>, <status_column>, created_at
FROM <main_table>
ORDER BY created_at DESC
LIMIT 20;

-- Config / setting row
SELECT id, key, value
FROM <settings_table>
WHERE key = '<setting_key>';
```

```bash
# example: Redis / queue inspection
<redis-cli|queue-cli> <command>
```

---

## Verify Key Operations

<!-- hint: manual smoke-check steps after `docker compose up` or after a deploy to staging -->

1. Log in as `<role>` at `<login-url>`.
2. Navigate to `<page>` — confirm `<expected state, e.g. list loads with N rows>`.
3. Trigger `<action, e.g. export / submit form>` — confirm `<expected outcome>`.
4. Check background job result at `<job-status-url or DB query>`.
