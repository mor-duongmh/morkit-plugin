# Scope

## In Scope

`mail-history-admin` covers the administrator-facing mail history UI and the API/use-case code directly supporting it.

In scope:

- Page route `/mail-history/admin/*`
- Vue SPA under `app/vue/src/mail-history-admin`
- Mail history list for records stored in `pp_email_managements`
- Filtering by related application, status, date/time, subject, email address, and employee name
- Export reservation for filtered mail history data
- Notification setting read/update through `email_notification_setting`
- Header TODO deletion setting read/update through `/todos/setting`
- Account notification target count and send trigger used by the notification setting screen
- Bounce log webhook route `/api/mail-history/admin/bounce-logs`
- Legacy process/step history APIs while routes still exist

## Out Of Scope

Out of scope:

- The business modules that create mail records, such as workflow, job posting, evaluation 360, static MBO, and others
- Mail template authoring and localization outside the mail history admin UI
- SQS/worker infrastructure beyond how this module reserves exports and records bounce status
- Full API contract docs for unrelated account notification endpoints
- Generated Vue bundle ctp files when not present in the working tree

## Feature Boundaries

`mail-history-admin` reads and displays mail activity. It should not decide whether a business module should send a mail. Sending rules belong to the source module or shared mail services.

`mail-history-admin` may filter visible modules by access control. It should not bypass `UserSingleton::getInstance()->isAppliedAccessControl()` checks in the application services.

## Legacy Boundary

The old process/step API routes under `/api/v1/mail-history/admin/processes/:processId/steps` are marked as planned for deletion in `app/Config/routes.php`. Keep docs for them so agents do not accidentally remove or revive behavior without a product decision.
