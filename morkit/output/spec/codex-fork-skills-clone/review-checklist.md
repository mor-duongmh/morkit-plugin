# Plan Review Checklist — `codex-fork-skills-clone`

> **Human gate.** Tick the items below honestly. Set **Overall Decision: OK** at the
> bottom only when you're satisfied with the plan. Until that happens, the plugin
> blocks `/morkit:executing-plans`, `/morkit:executing-plans`, and
> `/morkit:subagent-driven-development` for this change.

## Meta

- **Change:** `codex-fork-skills-clone`
- **Variant:** BE - Refactor *(auto-detected; override via `--variant` if wrong)*
- **Generated:** 2026-05-18T07:57:03Z
- **Source:** [Mor Developer Review Checklist](https://docs.google.com/document/d/184wY2N2WOUExmZrClvHCfcRCnSQsJYvav6gc6JwL6xc)
- **Files reviewed:**
  - [`proposal.md`](./proposal.md)
  - [`design.md`](./design.md) (if present)
  - [`tasks.md`](./tasks.md)

---

## BE - Refactor

### Mục đích & giới hạn

- [x] Có Motivation cụ thể (tech debt nào, pain point nào, metric nào muốn cải thiện)  
- [x] Có metric thành công đo được (response time, LOC, coverage)  
- [x] Scope nêu rõ: refactor này KHÔNG đổi behavior / API contract / schema

### Đảm bảo không làm hỏng chức năng đang chạy

- [x] Plan đánh giá test coverage hiện tại của module refactor  
- [x] Coverage thấp → plan có bổ sung test TRƯỚC khi refactor  
- [x] Plan chạy full test suite sau mỗi bước  
- [x] Interface public của module KHÔNG breaking change (hoặc đã align với người dùng module)x

### Security

Mục tiêu: đảm bảo các biện pháp bảo mật hiện có **KHÔNG bị bỏ hoặc yếu đi** sau refactor.

#### Authentication / Authorization

- [x] **Auth check KHÔNG bị mất khi chuyển logic giữa các layer** Khi agent di chuyển code từ controller → service, check JWT có còn không? Khi tách function, middleware auth có được apply đúng chỗ không? Lỗi này dễ bị miss khi "dọn code".  
        
- [x] **Authorization check (RBAC, IDOR) KHÔNG bị bypass khi đơn giản hoá code** Code cũ có thể có nhiều lớp check (middleware \+ service \+ repository) — refactor rút gọn không được bỏ lớp quan trọng với lý do "trùng lặp". Defense in depth cố tình có nhiều lớp.  
        
- [x] **Admin route protection KHÔNG bị gỡ guard** Kiểm tra các route `/admin/*` vẫn có guard kiểm tra role sau refactor. Agent đôi khi "dọn middleware" làm mất.

#### Common Attacks

- [x] **SQL Injection — parameterized query / ORM KHÔNG bị thay bằng string-concat** Kiểm tra mọi query sau refactor vẫn dùng ORM hoặc `$1, $2`. Đôi khi agent rewrite query với string template literal cho "đẹp hơn" → tạo lỗ hổng SQL injection.  
        
- [x] **XSS / Input validation — validation rule KHÔNG bị bỏ hoặc làm yếu** DTO / schema validation vẫn đầy đủ sau refactor, không bị đơn giản hóa (ví dụ bỏ regex email, bỏ max length).  
        
- [x] **CSRF — bảo vệ CSRF KHÔNG bị gỡ** Nếu app dùng cookie auth: flag `SameSite` trên cookie vẫn được set; hoặc CSRF token middleware vẫn active sau refactor.

#### Data Protection

- [x] **Password hash / token handling KHÔNG bị downgrade thuật toán** Không đổi bcrypt → sha256 "cho nhanh hơn". Không giảm cost factor bcrypt từ 12 → 8\. Không đổi JWT từ RS256 → HS256 mà không có lý do rõ ràng.  
        
- [x] **Secret handling KHÔNG bị hardcode khi agent "dọn" config** Agent đôi khi đơn giản hoá config bằng cách hardcode giá trị mặc định (`const secret = process.env.JWT_SECRET || "default-secret"` — fallback string là lỗ hổng nếu env var không set).  
        
- [x] **Log redaction KHÔNG bị bỏ khi refactor logging** Nếu code cũ có `logger.info("User login", { email, password: "***" })`, refactor không được đổi thành `logger.info({ email, password })` (log cả password raw).

#### Infrastructure

- [x] **Upgrade dependency: có bước check CVE** Nếu refactor có upgrade thư viện: plan có chạy `npm audit` / `pip-audit` để đảm bảo phiên bản mới không có CVE.  
        
- [x] **Security headers / CORS config KHÔNG bị thay đổi / nới lỏng** Helmet config, CORS origin list không bị sửa thành dễ dãi hơn (ví dụ CORS `*` vì "refactor cho đơn giản").

### Tác động

- [x] Liệt kê consumer (service / team khác) đang dùng module  
- [x] Có feature flag / gradual rollout nếu thay đổi lớn  
- [x] Có rollback plan

### Chi tiết việc plan thực thi

- [x] Mọi task có Steps đánh số rõ ràng  
- [x] Mọi Step có code snippet / command cụ thể  
- [x] Mọi task có verify step \+ commit

### Review Summary

\- Section có Fail: Không

\- Critical Issues: Không

\- Major Issues: Không

\- Minor Issues: 5 open questions trong design.md (vocab `Bash tool`, gate matcher rộng, drift mtime vs hash, commands-codex minimal, CI guard job) — accept để resolve trong Phase 2/4 thay vì block plan

\- Câu hỏi muốn bàn lại với agent: Không (đã chốt qua AskUserQuestion: commands clone mirror, hooks-codex với matcher apply_patch|Edit|Write, drift CI vào Phase 1)

\- Quyết định: OK

---

Reviewed by: user (2026-05-18) — confirmed via interactive review flow.

---

## Overall Decision

Overall Decision: OK

### Notes / questions for the agent
