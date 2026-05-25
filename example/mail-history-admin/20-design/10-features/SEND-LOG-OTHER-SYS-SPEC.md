# Send Log Other System Specification

## Purpose

The current mail send history list lets administrators review mail records stored in `pp_email_managements` across related applications.

## Source Anchors

| Layer | Source |
|---|---|
| UI page | `app/vue/src/mail-history-admin/components/Table/ListEmailHistoryOther.vue` |
| Filter modal | `app/vue/src/mail-history-admin/components/Modal/ModalFilterEmailOtherList.vue` |
| API client | `app/vue/src/mail-history-admin/api/apiMap.js` |
| List controller | `app/Controller/api/People/MailHistoryAdmin/ApiMailHistoryAdminSendLogOtherListGetController.php` |
| List service | `app/Lib/people/Core/Application/MailHistory/MailOtherSendLogListGetApplicationService.php` |
| Repository query | `app/Lib/people/Core/Infrastructure/Cake2/MailHistory/MailSendLogRepository.php::findOtherMailSendLogs` |
| Module list API | `ApiMailHistoryAdminProcessListPageGetController.php` |
| Module list service | `MailHistoryProcessListPageGetApplicationService.php` |

## Flow

```text
ListEmailHistoryOther.created()
-> api('getApplication')
-> GET /api/v1/mail-history/admin/processes/page
-> visible modules returned
-> query params copied into local filter params
-> api('getEmailHistoriesOther')
-> GET /api/v1/mail-history/admin/send-logs-other
-> MailOtherSendLogListGetApplicationService validates module access
-> MailSendLogRepository::findOtherMailSendLogs queries pp_email_managements
-> UI updates list and pagination
```

## Filters

| UI Field | Query Param | Backend Command Setter | Notes |
|---|---|---|---|
| related application | `moduleId` | `setModuleId` | Must be visible to current user |
| status tab | `status` | `setStatus` | `SUCCESS`, `ERROR`, `BOUNCE`, or empty |
| start date/time | `startDate` | `setStartDate` | Compared with `t.created >=` |
| end date/time | `endDate` | `setEndDate` | Compared with `t.created <=` |
| subject | `subject` | `setSubject` | LIKE search, `\n` converted |
| email address | `mailAddress` | `setMail` | Searches legacy `to` and JSON `params.to[*].email` |
| employee name | `name` | `setName` | Searches legacy `to_name` and JSON `params.to[*].name` |
| process id | `processId` | `setProcessId` | Special handling for personal profile notification module |

## Response Data Used By UI

`EmailOtherDetailRow.vue` expects:

| Field | Usage |
|---|---|
| `stepId` | Backend row id returned by `MailOtherSendLogListGetResult` |
| `status` | Numeric/index status styling |
| `statusName` | Display label |
| `startDate` | Send date display |
| `moduleName` | Related application |
| `fullName` | Recipient name |
| `employeeCode` | Recipient employee code |
| `mail` | Recipient email |
| `subject` | Mail subject rendered with `v-html` |
| `message` | Error/bounce message rendered with `v-html` |

## Business Rules

| Rule ID | Rule |
|---|---|
| MH-SL-001 | Only non-skip `pp_email_managements` rows are listed. |
| MH-SL-002 | If `moduleId` is provided, it must be included in current user's visible modules. |
| MH-SL-003 | If `moduleId` is not provided, query uses all visible module ids. |
| MH-SL-004 | Module id to email key mapping comes from `EmailKey::KEYS`. |
| MH-SL-005 | The list is ordered by `pp_email_managements.created DESC`. |
| MH-SL-006 | UI date filter requires date and time to be entered as a pair. |
| MH-SL-007 | UI blocks start/end dates older than 89 days from current date. |

## Current Source Mismatch

`MailOtherSendLogListGetResult` returns `stepId`, but `ListEmailHistoryOther.vue` currently renders rows with `:key="item.id"`. Treat this as an existing source issue to verify before editing row identity behavior.

## Change Impact

When changing this feature, check:

- `apiMap.js` parameter names.
- `MailHistoryOtherStepListGetCommand` setters/getters.
- `FindOtherMailSendLogCommand`.
- `MailSendLogRepository::findOtherMailSendLogs`.
- `MailOtherSendLogListGetResult` and `MailSendLog::toArray()` behavior.
- Export feature because it mirrors the list filters.
- Access-control filtering for module visibility.
