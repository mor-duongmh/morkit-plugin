# Known Pitfalls

| Pitfall | Why It Happens | How To Avoid |
|---|---|---|
| Confusing current and legacy history tables | Both systems exist in source | Use `pp_email_managements` for current `history-others`; treat `pp_mail_history_log_*` as legacy |
| Adding only `pp_mail_history_modules` row | Current logs map from `email_key` through `EmailKey::KEYS` | Update both DB DML and `EmailKey::KEYS` |
| Data leakage through export | Export accepts filters separately from list request | Repeat module access validation in export service |
| Losing notification setting fields | UI sends partial payloads | Preserve nullable command behavior and merge into existing/default setting |
| Breaking hidden `setting-emails` route | Menu is commented but route still exists | Check route/component before deleting |
| Unescaped HTML display | Row renders `subject` and `message` via `v-html` | Treat source content carefully; prefer sanitized text if changing rendering |
| Mismatched page size defaults | Backend defaults to 20 while UI initializes 10 | Ensure UI sends pageSize or intentionally align defaults |
| Export option rename breaks batch | Batch args are serialized and consumed elsewhere | Find batch executor before renaming fields |
| Bounce token hard-coded in controller | Webhook auth is implemented locally | Do not expose/change token handling casually; consider config migration as separate work |
| `REGEX_DATE` import mismatch | `ListEmailHistoryOther.vue` and `NotificationSetting.vue` import `REGEX_DATE`, but `constants/index.js` currently does not export it | Check the build before touching constants/imports; remove unused imports or add the missing export as a separate code fix |
| Current row key mismatch | Backend returns `stepId`, while `ListEmailHistoryOther.vue` uses `item.id` as Vue key | Verify row identity before changing list rendering or response shape |
