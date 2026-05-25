# Mail History Admin Invariants

## Access Control

- A user must not see or export logs for a mail history module that is not visible to that user.
- When `User::isAppliedAccessControl()` is true, visible modules must be filtered by `getModuleMenuAbility()`.
- Backend must validate `moduleId`; frontend filtering alone is insufficient.

## Data Mapping

- Current history list records come from `pp_email_managements`.
- `email_key` must map to a module id through `EmailKey::KEYS`.
- A module id must have a row in `pp_mail_history_modules` and localized label data to display a module name.
- Rows with skipped email status are excluded from the current history list.

## Notification Setting

- Missing `pp_tenant_settings.key = email_notification_setting` means default `EmailNotificationSetting`.
- Update payloads are partial; absent fields must preserve existing/default values.
- `profile_item_ids_to_notify` values are represented as `ProfileItemID` value objects and sorted before persistence.

## Export

- Export APIs reserve server-side work through `BatchManagement`.
- Export APIs should not perform heavy export generation synchronously.
- The UI opens `server-processing-another` after successful reservation.

## Bounce Handling

- Bounce webhook must authorize before mutating data.
- Bounce update must only change a matching sent email record where `sent_at <= bounce_at`.
- Bounce data should preserve original message details in `pp_email_bounces`.

## Legacy Routes

- Routes marked `削除予定` should not be used as the default design baseline for new work.
- Do not remove or change legacy route behavior without checking current callers and product intent.
