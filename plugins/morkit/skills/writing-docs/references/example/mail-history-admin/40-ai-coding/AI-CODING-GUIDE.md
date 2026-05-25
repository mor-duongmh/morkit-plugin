# AI Coding Guide

## Before Editing

Read these first:

1. `00-overview/SOURCE-MAP.md`
2. `20-design/DESIGN-MAP.md`
3. The relevant feature spec in `20-design/10-features/`
4. `30-test/TEST-RUNBOOK.md`

## Safe Change Workflow

1. Identify whether the change targets current history, hidden email settings, visible notification settings, bounce handling, or legacy process/step APIs.
2. Confirm frontend route/component and backend API mapping in `apiMap.js`.
3. Check command/result objects before changing request or response shapes.
4. Preserve backend access-control checks for any list/export path.
5. Keep export filters aligned with list filters.
6. Run or document targeted tests.
7. Update this docs folder if behavior, routes, request fields, response fields, or persistence rules changed.

## Common Source Entry Points

| Task | Start Here |
|---|---|
| Add a filter to current history list | `ListEmailHistoryOther.vue`, `apiMap.js`, `MailHistoryOtherStepListGetCommand`, `FindOtherMailSendLogCommand`, `findOtherMailSendLogs` |
| Change visible related applications | `MailHistoryProcessListPageGetApplicationService`, `MailSendLogQueryService`, `EmailManagementModuleQueryService`, `EmailKey::KEYS` |
| Change export filters | `ListEmailHistoryOther.vue::handleSubmit`, `ApiMailHistoryAdminSendLogOtherListExportController`, `MailHistoryOtherStepExportReserveApplicationService`, `exportOtherMailStep` |
| Change notification destination setting | `EmailSetting.vue`, `NotificationSettingCommand`, `EmailNotificationSetting`, `SettingRepository` |
| Change TODO deletion setting UI | `NotificationSetting.vue`, `ApiHeaderTodoDeletable*` |
| Change bounce handling | `ApiMailHistoryAdminBounceLogCreateController`, `MailHistoryStepBounceApplicationService`, `MailSendLogRepository::saveBouncedMail`, `updateEmailManagement` |

## Do Not Break

- Do not trust frontend module filtering for authorization.
- Do not add a new mail history module only in DML; update `EmailKey::KEYS` too.
- Do not remove partial update behavior from `NotificationSettingCommand`.
- Do not change export serialized option names without checking the `mail-history-step` batch executor.
- Do not use legacy process/step tables for the current history list unless the requirement explicitly says so.

## Notes For Agents

- There are two history systems in the code: current `pp_email_managements` and legacy `pp_mail_history_log_*`.
- The current visible list is `history-others`.
- `setting-emails` is route-enabled but sidebar-hidden.
- Some strings/status labels are hard-coded Japanese in backend repository methods.
