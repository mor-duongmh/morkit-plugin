# Notification Setting System Specification

## Purpose

The notification setting area contains two related behaviors:

- `setting-notification`: header TODO deletion setting and account notification send trigger.
- `setting-emails`: tenant email destination settings. The route/component exists, but the sidebar menu item is currently commented out.

## Source Anchors

| Layer | Source |
|---|---|
| Visible notification UI | `app/vue/src/mail-history-admin/components/Notification/NotificationSetting.vue` |
| Hidden email destination UI | `app/vue/src/mail-history-admin/components/SettingEmail/EmailSetting.vue` |
| API client | `app/vue/src/mail-history-admin/api/apiMap.js` |
| TODO setting get/update | `ApiHeaderTodoDeletableGetController.php`, `ApiHeaderTodoDeletableUpdateController.php` |
| Email setting get/update | `ApiMailHistoryAdminNotificationSettingGetController.php`, `ApiMailHistoryAdminNotificationSettingUpdateController.php` |
| Email setting services | `GetNotificationSettingService.php`, `UpdateNotificationSettingService.php` |
| Setting entity | `EmailNotificationSetting.php` |
| Setting repository | `SettingRepository.php` |

## Visible Setting Notification Flow

```text
Admin opens /setting-notification
-> NotificationSetting.created()
-> application/getSetting
-> GET /api/v1/mail-history/admin/todos/setting
-> api('getAmountNoticedAccounts')
-> GET /api/account-notification/count
-> Admin can update TODO setting or send account notification mail
```

## Email Destination Setting Flow

```text
Admin opens /setting-emails
-> EmailSetting.created()
-> GET /api/v1/mail-history/admin/notification/setting
-> GetNotificationSettingService reads setting or creates default
-> PersonalProfileItemRepository returns usable email profile items
-> Admin changes profile item ids / modify permission / retiree behavior
-> PUT /api/v1/mail-history/admin/notification/setting
-> UpdateNotificationSettingService merges provided fields
-> SettingRepository saves JSON in pp_tenant_settings
```

## Persisted Shape

Stored in `pp_tenant_settings`:

```json
{
  "key": "email_notification_setting",
  "json": {
    "profile_item_ids_to_notify": [1, 2],
    "send_to_retirees": true,
    "is_allowed_to_modify": false
  }
}
```

## Business Rules

| Rule ID | Rule |
|---|---|
| MH-NS-001 | Missing setting row falls back to `new EmailNotificationSetting()`. |
| MH-NS-002 | Default destination profile item ids are `ProfileItemID::DefaultItemIDs()`. |
| MH-NS-003 | Available destination checkboxes are `ProfileItemID::AllEmailItemIDs()` filtered by `ProfileItem::isUse()`. |
| MH-NS-004 | Update payload may include only destination fields or only retiree setting. |
| MH-NS-005 | Absent fields must remain unchanged. |
| MH-NS-006 | Save happens inside `TransactionV4`. |

## Change Impact

When changing this feature, check:

- `EmailSetting.vue` payload shape.
- `NotificationSettingCommand` constructor and nullable field behavior.
- `EmailNotificationSetting::toArray()` and `fromArray()`.
- `SettingRepository` key name.
- Account notification endpoints if changing `setting-notification`.
