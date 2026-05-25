# Legacy Process Step System Specification

## Status

Legacy / planned for deletion.

`app/Config/routes.php` marks these routes with `削除予定`:

- `GET /api/v1/mail-history/admin/processes/:processId/steps`
- `POST /api/v1/mail-history/admin/processes/:processId/steps/export`

## Source Anchors

| Layer | Source |
|---|---|
| Detail UI component | `app/vue/src/mail-history-admin/components/Table/EmailDetail.vue` |
| Detail API controller | `ApiMailHistoryAdminStepListGetController.php` |
| Detail export controller | `ApiMailHistoryAdminStepExportController.php` |
| List service | `MailSendLogListGetApplicationService.php` |
| Export service | `MailHistoryStepExportReserveApplicationService.php` |
| Repository methods | `findSendLogs`, `exportStep` in `MailSendLogRepository.php` |
| Tables | `pp_mail_history_log_processes`, `pp_mail_history_log_steps` |

## Behavior

Legacy detail list reads per-recipient rows from `pp_mail_history_log_steps` for one `processId`.

Supported filters:

- `page`
- `pageSize`
- `status`

Supported status tabs in `EmailDetail.vue`:

- all
- `SUCCESS`
- `ERROR`
- `UNREGISTERED`

## Design Notes

- Current main sidebar no longer exposes a route that clearly navigates to this component.
- `EmailDetail.vue` still references `this.$route.params.id`; this route is not registered in the current `router.js`.
- Treat this code as compatibility residue until callers are confirmed.

## Change Guidance

Do not use this legacy process/step path as the base for new history list work. Current list work should start from `SEND-LOG-OTHER-SYS-SPEC.md`.
