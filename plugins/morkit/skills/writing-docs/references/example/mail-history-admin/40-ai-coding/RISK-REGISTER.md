# Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Access-control regression | Admin may view/export unauthorized module history | Test allowed and denied `moduleId` paths in list/export services |
| Legacy route accidental removal | Existing hidden caller may break | Search routes, frontend links, and server logs before removal |
| Current/legacy data source confusion | Feature implemented against wrong table | Use `SEND-LOG-OTHER-SYS-SPEC.md` for current UI |
| Notification setting partial update regression | Existing settings overwritten by absent fields | Add tests around `NotificationSettingCommand` and `UpdateNotificationSettingService` |
| Batch export args drift | Export job fails or ignores filters | Keep docs and executor args synchronized |
| Bounce parsing assumptions | Webhook payload changes can break processing | Validate payload shape and handle missing optional fields defensively |
| Hard-coded status labels | Localization issues | Move labels to i18n only as a planned refactor with UI review |
