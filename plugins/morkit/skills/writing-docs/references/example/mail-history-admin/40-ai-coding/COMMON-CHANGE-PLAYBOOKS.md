# Common Change Playbooks

## Add A New Filter To Current History List

1. Add UI field in `ModalFilterEmailOtherList.vue`.
2. Add local state and route query handling in `ListEmailHistoryOther.vue`.
3. Add query/body mapping in `apiMap.js`.
4. Add setter/getter to `MailHistoryOtherStepListGetCommand`.
5. Add corresponding field to `FindOtherMailSendLogCommand`.
6. Apply condition in `MailSendLogRepository::findOtherMailSendLogs`.
7. Mirror the same field in export command/service/repository.
8. Update `SEND-LOG-OTHER-SYS-SPEC.md` and `EXPORT-BATCH-SYS-SPEC.md`.

## Add A New Mail-Producing Module To History

1. Add email key constants in `EmailKey.php`.
2. Add keys under the correct module id in `EmailKey::KEYS`.
3. Add or verify `pp_mail_history_modules` DML row.
4. Add or verify localized labels in `languages`.
5. Confirm producing module writes `pp_email_managements.email_key` using the new key.
6. Check access control: `label_foreign_key` should map to the admin menu item checked by `getModuleMenuAbility()`.

## Change Notification Setting Shape

1. Update `EmailNotificationSetting` fields, `toArray()`, and `fromArray()`.
2. Update `NotificationSettingCommand` nullable field parsing.
3. Update `GetNotificationSettingResult` if response metadata/data changes.
4. Update `EmailSetting.vue` payload and rendering.
5. Add/adjust domain tests for default, fromArray, toArray, and partial update.

## Change Export Behavior

1. Find `MailSendLogRepository::exportOtherMailStep`.
2. Check the batch executor for `class_name = mail-history-step`.
3. Keep API response lightweight.
4. Keep UI navigation to `server-processing-another` after successful reservation.
5. Add tests for serialized options if possible.
