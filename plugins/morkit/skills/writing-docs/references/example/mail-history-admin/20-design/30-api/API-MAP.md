# API Map

## Page Route

| Method | Path | Controller | Purpose |
|---|---|---|---|
| GET | `/mail-history/admin/*` | `MailHistoryAdminController::index` | Render Vue app |

## Mail History APIs

| Method | Path | Controller | Purpose |
|---|---|---|---|
| GET | `/api/v1/mail-history/admin/processes/page` | `ApiMailHistoryAdminProcessListPageGetController` | Return visible related application modules |
| GET | `/api/v1/mail-history/admin/send-logs-other` | `ApiMailHistoryAdminSendLogOtherListGetController` | Return current paginated mail history |
| POST | `/api/v1/mail-history/admin/send-logs-other/export` | `ApiMailHistoryAdminSendLogOtherListExportController` | Reserve export for current history filters |
| GET | `/api/v1/mail-history/admin/processes/:processId/steps` | `ApiMailHistoryAdminStepListGetController` | Legacy process step list |
| POST | `/api/v1/mail-history/admin/processes/:processId/steps/export` | `ApiMailHistoryAdminStepExportController` | Legacy process step export |
| POST | `/api/mail-history/admin/bounce-logs` | `ApiMailHistoryAdminBounceLogCreateController` | Bounce webhook |

## Setting APIs

| Method | Path | Controller | Purpose |
|---|---|---|---|
| GET | `/api/v1/mail-history/admin/todos/setting` | `ApiHeaderTodoDeletableGetController` | Get header TODO deletion setting |
| PUT | `/api/v1/mail-history/admin/todos/setting` | `ApiHeaderTodoDeletableUpdateController` | Update header TODO deletion setting |
| GET | `/api/v1/mail-history/admin/notification/setting` | `ApiMailHistoryAdminNotificationSettingGetController` | Get email destination setting |
| PUT | `/api/v1/mail-history/admin/notification/setting` | `ApiMailHistoryAdminNotificationSettingUpdateController` | Update email destination setting |
| GET | `/api/account-notification/count` | Outside this module | Count account notification targets |
| POST | `/api/account-notification/count` | Outside this module | Trigger account notification mail |

## Query Parameters: `send-logs-other`

| Param | Type | Default | Notes |
|---|---|---|---|
| `page` | int | `1` | Controller default |
| `pageSize` | int | `20` backend, `10` UI initial | UI normally sends pageSize |
| `processId` | string | null | Special personal profile notification filtering |
| `moduleId` | string | null | Must be visible to current user |
| `status` | string | null | `SUCCESS`, `ERROR`, `BOUNCE` |
| `startDate` | string | null | Parsed by shared `Date` value object |
| `endDate` | string | null | Parsed by shared `Date` value object |
| `subject` | string | null | LIKE search |
| `mailAddress` | string | null | Searches legacy and JSON recipients |
| `name` | string | null | Searches legacy and JSON recipient names |

## Error Handling Notes

- Some list APIs catch `ValidationException` and return its response body without explicitly setting HTTP 400.
- Notification setting update catches `ValidationException` and returns HTTP 400.
- Bounce webhook returns HTTP 401 when the authorization header does not match its static token.
