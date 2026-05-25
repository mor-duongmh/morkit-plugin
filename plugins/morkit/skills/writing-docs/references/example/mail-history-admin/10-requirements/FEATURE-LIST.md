# Feature List

## Current Features

| Feature | Status | User Value | Main Sources |
|---|---|---|---|
| Mail send history list | Active | Admin can inspect sent/error/bounced mail records across related applications | `ListEmailHistoryOther.vue`, `ApiMailHistoryAdminSendLogOtherListGetController.php` |
| Mail send history filter | Active | Admin can narrow logs by module, status, date, subject, email, name | `ModalFilterEmailOtherList.vue`, `MailOtherSendLogListGetApplicationService.php` |
| Mail send history export | Active | Admin can export filtered mail history via async server processing | `ApiMailHistoryAdminSendLogOtherListExportController.php`, `MailHistoryOtherStepExportReserveApplicationService.php` |
| Notification setting | Active | Admin can control TODO deletion setting and trigger account notification mails | `NotificationSetting.vue`, `ApiHeaderTodoDeletable*`, account notification APIs |
| Email destination setting | Hidden in sidebar | Route/component exists for configuring destination profile items and retiree behavior | `EmailSetting.vue`, `ApiMailHistoryAdminNotificationSetting*` |
| Bounce log webhook | Backend active | External mail bounce events can update records as bounced | `ApiMailHistoryAdminBounceLogCreateController.php` |
| Legacy process/step list | Legacy | Old process/recipient history API still exists | `ApiMailHistoryAdminStepListGetController.php` |

## Non-Functional Requirements

- History visibility must respect access control when position access control is applied.
- Exports should be async via `BatchManagement`; UI opens `server-processing-another` after reservation.
- Notification settings must support partial updates because the UI submits different payload shapes from separate cards.
- Date filters must be accepted by backend value objects and should not allow unsupported old date windows from the UI.
- Bounce webhook must reject unauthorized requests before parsing and mutating mail data.
