# User Flows

## Flow: View Mail Send History

```text
Admin opens /mail-history/admin/
-> Vue router redirects to /history-others
-> UI requests /api/v1/mail-history/admin/processes/page
-> UI receives visible related applications
-> UI requests /api/v1/mail-history/admin/send-logs-other
-> API returns paginated mail records
-> UI renders status, send date, module, recipient, subject, error/remarks
```

## Flow: Filter History

```text
Admin opens filter modal
-> Selects related application and optional date/time/status/text filters
-> UI validates date/time completeness and 89-day minimum date window
-> UI writes query params into route
-> UI calls /api/v1/mail-history/admin/send-logs-other
-> Backend validates module access
-> Backend queries pp_email_managements
```

## Flow: Export History

```text
Admin clicks download
-> UI opens export confirmation modal
-> UI posts current filter state to /send-logs-other/export
-> Backend validates module access
-> Backend creates BatchManagement job with class_name mail-history-step and method export
-> UI opens server-processing-another
```

## Flow: Update Notification Setting

```text
Admin opens /setting-emails route
-> UI gets /api/v1/mail-history/admin/notification/setting
-> UI edits destination profile items, employee modification permission, or retiree send flag
-> UI puts changed subset to /api/v1/mail-history/admin/notification/setting
-> Backend merges provided fields into EmailNotificationSetting
-> Backend saves pp_tenant_settings.key = email_notification_setting
```

## Flow: Bounce Event

```text
External bounce source posts /api/mail-history/admin/bounce-logs
-> Controller validates authorization header against static token
-> Controller parses SNS-like data.Message JSON
-> Controller extracts original People email header
-> Service records pp_email_bounces
-> Repository updates matching pp_email_managements row to BOUNCE when possible
```
