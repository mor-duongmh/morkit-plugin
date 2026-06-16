# Source Reference

## Routes

- `app/Config/routes.php`

Search anchor:

```text
メール通知履歴
```

## Frontend

- `app/vue/src/mail-history-admin/api/apiMap.js`
- `app/vue/src/mail-history-admin/router/router.js`
- `app/vue/src/mail-history-admin/layout/Layout.vue`
- `app/vue/src/mail-history-admin/components/Table/ListEmailHistoryOther.vue`
- `app/vue/src/mail-history-admin/components/Modal/ModalFilterEmailOtherList.vue`
- `app/vue/src/mail-history-admin/components/Notification/NotificationSetting.vue`
- `app/vue/src/mail-history-admin/components/SettingEmail/EmailSetting.vue`

## Backend Controllers

- `app/Controller/people/MailHistoryAdminController.php`
- `app/Controller/api/People/MailHistoryAdmin/ApiMailHistoryAdminProcessListPageGetController.php`
- `app/Controller/api/People/MailHistoryAdmin/ApiMailHistoryAdminSendLogOtherListGetController.php`
- `app/Controller/api/People/MailHistoryAdmin/ApiMailHistoryAdminSendLogOtherListExportController.php`
- `app/Controller/api/People/MailHistoryAdmin/ApiMailHistoryAdminNotificationSettingGetController.php`
- `app/Controller/api/People/MailHistoryAdmin/ApiMailHistoryAdminNotificationSettingUpdateController.php`
- `app/Controller/api/People/MailHistoryAdmin/ApiMailHistoryAdminBounceLogCreateController.php`

## Backend Services

- `app/Lib/people/Core/Application/MailHistory/MailHistoryProcessListPageGetApplicationService.php`
- `app/Lib/people/Core/Application/MailHistory/MailOtherSendLogListGetApplicationService.php`
- `app/Lib/people/Core/Application/MailHistory/MailHistoryOtherStepExportReserveApplicationService.php`
- `app/Lib/people/Core/Application/MailHistory/GetNotificationSettingService.php`
- `app/Lib/people/Core/Application/MailHistory/UpdateNotificationSettingService.php`
- `app/Lib/people/Core/Application/MailHistory/MailHistoryStepBounceApplicationService.php`

## Persistence

- `app/Lib/people/Core/Infrastructure/Cake2/MailHistory/MailSendLogRepository.php`
- `app/Lib/people/Core/Infrastructure/Cake2/MailHistory/SettingRepository.php`
- `app/Lib/people/Core/Infrastructure/Cake2Query/MailHistory/MailSendLogQueryService.php`
- `app/Lib/people/Core/Infrastructure/Cake2Query/MailHistory/EmailManagementModuleQueryService.php`

## DB Schema Anchors

- `docker/mysql/data/dmp-people-schema.sql`
- `docker/mysql/ddl/`
- `docker/mysql/dml/`
