# Data Map

## Current History Tables

### `pp_email_managements`

Current source for the visible `history-others` list.

Important columns:

| Column | Purpose |
|---|---|
| `id` | Mail management row id |
| `email_key` | Maps to module id through `EmailKey::KEYS` |
| `unique_id` | Source module identity for the mail |
| `to` | Legacy recipient email |
| `resend_count` | Duplicate-send discriminator |
| `subject` | Mail subject |
| `params` | JSON payload, including modern `to` recipient array |
| `status` | Numeric email status |
| `valid_from` | Scheduled send availability |
| `sent_at` | Send timestamp |
| `remarks` | Error/bounce remarks |
| `created` | Used as send/history datetime in current list |

Unique key:

```text
(email_key, unique_id, to, resend_count)
```

### `pp_email_bounces`

Stores bounce webhook messages.

Important columns:

- `email_key`
- `unique_id`
- `to`
- `bounce_at`
- `message`
- `subject`

## Module Mapping Tables

### `pp_mail_history_modules`

Maps module ids to localized menu labels.

Important columns:

- `id`
- `label_model`
- `label_field`
- `label_foreign_key`

### `languages`

Used by query services to resolve display names for `pp_mail_history_modules`.

## Legacy History Tables

### `pp_mail_history_log_processes`

Legacy process-level history.

Important columns:

- `module_id`
- `start_date`
- `end_date`
- `status`
- `content`
- `target_count`
- `success_count`
- `error_count`
- `unregistered_count`
- `additional_info` was added later by DDL.

### `pp_mail_history_log_steps`

Legacy recipient-level process history.

Important columns:

- `process_id`
- `module_id`
- `pp_employee_id`
- `start_date`
- `end_date`
- `status`
- `error_message`
- `employee_code`
- `last_name`
- `first_name`
- `mail`

## Settings Table

### `pp_tenant_settings`

Notification destination settings use:

```text
key = email_notification_setting
json = EmailNotificationSetting::toArray()
```

## Data Ownership

`mail-history-admin` owns the read/display and setting behavior, but most `pp_email_managements` rows are created by other modules through shared mail reservation/sending services.
