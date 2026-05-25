# UI Map

## Vue App

| File | Purpose |
|---|---|
| `main.js` | App bootstrap |
| `App.vue` | Root app shell |
| `router/router.js` | History mode routes under `/mail-history/admin/` |
| `layout/Layout.vue` | Shared layout, sidebar, redirect to first menu |
| `api/apiMap.js` | API endpoint map |
| `store/application.js` | TODO setting state/actions |
| `i18n.js` and `locales/*.json` | Module translations |

## Routes And Components

| Route | Component | Notes |
|---|---|---|
| `/` | `Layout.vue` | Redirects to first visible menu |
| `/history-others` | `Table/ListEmailHistoryOther.vue` | Main visible history list |
| `/setting-notification` | `Notification/NotificationSetting.vue` | Visible settings screen |
| `/setting-emails` | `SettingEmail/EmailSetting.vue` | Route exists, sidebar menu commented |

## Main History Components

| Component | Purpose |
|---|---|
| `ListEmailHistoryOther.vue` | Fetches modules and mail logs, controls pagination/filter/export |
| `EmailOtherDetailHeader.vue` | Current list header |
| `EmailOtherDetailRow.vue` | Current list row |
| `ModalFilterEmailOtherList.vue` | Filter modal and date/time validation |
| `ModalExportData.vue` | Export confirmation modal |
| `TabSorter.vue` | Status filter tabs |
| `SortHeader.vue` | Filter chip area |
| `SortLimit.vue` | Page-size selector |
| `TableFooter.vue` | Pagination footer |

## Important UI Constraints

- `ListEmailHistoryOther.vue` stores query params in the URL for filters except page/pageSize.
- The filter modal only emits when the form is active/valid.
- Date and time must be set together.
- Start date cannot be older than 89 days from current date.
- Export button is disabled visually when the current list is empty.
- `EmailOtherDetailRow.vue` renders subject and message with `v-html`; backend/source content must be treated carefully.
