# Dependency Map

## Internal Dependencies

| Dependency | Direction | Purpose |
|---|---|---|
| `share/store/main-page` | Vue depends on shared frontend | Loading state and main page initialization |
| `share/store/toastMessages` | Vue depends on shared frontend | Success/error toast messages |
| `GlobalContentLayout` | Vue depends on shared frontend | Shell layout and sidebar area |
| `UserSingleton` | Application services depend on login user | Access-control-aware filtering |
| `MailSendLogQueryService` | Services depend on query service | Visible modules and module access filtering |
| `MailSendLogRepository` | Services depend on repository | History list data, export job reservation, bounce update |
| `SettingRepository` | Notification services depend on repository | Tenant notification setting persistence |
| `PersonalProfileItemRepository` | Notification setting read depends on profile item metadata | Available email destination fields |
| `BatchManagement` | Export reservation depends on Cake model | Creates async export jobs |
| `EmailKey` | Query/repository depend on value object | Maps email keys to module ids |

## Data Dependencies

| Table | Use |
|---|---|
| `pp_email_managements` | Current mail send log list |
| `pp_email_bounces` | Bounce webhook persistence |
| `pp_mail_history_modules` | Module id to localized label metadata |
| `languages` | Module display names |
| `menus` / `RoleAuthority` | Legacy and non-access-control module visibility |
| `pp_mail_history_log_processes` | Legacy process history |
| `pp_mail_history_log_steps` | Legacy process recipient details |
| `pp_tenant_settings` | Notification setting JSON |

## Cross-Module Dependencies

Mail history data is produced by many modules through shared mail services and `PpEmailManagement`, including workflow, employee contract, job posting, HR FAQ, evaluation 360, static MBO, personal profile, self request, and one-on-one.

When adding a new producing module, update both:

- `People\ValueObject\EmailKey::KEYS`
- `pp_mail_history_modules` DML and localized menu labels
