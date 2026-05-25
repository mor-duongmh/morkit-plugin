# Design Map

## Design Layers

| Layer | Canonical Doc | Purpose |
|---|---|---|
| Architecture | `00-core/MAIL-HISTORY-ADMIN-ARCHITECTURE.md` | How Vue, CakePHP controllers, services, repositories, and data stores fit together |
| Invariants | `00-core/MAIL-HISTORY-ADMIN-INVARIANTS.md` | Rules that must not be broken by coding changes |
| Current history list | `10-features/SEND-LOG-OTHER-SYS-SPEC.md` | Current visible mail send history feature |
| Notification settings | `10-features/NOTIFICATION-SETTING-SYS-SPEC.md` | Tenant notification settings and related UI |
| Legacy process/step | `10-features/LEGACY-PROCESS-STEP-SYS-SPEC.md` | Routes marked planned for deletion |
| Data | `20-data/DATA-MAP.md` | Tables and JSON structures |
| API | `30-api/API-MAP.md` | Backend endpoint map |
| UI | `40-ui/UI-MAP.md` | Route/component map |
| Batch/export | `50-batch/EXPORT-BATCH-SYS-SPEC.md` | Async export reservation behavior |
| References | `90-reference/SOURCE-REFERENCE.md` | Source anchors |

## System Overview

```text
Cake route /mail-history/admin/*
-> MailHistoryAdminController
-> index.ctp includes generated Vue bundle
-> Vue router /history-others or /setting-notification
-> apiMap.js calls Cake API controllers
-> Application service builds commands and checks access
-> Repository/query service reads pp_email_managements or settings tables
-> Vue renders paginated data or setting form
```

## Key Design Decisions Found In Source

- Current history list uses `pp_email_managements`, not the older `pp_mail_history_log_*` process/step tables.
- Module filtering is based on `EmailKey::KEYS` and `pp_mail_history_modules`.
- Access-control-aware users only see modules allowed by `User::getModuleMenuAbility()`.
- Export requests create async `BatchManagement` jobs instead of streaming files from the API request.
- Notification setting update accepts partial payloads and merges them into existing/default `EmailNotificationSetting`.
