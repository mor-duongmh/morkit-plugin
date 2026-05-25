# Test Matrix

| Feature | Case | Expected Result |
|---|---|---|
| Module list | Access control off | Returns modules from `getModules()` intersected with email keys present in `PpEmailManagement` |
| Module list | Access control on | Returns only modules allowed by `getModuleMenuAbility()` and present in email keys |
| History list | No filters | Returns non-skip records for visible modules, newest first |
| History list | Invalid module id | Validation error for inaccessible module |
| History list | Status filter `SUCCESS` | Only successful rows |
| History list | Status filter `ERROR` | Only error rows |
| History list | Status filter `BOUNCE` | Only bounced rows |
| History list | Email filter | Matches legacy `to` and JSON `params.to[*].email` |
| History list | Name filter | Matches legacy `to_name` and JSON `params.to[*].name` |
| History export | Same filters as list | Batch options contain same filters |
| Notification setting get | No tenant setting row | Returns default `EmailNotificationSetting` |
| Notification setting update | Only retiree flag sent | Destination item ids and allow-modify flag are preserved |
| Notification setting update | Destination payload sent | `profile_item_ids_to_notify` sorted and persisted |
| Bounce webhook | Missing/wrong token | HTTP 401, no mutation |
| Bounce webhook | Valid payload with original header | `pp_email_bounces` insert and matching email management row updated to bounce |
