# Glossary

| Term | Meaning |
|---|---|
| Mail history admin | Admin UI and APIs for reviewing mail notification history |
| Email key | String key identifying a mail type, defined in `People\ValueObject\EmailKey` |
| Mail history module | Numeric module id used by history filtering, backed by `pp_mail_history_modules` |
| Other send log | Current list view backed by `pp_email_managements` |
| Process | Legacy batch-like mail process stored in `pp_mail_history_log_processes` |
| Step | Legacy per-recipient process log stored in `pp_mail_history_log_steps` |
| Bounce | Delivery failure status recorded from bounce webhook and reflected on `pp_email_managements` |
| Notification setting | Tenant-level email destination setting stored as JSON in `pp_tenant_settings` |
| Access control | Module visibility filtering based on login user's module menu ability |
| Export reservation | BatchManagement record creation that later executes an export job |
| `server-processing-another` | Page opened after export reservation so users can monitor/download server-side processing |

## Status Values

| Status | Where Used | Meaning |
|---|---|---|
| `SUCCESS` | Legacy step/process and UI filters | Successful send or successful process |
| `ERROR` | Legacy and current logs | Send or processing error |
| `BOUNCE` | Current logs | Mail was sent but later bounced |
| `PROCESSING` | Legacy/current mail status | Still being processed |
| `UNREGISTERED` | Legacy step logs | Recipient email address was not registered |
| `SKIP` | Current mail management table | Excluded from current list by `status != skip()` |
