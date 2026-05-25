# Source Map

## Module Source Summary

| Concern | Files / Directories | Responsibility |
|---|---|---|
| Web route | `app/Config/routes.php` | Defines page and API routes |
| Page controller | `app/Controller/people/MailHistoryAdminController.php` | Renders the Vue page with `people_page_vue_share` layout |
| Page view | `app/View/people/MailHistoryAdmin/index.ctp` | Includes `vue/mail_history_admin_js` |
| Vue entry | `app/vue/src/mail-history-admin/main.js` | Creates the SPA |
| Vue router | `app/vue/src/mail-history-admin/router/router.js` | Routes under `/mail-history/admin/` |
| Vue API map | `app/vue/src/mail-history-admin/api/apiMap.js` | Maps frontend actions to backend endpoints |
| History list UI | `app/vue/src/mail-history-admin/components/Table/ListEmailHistoryOther.vue` | Current mail send history list |
| Filter modal | `app/vue/src/mail-history-admin/components/Modal/ModalFilterEmailOtherList.vue` | Filter input and date validation |
| Notification UI | `app/vue/src/mail-history-admin/components/Notification/NotificationSetting.vue` | TODO delete setting and account notification action |
| Email destination UI | `app/vue/src/mail-history-admin/components/SettingEmail/EmailSetting.vue` | Route exists, menu currently commented |
| API controllers | `app/Controller/api/People/MailHistoryAdmin/` | Thin controllers that construct commands/services |
| App services | `app/Lib/people/Core/Application/MailHistory/` | Use cases for listing, export, settings, bounce |
| Domain objects | `app/Lib/people/Core/Domain/Model/MailHistory/` | Commands, results, value objects, collection wrappers |
| Repository | `app/Lib/people/Core/Infrastructure/Cake2/MailHistory/MailSendLogRepository.php` | Reads/writes logs and reserves export batches |
| Query service | `app/Lib/people/Core/Infrastructure/Cake2Query/MailHistory/MailSendLogQueryService.php` | Retrieves visible modules and access-control filtering |
| Email module map | `app/Lib/people/ValueObject/EmailKey.php` | Maps email keys to mail history module ids |

## Important Symbols

| Symbol | File | Purpose |
|---|---|---|
| `MailHistoryAdminController::index` | `app/Controller/people/MailHistoryAdminController.php` | Page entrypoint |
| `ApiMailHistoryAdminSendLogOtherListGetController::invoke` | `app/Controller/api/People/MailHistoryAdmin/ApiMailHistoryAdminSendLogOtherListGetController.php` | Current history list API |
| `MailOtherSendLogListGetApplicationService::handle` | `app/Lib/people/Core/Application/MailHistory/MailOtherSendLogListGetApplicationService.php` | Validates module access and builds find command |
| `MailSendLogRepository::findOtherMailSendLogs` | `app/Lib/people/Core/Infrastructure/Cake2/MailHistory/MailSendLogRepository.php` | Queries `pp_email_managements` |
| `MailHistoryOtherStepExportReserveApplicationService::handle` | `app/Lib/people/Core/Application/MailHistory/MailHistoryOtherStepExportReserveApplicationService.php` | Reserves filtered export |
| `MailSendLogRepository::exportOtherMailStep` | `app/Lib/people/Core/Infrastructure/Cake2/MailHistory/MailSendLogRepository.php` | Creates `BatchManagement` job |
| `GetNotificationSettingService::handle` | `app/Lib/people/Core/Application/MailHistory/GetNotificationSettingService.php` | Reads tenant email notification setting |
| `UpdateNotificationSettingService::handle` | `app/Lib/people/Core/Application/MailHistory/UpdateNotificationSettingService.php` | Saves partial notification setting updates |
| `ApiMailHistoryAdminBounceLogCreateController::invoke` | `app/Controller/api/People/MailHistoryAdmin/ApiMailHistoryAdminBounceLogCreateController.php` | Receives bounce webhook |

## Code Search Keywords

Use these keywords when investigating this module:

```text
mail-history-admin
mail_history_admin
MailHistoryAdmin
MailOtherSendLog
MailHistoryOtherStep
MailHistoryProcess
email_notification_setting
pp_email_managements
pp_mail_history_modules
pp_mail_history_log_steps
pp_email_bounces
EmailKey::KEYS
server-processing-another
```

## Source Boundaries

This module owns:

- Admin UI for mail history and related settings.
- Filtering/export reservation for displayed history data.
- Mapping visible mail history modules based on email keys and access control.

This module depends on:

- Mail records produced by other modules.
- Shared account notification endpoints.
- Shared batch processing and SQS/mail sender infrastructure.

This module must not own:

- Source business rules deciding when a workflow/evaluation/job-posting mail is generated.
- Email template content for each business module.
