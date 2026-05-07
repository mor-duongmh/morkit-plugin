<!--
Screen Spec Template — 1 file per screen
Filename: screen-specs/SCREEN-{NNN}-{kebab-slug}.md
Format: Markdown, single-language (JP | EN | VN).
Source: SRS Appendix A index → expand vào file riêng.

Mockup workflow:
  1. User cung cấp ảnh: assets/screens/SCREEN-{NNN}-{slug}.png
  2. Skill dùng Claude vision (Read tool) → extract items + bbox
  3. Pillow annotate số thứ tự lên ảnh → assets/screens/SCREEN-{NNN}-{slug}-annotated.png
  4. Số trên ảnh khớp cột # trong tables §3
-->

# SCREEN-{{SCREEN_ID}}: {{SCREEN_NAME}}

| Field | Value |
|---|---|
| Screen ID | SCREEN-{{NNN}} |
| 画面名 / Screen Name | {{SCREEN_NAME}} |
| 関連FR / Related FR | FR-{{NNN}}, FR-{{NNN}} |
| アクセス権 / Access Role | {{ROLE}} (admin / user / guest) |
| URL / Route | {{URL_PATH}} |
| 親画面 / Parent | SCREEN-{{NNN}} |
| 子画面 / Children | SCREEN-{{NNN}}, SCREEN-{{NNN}} |
| 優先度 / Priority | High / Mid / Low |
| Version | {{VERSION}} |

---

## 1. 概要 / Overview

{{SCREEN_PURPOSE}}

**ユーザーゴール / User Goal:** {{USER_GOAL}}
**前提 / Pre-condition:** {{PRECONDITION}}
**事後 / Post-condition:** {{POSTCONDITION}}

---

## 2. レイアウト / Layout

### 2.1 Mockup (annotated)

![SCREEN-{{NNN}}-{{slug}}](../assets/screens/SCREEN-{{NNN}}-{{slug}}-annotated.png)

> Annotated từ original: `../assets/screens/SCREEN-{{NNN}}-{{slug}}.png`
> Số trên ảnh tương ứng với cột `#` trong các bảng items dưới đây.
> Color code: 🔵 input | 🟠 button | ⚪ label/output | 🟢 table/chart

### 2.2 Layout Description
{{LAYOUT_DESCRIPTION_FROM_VISION}}

### 2.3 Responsive Breakpoints

| Breakpoint | Layout Behavior |
|---|---|
| ≥1280px (Desktop) | Sidebar fixed, 2-column |
| 768-1279px (Tablet) | Sidebar collapsible |
| <768px (Mobile) | Single column, hamburger menu |

---

## 3. 入出力項目 / Input/Output/Action Items

> Cột `#` khớp số đánh dấu trên ảnh annotated ở §2.1.

### 3.1 Input Items 🔵

| # | ラベル / Label | Component | Type | 必須 / Required | デフォルト / Default | 検証 / Validation | エラーCode | 備考 / Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | {{LABEL}} | TextField | string | Y | - | RFC 5322, max 255 | E-IN-001 | Email login |
| 2 | {{LABEL}} | TextField | password | Y | - | min 8 chars, mixed | E-IN-002 | Masked |
| 3 | {{LABEL}} | DatePicker | date | N | today | yyyy-MM-dd | E-IN-003 | |

### 3.2 Output / Display Items ⚪

| # | ラベル / Label | Component | Source | Format | 備考 / Notes |
|---|---|---|---|---|---|
| 4 | {{LABEL}} | Label | API GET /users/{id}.name | text | |
| 5 | {{LABEL}} | Table | API GET /orders | paginated 20/page | Sortable: created_at |

### 3.3 Action / Buttons 🟠

| # | ラベル / Label | Type | 動作 / Behavior | API Call | Permission |
|---|---|---|---|---|---|
| 6 | Sign In / ログイン | Primary | Submit form | POST /api/login | guest |
| 7 | Cancel / キャンセル | Secondary | Discard, back | - | user |
| 8 | Delete / 削除 | Danger | Confirm modal → DELETE | DELETE /users/{id} | admin |

