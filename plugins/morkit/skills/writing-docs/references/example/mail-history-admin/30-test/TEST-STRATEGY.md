# Test Strategy

## Existing Test Coverage Found

Existing MailHistory tests are mostly domain/application-level:

- `app/Test/Case/people/Core/ApplicationService/MailHistory/EmailSendingServiceTest.php`
- `app/Test/Case/people/Core/Domain/Model/MailHistory/EmailMessageTest.php`
- `app/Test/Case/people/Core/Domain/Model/MailHistory/EmailNotificationSettingTest.php`
- `app/Test/Case/people/Core/Domain/Model/MailHistory/EmployeeEmailSettingTest.php`
- `app/Test/Case/people/Core/Domain/Model/MailHistory/ProfileItemIDTest.php`

No direct controller tests for `ApiMailHistoryAdmin*` were found during source review.

## Priority Test Areas

| Area | Risk | Preferred Coverage |
|---|---|---|
| Access-control module filtering | Data leakage | Service/repository tests with visible and invisible module ids |
| `send-logs-other` filters | Incorrect or missing records | Repository/query tests for status/date/subject/mail/name |
| Export reservation | Wrong export data | Service test verifying serialized batch options |
| Notification setting update | Silent setting loss | Domain/service tests for partial payload updates |
| Bounce webhook | Incorrect mutation/security | Controller/service tests for token, original header, matching row |
| Vue filter validation | Bad queries | Unit tests for modal validation if frontend test setup is available |

## Manual Test Focus

- User with access control sees only permitted related applications.
- Export result matches list filters.
- Date/time filter refuses incomplete pairs.
- Email destination setting preserves fields not submitted by the current form.
- Bounce status appears as `BOUNCE` in history after webhook processing.
