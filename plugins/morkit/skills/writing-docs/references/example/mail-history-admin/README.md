# Mail History Admin Documentation

This directory is the documentation entrypoint for the `mail-history-admin` module.

The module provides the administrator UI for mail notification history, related mail log filtering/export, and notification-related settings. It is a Vue SPA mounted by a CakePHP page controller and backed by API controllers under `app/Controller/api/People/MailHistoryAdmin`.

## Canonical Docs

- Overview and read order: `00-overview/DOCUMENT-MAP.md`
- Scope: `00-overview/SCOPE.md`
- Source map: `00-overview/SOURCE-MAP.md`
- Design map: `20-design/DESIGN-MAP.md`
- AI coding guide: `40-ai-coding/AI-CODING-GUIDE.md`
- Test runbook: `30-test/TEST-RUNBOOK.md`

## Main Source Locations

| Layer | Path | Notes |
|---|---|---|
| Page route | `app/Config/routes.php` | `/mail-history/admin/*` and related API routes |
| Page controller | `app/Controller/people/MailHistoryAdminController.php` | Renders the Vue shell |
| CakePHP view | `app/View/people/MailHistoryAdmin/index.ctp` | Includes generated Vue bundle element |
| Vue app | `app/vue/src/mail-history-admin/` | SPA source |
| Vue build config | `app/vue/vue.config.js` | `mail_history_admin` entry and generated ctp target |
| API controllers | `app/Controller/api/People/MailHistoryAdmin/` | Mail history admin API entrypoints |
| Application services | `app/Lib/people/Core/Application/MailHistory/` | Use-case orchestration |
| Domain model | `app/Lib/people/Core/Domain/Model/MailHistory/` | Mail history entities, commands, results |
| Repositories | `app/Lib/people/Core/Infrastructure/Cake2/MailHistory/` | Writes and batch reservation |
| Query services | `app/Lib/people/Core/Infrastructure/Cake2Query/MailHistory/` | Read-side module/log queries |
| Email key map | `app/Lib/people/ValueObject/EmailKey.php` | Maps email keys to mail history module ids |
| Tests | `app/Test/Case/people/Core/.../MailHistory/` | Existing domain/application tests |

## Recommended Read Order For AI Agents

1. `00-overview/SOURCE-MAP.md`
2. `20-design/DESIGN-MAP.md`
3. `20-design/10-features/SEND-LOG-OTHER-SYS-SPEC.md`
4. `20-design/10-features/NOTIFICATION-SETTING-SYS-SPEC.md`
5. `40-ai-coding/AI-CODING-GUIDE.md`
6. `30-test/TEST-RUNBOOK.md`

## Current State Notes

- The visible sidebar currently links to `history-others` and `setting-notification`.
- `setting-emails` has a Vue route and component, but the menu item is commented out.
- `/api/v1/mail-history/admin/processes/:processId/steps` routes are marked `削除予定` in `routes.php`; treat them as legacy unless the product requirement says otherwise.
