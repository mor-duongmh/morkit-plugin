# Mail History Admin Architecture

## Purpose

`mail-history-admin` provides administrator screens for reviewing mail delivery state and changing notification-related settings.

## Runtime Structure

```text
Browser
  Vue 2 SPA: app/vue/src/mail-history-admin
    router.js
    apiMap.js
    components/Table/*
    components/Notification/*
    components/SettingEmail/*

CakePHP 2
  MailHistoryAdminController
  AppApiBaseController-based API controllers
  People\Core\Application\MailHistory services
  People\Core\Domain\Model\MailHistory objects
  Cake2 repositories/query services

Database
  pp_email_managements
  pp_email_bounces
  pp_mail_history_modules
  pp_mail_history_log_processes
  pp_mail_history_log_steps
  pp_tenant_settings
```

## Page Mounting

`MailHistoryAdminController` uses `people_page_vue_share` layout. The view `app/View/people/MailHistoryAdmin/index.ctp` includes `vue/mail_history_admin_js`.

The generated element is produced from `app/vue/vue.config.js`:

- development filename: `mail-history-admin.html`
- production ctp target: `app/View/people/Elements/vue/mail_history_admin_js.ctp`

## Frontend Routing

Vue router base:

```text
{company}mail-history/admin/
```

Routes:

| Route | Component | Current Menu |
|---|---|---|
| `/history-others` | `ListEmailHistoryOther.vue` | Visible |
| `/setting-notification` | `NotificationSetting.vue` | Visible |
| `/setting-emails` | `EmailSetting.vue` | Hidden/commented |

When the route path is `/`, `Layout.vue` redirects to the first visible menu, currently `/history-others`.

## Backend Routing

Backend routes live in `app/Config/routes.php` under `// メール通知履歴`.

Important routes:

- `GET /api/v1/mail-history/admin/processes/page`
- `GET /api/v1/mail-history/admin/send-logs-other`
- `POST /api/v1/mail-history/admin/send-logs-other/export`
- `GET|PUT /api/v1/mail-history/admin/todos/setting`
- `GET|PUT /api/v1/mail-history/admin/notification/setting`
- `POST /api/mail-history/admin/bounce-logs`

## Service Pattern

Controllers are thin:

1. Read request query/data.
2. Populate command objects.
3. Instantiate concrete repositories/query services.
4. Call application service.
5. Encode `IResult::toArray()` as JSON.

This module does not use dependency injection containers in these controllers.

## Access Control

History module visibility is calculated in `MailSendLogQueryService`.

When access control is applied:

```text
getModulesByAccessControl()
-> filterAccessibleModules($modules, $user)
```

Otherwise:

```text
getModules()
```

Filtering services validate requested `moduleId` against the visible module set before querying or exporting.
