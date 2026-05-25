# Troubleshooting

## Related Application List Is Empty

Check:

- `pp_email_managements` has rows with known `email_key`.
- `EmailKey::KEYS` maps those email keys to module ids.
- `pp_mail_history_modules` has matching ids.
- `languages` has labels for the login locale.
- Access control is not filtering out every module.

## Filter By Module Returns Validation Error

The requested `moduleId` is not in the current user's visible module id collection.

Check:

- `User::isAppliedAccessControl()`
- `MailSendLogQueryService::filterAccessibleModules`
- `label_foreign_key` in `pp_mail_history_modules`
- target admin menu authority

## Export Opens Processing Page But No Result

Check:

- `BatchManagement::createBatch` succeeded.
- Batch record uses `class_name = mail-history-step`.
- Serialized options match the batch executor's expected names.
- Worker/cake demand process is running.

## Notification Setting Does Not Persist

Check:

- PUT payload is nested under `data` in `apiMap.js`.
- `NotificationSettingCommand` recognizes the submitted fields.
- `pp_tenant_settings.key = email_notification_setting` row is created/updated.
- JSON encoding succeeds in `SettingRepository`.

## Bounce Does Not Change Mail Status

Check:

- Authorization header equals the controller token.
- Payload has `data.Message`.
- Message JSON has `mail.headers`.
- Original People header exists.
- Matching `pp_email_managements` row has status send and `sent_at <= bounce_at`.
