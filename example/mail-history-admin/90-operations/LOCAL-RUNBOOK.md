# Local Runbook

## Start Backend

From repository root:

```bash
docker compose up -d
```

Apple silicon alternative from repo README:

```bash
docker-compose -f docker-compose-arm.yml up -d
```

## Start Frontend

From `app/vue`:

```bash
touch .env.local
npm i
npm start
```

For focused local serve, try:

```bash
URANUS_APP=mail_history_admin npm run serve
```

## Open Module

```text
http://localhost:50001/comet/mail-history/admin/history-others
http://localhost:50001/comet/mail-history/admin/setting-notification
```

## Useful DB Checks

```sql
SELECT id, email_key, unique_id, status, subject, created
FROM pp_email_managements
ORDER BY created DESC
LIMIT 20;

SELECT id, label_model, label_field, label_foreign_key
FROM pp_mail_history_modules
ORDER BY id;

SELECT id, `key`, json
FROM pp_tenant_settings
WHERE `key` = 'email_notification_setting';
```

## Export Verification

After clicking export, inspect server processing UI at:

```text
/comet/server-processing-another
```

For backend debugging, inspect `BatchManagement` records created with:

```text
class_name = mail-history-step
method_name = export
```
