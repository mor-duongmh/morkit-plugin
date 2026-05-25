# Code Search Guide

## Find Module Entrypoints

```bash
rg -n "mail-history/admin|MailHistoryAdmin|mail_history_admin" app/Config app/Controller app/View app/vue/src
```

## Find Current History List Flow

```bash
rg -n "send-logs-other|MailOtherSendLog|findOtherMailSendLogs|MailHistoryOtherStep" app/vue/src/mail-history-admin app/Controller app/Lib/people/Core
```

## Find Notification Setting Flow

```bash
rg -n "notification/setting|NotificationSettingCommand|EmailNotificationSetting|email_notification_setting" app/vue/src/mail-history-admin app/Controller app/Lib/people/Core
```

## Find Module Mapping

```bash
rg -n "EmailKey::KEYS|pp_mail_history_modules|findModuleIdFromEmailKey|getEmailKeyByModuleId" app/Lib docker/mysql
```

## Find Bounce Handling

```bash
rg -n "bounce-logs|Bounce|saveBouncedMail|updateEmailManagement|pp_email_bounces" app/Controller app/Lib/people/Core docker/mysql
```

## Find Legacy Process/Step Code

```bash
rg -n "processes/:processId/steps|MailHistoryStepList|findSendLogs|pp_mail_history_log_steps" app/Config app/Controller app/Lib/people/Core app/vue/src/mail-history-admin
```
