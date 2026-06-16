# Test Runbook

## PHP Unit Tests

Run targeted CakePHP tests inside the app container.

Common local pattern from repo docs:

```bash
docker exec -it uranus-app /bin/bash
cd /var/www/html/comet/dev-tools
```

Targeted examples:

```bash
sh phpunit-bridge.sh app/Test/Case/people/Core/Domain/Model/MailHistory/EmailNotificationSettingTest.php
sh phpunit-bridge.sh app/Test/Case/people/Core/Domain/Model/MailHistory/EmailMessageTest.php
sh phpunit-bridge.sh app/Test/Case/people/Core/ApplicationService/MailHistory/EmailSendingServiceTest.php
```

If using the Cake test runner directly, follow the project-local CakePHP 2 test convention for the target test case.

## Frontend Checks

From `app/vue`:

```bash
npm run lint
npm run test:unit
URANUS_APP=mail_history_admin npm run serve
```

The repo's standard watch flow usually uses:

```bash
cd app/vue
npm start
```

with `.env.local` controlling the app build target.

## Manual Verification URLs

Local app base from repo README:

```text
http://localhost:50001/comet/
```

Module routes:

```text
/comet/mail-history/admin/history-others
/comet/mail-history/admin/setting-notification
/comet/mail-history/admin/setting-emails
```

## Minimal Verification By Change Type

| Change Type | Required Checks |
|---|---|
| Vue-only list layout | Open `history-others`, check empty and non-empty rows, pagination, status tabs |
| Filter query change | Check URL query, API query params, backend command setters |
| Backend list query | Test with module access allowed/denied, status/date/text filters, pagination |
| Export change | Check batch row options and `server-processing-another` navigation |
| Notification setting | Check default row absence, partial update, persisted JSON |
| Bounce change | Check unauthorized request, valid webhook payload, bounced mail update |

## Current Gaps

- Direct API controller tests for `ApiMailHistoryAdmin*` are missing.
- Frontend tests for `mail-history-admin` components were not found in the source scan.
