<!--
API Docs Template — Markdown chuẩn cho output skill
Format: Markdown, hỗ trợ JP / EN / VN (placeholder {{LANG}} replace bởi skill)
Mỗi endpoint = 1 sub-section, có Request/Response/Errors/Example.
-->

# API Documentation — {{PROJECT_NAME}}

| Field | Value |
|---|---|
| Version | {{API_VERSION}} |
| Base URL | {{BASE_URL}} |
| Date | {{DATE}} |
| Auth | {{AUTH_TYPE}} (Bearer / OAuth2 / API Key) |
| Language | {{LANG}} |

---

## 1. Overview / 概要

{{API_OVERVIEW}}

**Conventions:**
- All requests/responses are JSON unless noted.
- Timestamps: ISO 8601 UTC (`2026-05-03T10:00:00Z`).
- IDs: UUID v4 strings.
- Pagination: cursor-based (`?cursor=...&limit=20`).

---

## 2. Authentication / 認証

### 2.1 Method
{{AUTH_DESCRIPTION}}

```http
Authorization: Bearer <ACCESS_TOKEN>
```

### 2.2 Get Access Token
- Endpoint: `POST {{BASE_URL}}/auth/token`
- Body: `{ "client_id": "...", "client_secret": "..." }`
- Returns: `{ "access_token": "...", "expires_in": 3600 }`

---

## 3. Global Error Codes / グローバルエラーコード

| Code | HTTP Status | Meaning (EN) | 意味 (JA) | Tiếng Việt |
|---|---|---|---|---|
| BAD_REQUEST | 400 | Validation failed | 入力エラー | Sai định dạng |
| UNAUTHORIZED | 401 | Missing/invalid auth | 認証エラー | Chưa xác thực |
| FORBIDDEN | 403 | No permission | 権限なし | Không có quyền |
| NOT_FOUND | 404 | Resource not found | リソースなし | Không tìm thấy |
| CONFLICT | 409 | State conflict | 競合エラー | Xung đột trạng thái |
| RATE_LIMITED | 429 | Too many requests | レート制限 | Vượt giới hạn |
| INTERNAL_ERROR | 500 | Server error | サーバーエラー | Lỗi server |

**Error Response Format:**

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable message",
  "details": [
    { "field": "email", "issue": "Invalid format" }
  ],
  "request_id": "req_abc123"
}
```

---

## 4. Rate Limiting / レート制限

| Tier | Limit | Window |
|---|---|---|
| Free | 60 req | 1 min |
| Pro | 1000 req | 1 min |

Headers returned: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

---

## 5. Endpoints / エンドポイント

### 5.1 {{RESOURCE_NAME}} (e.g. Users)

#### 5.1.1 List {{RESOURCE_NAME}}

`GET {{BASE_URL}}/{{resource}}`

**Description:** {{DESCRIPTION}}
**Auth:** Required ({{ROLE}})
**Related FR:** FR-001

**Query Parameters:**

| Param | Type | Required | Default | Description |
|---|---|---|---|---|
| cursor | string | N | - | Pagination cursor |
| limit | int | N | 20 | Max 100 |
| sort | enum | N | created_at_desc | created_at_asc, name_asc, ... |

**Response 200:**

```json
{
  "data": [
    {
      "id": "uuid-1234",
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2026-05-03T10:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6...",
    "has_more": true
  }
}
```

**Errors:** `UNAUTHORIZED`, `BAD_REQUEST`, `RATE_LIMITED`

**cURL:**

```bash
curl -X GET "{{BASE_URL}}/{{resource}}?limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

---

#### 5.1.2 Get {{RESOURCE_NAME}} by ID

`GET {{BASE_URL}}/{{resource}}/{id}`

**Path Parameters:**

| Param | Type | Required | Description |
|---|---|---|---|
| id | UUID | Y | Resource ID |

**Response 200:**

```json
{
  "id": "uuid-1234",
  "name": "John Doe"
}
```

**Errors:**

| Code | Status | Description |
|---|---|---|
| NOT_FOUND | 404 | ID không tồn tại |
| UNAUTHORIZED | 401 | Missing token |

---

#### 5.1.3 Create {{RESOURCE_NAME}}

`POST {{BASE_URL}}/{{resource}}`

**Request Body:**

```json
{
  "name": "John Doe",
  "email": "john@example.com"
}
```

| Field | Type | Required | Validation | Description |
|---|---|---|---|---|
| name | string | Y | 1-255 chars | Full name |
| email | string | Y | RFC 5322 | Unique |

**Response 201:**

```json
{
  "id": "uuid-1234",
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2026-05-03T10:00:00Z"
}
```

**Errors:** `BAD_REQUEST` (validation), `CONFLICT` (email duplicate)

---

#### 5.1.4 Update {{RESOURCE_NAME}}

`PUT {{BASE_URL}}/{{resource}}/{id}` — Full replace
`PATCH {{BASE_URL}}/{{resource}}/{id}` — Partial update

[Same structure as Create]

---

#### 5.1.5 Delete {{RESOURCE_NAME}}

`DELETE {{BASE_URL}}/{{resource}}/{id}`

**Response 204:** No content

**Errors:** `NOT_FOUND`, `FORBIDDEN`

---

## 6. Webhooks / ウェブフック

### 6.1 Event Types

| Event | Trigger | Payload |
|---|---|---|
| {{resource}}.created | New record | Full object |
| {{resource}}.updated | Field change | Full object + changes |
| {{resource}}.deleted | Soft delete | `{ id, deleted_at }` |

### 6.2 Payload Format

```json
{
  "event": "users.created",
  "timestamp": "2026-05-03T10:00:00Z",
  "data": { },
  "signature": "sha256=..."
}
```

### 6.3 Signature Verification

```
HMAC-SHA256(payload, webhook_secret) == header X-Signature
```

---

## 7. Changelog / 変更履歴

| Version | Date | Changes |
|---|---|---|
| 1.0 | {{DATE}} | Initial release |

---

## Appendix A: SDKs

| Language | Repo |
|---|---|
| TypeScript | {{TS_SDK_URL}} |
| Python | {{PY_SDK_URL}} |

## Appendix B: OpenAPI Spec

Source of truth: `{{OPENAPI_YAML_URL}}`
