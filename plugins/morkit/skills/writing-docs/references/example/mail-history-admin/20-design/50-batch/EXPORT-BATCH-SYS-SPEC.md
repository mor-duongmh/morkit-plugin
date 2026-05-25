# Export Batch System Specification

## Purpose

Mail history exports are asynchronous. The API reserves a server-side batch job and the UI opens `server-processing-another`.

## Current History Export Flow

```text
ListEmailHistoryOther.handleSubmit()
-> POST /api/v1/mail-history/admin/send-logs-other/export
-> ApiMailHistoryAdminSendLogOtherListExportController
-> MailHistoryOtherStepExportReserveCommand
-> MailHistoryOtherStepExportReserveApplicationService
-> Validate module access
-> MailSendLogRepository::exportOtherMailStep
-> BatchManagement::createBatch
-> UI opens server-processing-another
```

## Batch Reservation

`MailSendLogRepository::exportOtherMailStep` creates:

| Field | Value |
|---|---|
| `category_class` | `Registration` |
| `class_name` | `mail-history-step` |
| `method_name` | `export` |
| `batch_name` | `メール送信履歴（詳細）` |
| `argument` | serialized options |

Serialized options:

- `processId`
- `moduleId`
- `startDate`
- `endDate`
- `status`
- `subject`
- `mail`
- `name`

## Legacy Export

`MailSendLogRepository::exportStep` also creates a `mail-history-step` export, but only with `processId`.

## Change Guidance

- Keep export filters aligned with list filters.
- Validate module access before creating a batch.
- Do not add synchronous export generation to the API controller.
- Check the batch executor for `class_name = mail-history-step` before changing option names.
