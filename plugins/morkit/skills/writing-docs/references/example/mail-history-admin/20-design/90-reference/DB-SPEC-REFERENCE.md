# DB Spec Reference

Physical schema is not maintained in this module doc. Use these source locations:

- `docker/mysql/data/dmp-people-schema.sql`
- `docker/mysql/ddl/`
- `docker/mysql/dml/`

Relevant schema anchors:

| Table | Schema Anchor |
|---|---|
| `pp_email_managements` | `CREATE TABLE pp_email_managements` |
| `pp_email_bounces` | `CREATE TABLE pp_email_bounces` |
| `pp_mail_history_modules` | `CREATE TABLE pp_mail_history_modules` |
| `pp_mail_history_log_processes` | `CREATE TABLE pp_mail_history_log_processes` |
| `pp_mail_history_log_steps` | `CREATE TABLE pp_mail_history_log_steps` |
| `pp_tenant_settings` | `CREATE TABLE pp_tenant_settings` |

Relevant DML anchors:

- `docker/mysql/dml/*/dml-*.sql` files inserting into `pp_mail_history_modules`
- `docker/mysql/dml/job-posting-v2/dml-71703.sql` for email key migration examples

When a new module's mail should appear in history, check both data areas:

1. `EmailKey::KEYS`
2. `pp_mail_history_modules` DML row and language labels