---

## 4. 画面遷移 / Transitions

```mermaid
flowchart LR
    PREV[SCREEN-000<br/>Previous] -->|"Click {{action}}"| THIS[SCREEN-{{NNN}}<br/>{{SCREEN_NAME}}]
    THIS -->|"Save success"| NEXT_OK[SCREEN-002<br/>Confirmation]
    THIS -->|"Cancel"| BACK[SCREEN-000<br/>Previous]
    THIS -->|"Validation error"| THIS
    THIS -->|"Server error"| ERROR[SCREEN-999<br/>Error Page]
```

| Trigger | From | To | Condition | Method |
|---|---|---|---|---|
| Initial load | SCREEN-000 | SCREEN-{{NNN}} | Auth OK | GET render |
| Save success | SCREEN-{{NNN}} | SCREEN-002 | API 200 | Redirect |
| Cancel | SCREEN-{{NNN}} | SCREEN-000 | - | Browser back |
| Server error | SCREEN-{{NNN}} | SCREEN-999 | API 5xx | Replace |

---

## 5. 業務ロジック / Business Logic

### 5.1 On Load
1. Check authentication → if missing → redirect SCREEN-000 (Login)
2. Fetch user profile: `GET /api/users/me`
3. Populate form defaults from response
4. Hide admin-only actions if `role !== 'admin'`

### 5.2 On Submit (ACT-001)
1. Client-side validation cho IN-001 ~ IN-003
2. If invalid → show inline error, focus first invalid field
3. If valid → disable buttons, show spinner
4. Call `POST /api/users` với payload
5. On 200/201 → redirect SCREEN-002 (success)
6. On 400 → show field-level errors từ response
7. On 5xx → show toast "Server error", re-enable buttons

### 5.3 Conditional Display
- Field IN-003 chỉ hiển thị khi IN-002 = "Type B"
- Action ACT-003 chỉ hiện với role = `admin`

---

## 6. エラーハンドリング / Error Handling

| Error Code | Trigger | Display Type | Message | Recovery |
|---|---|---|---|---|
| E-IN-001 | IN-001 validation | Inline | "メールアドレスの形式が正しくありません" | Re-input |
| E-API-401 | API returns 401 | Modal | "Session expired. Please login again." | Redirect SCREEN-000 |
| E-API-500 | API returns 5xx | Toast | "Server error. Please retry." | Manual retry |
| E-NETWORK | Network timeout | Toast | "ネットワークエラー" | Auto-retry x3 |

---

## 7. 非機能要件 / Non-Functional Requirements (Screen-specific)

| Item | Requirement |
|---|---|
| Initial render | < 2s @ 3G mobile |
| Form submit response | < 500ms p95 |
| Accessibility | WCAG 2.1 AA |
| Keyboard navigation | Tab order defined; Enter = Save; Esc = Cancel |
| i18n | JP / EN / VN (depends on user preference) |
| Browser support | Chrome 90+, Edge 90+, Safari 14+, Firefox 88+ |

---

## 8. テスト観点 / Test Considerations

- [ ] All required fields show error when empty
- [ ] Email field rejects malformed input (test cases: `abc`, `abc@`, `@xyz.com`)
- [ ] Save button disabled until form valid
- [ ] Cancel discards changes without prompt if no edit; with prompt if edited
- [ ] Auth redirect works when token expired mid-session
- [ ] Mobile breakpoint renders correctly at 375px width
- [ ] Tab order matches visual order

---

## 9. 関連ファイル / Related Files

- SRS: [../srs.md](../srs.md) (Appendix A index)
- API: [../api-docs.md](../api-docs.md) — endpoints used: {{ENDPOINTS_LIST}}
- DB: [../database-design.md](../database-design.md) — tables touched: {{TABLES_LIST}}
- Mockup asset: `assets/SCREEN-{{NNN}}-mockup.png`
- Figma: {{FIGMA_URL}}

---

## 10. 変更履歴 / Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | {{DATE}} | {{BRSE_NAME}} | Initial |
