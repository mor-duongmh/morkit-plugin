# Document Map

This document explains where each type of information for `mail-history-admin` is maintained.

## Directory Roles

| Directory | Role |
|---|---|
| `00-overview` | Entry docs, scope, glossary, source map, dependency map |
| `10-requirements` | Feature inventory, user flows, behavioral requirements |
| `20-design` | Architecture, feature specs, data/API/UI/batch design |
| `30-test` | Test strategy, runbook, test matrix |
| `40-ai-coding` | Coding guide optimized for AI agents |
| `90-operations` | Local runbook and troubleshooting |
| `archive` | Old notes and non-canonical material |

## Read Paths

### Understand The Module

1. `README.md`
2. `00-overview/SCOPE.md`
3. `00-overview/SOURCE-MAP.md`
4. `20-design/DESIGN-MAP.md`

### Change The Mail History List

1. `20-design/10-features/SEND-LOG-OTHER-SYS-SPEC.md`
2. `20-design/30-api/API-MAP.md`
3. `20-design/20-data/DATA-MAP.md`
4. `40-ai-coding/COMMON-CHANGE-PLAYBOOKS.md`
5. `30-test/TEST-RUNBOOK.md`

### Change Notification Settings

1. `20-design/10-features/NOTIFICATION-SETTING-SYS-SPEC.md`
2. `20-design/20-data/DATA-MAP.md`
3. `40-ai-coding/AI-CODING-GUIDE.md`
4. `30-test/TEST-RUNBOOK.md`

### Investigate Legacy Process/Step History

1. `20-design/10-features/LEGACY-PROCESS-STEP-SYS-SPEC.md`
2. `20-design/50-batch/EXPORT-BATCH-SYS-SPEC.md`
3. `40-ai-coding/RISK-REGISTER.md`

## Canonical Source Rules

- Route truth: `app/Config/routes.php`
- Vue route truth: `app/vue/src/mail-history-admin/router/router.js`
- API client truth: `app/vue/src/mail-history-admin/api/apiMap.js`
- Email key to module mapping: `app/Lib/people/ValueObject/EmailKey.php`
- Mail history module labels: `pp_mail_history_modules` plus `languages`
- Notification setting persistence: `pp_tenant_settings.key = email_notification_setting`
