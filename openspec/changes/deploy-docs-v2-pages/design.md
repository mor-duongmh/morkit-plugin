## Context

Repo `mor-duongmh/claude-plugins` chứa marketplace plugin `morkit` với 22 skills + 15 commands + 9 agents. Folder `docs/` đã có 2 thế hệ landing:

- **v1** (PR #21 đã merge): `docs/index.html` (README-mirror), `docs/docs.html` (use cases storytelling).
- **v2** (mới, chưa publish): `docs/index-v2.html` (claudekit-style docs hub với sidebar nav, dark theme), `docs/docs-v2.html` (refresh layout). Cả hai đều dùng chung folder `docs/commands/` (15 file) + `docs/skills/` (26 file).

Hiện tại GitHub Pages chưa enable; người dùng chỉ thấy docs khi clone repo. README.md root liệt kê command/skill bằng bảng text, không có link "Live demo".

Stakeholders:
- **Mor team** (owner): muốn marketing landing chất lượng để khoe lên cộng đồng Claude Code.
- **Người dùng mới**: cần xem demo nhanh trước khi quyết định `/plugin install`.

Constraints:
- Cần admin quyền repo để enable Pages (one-time, qua UI hoặc API).
- Pages user-repo URL cố định: `https://mor-duongmh.github.io/claude-plugins/`.
- Không có build pipeline — HTML check thẳng vào git, Pages serve tĩnh.

## Goals / Non-Goals

**Goals:**
- v2 trở thành landing mặc định khi truy cập `https://mor-duongmh.github.io/claude-plugins/`.
- Loại bỏ v1 file rác khỏi `docs/` (yêu cầu user: "chỉ deploy v2, loại bỏ v1").
- README root có link rõ ràng tới live site.
- Internal link giữa các trang v2 hoạt động đúng sau rename.
- Không phá `docs/commands/*.html` và `docs/skills/*.html` (chúng đã đúng path).

**Non-Goals:**
- Không thêm custom domain (CNAME) — dùng URL `*.github.io` mặc định.
- Không setup GitHub Actions workflow build — Pages serve thẳng từ `/docs` (user đã chọn).
- Không refactor lại nội dung v2 — chỉ rename file + sửa internal link.
- Không thêm analytics, search, sitemap — out of scope cho deploy đầu tiên.
- Không cập nhật content trong `docs/commands/*.html` hoặc `docs/skills/*.html`.

## Decisions

### D1: Promote v2 bằng cách rename → `index.html` / `docs.html` (overwrite v1)

**Chọn**: `git mv docs/index-v2.html docs/index.html` và `git mv docs/docs-v2.html docs/docs.html` (overwrite v1).

**Alternatives đã cân nhắc**:
- (A) Giữ v2 ở subfolder `docs/v2/`: Pages link sẽ là `…/v2/`, README phải link sâu, v1 vẫn tồn tại tại root → vi phạm yêu cầu "loại bỏ v1".
- (B) Giữ suffix `-v2`, README link tới `index-v2.html`: URL xấu, v1 vẫn served tại `/`.
- (C) Rename + overwrite v1: URL gọn (`/`), v1 biến mất hoàn toàn. ✓ Chọn.

**Rationale**: User chọn "loại bỏ v1" + "Pages từ main /docs". Lựa chọn C cho URL ngắn nhất và sạch nhất.

### D2: Sửa internal link `docs-v2.html` → `docs.html` trong `index.html` mới

**Chọn**: Grep + replace toàn bộ reference `docs-v2.html` trong `docs/index-v2.html` (trước rename, hoặc sau rename trên `docs/index.html`) thành `docs.html`.

**Why**: Sau khi rename `docs-v2.html` → `docs.html`, các link `<a href="docs-v2.html">` sẽ 404. Tìm thấy 2 reference ở dòng 289 và 322 (sidebar + hero CTA).

### D3: Enable Pages thủ công qua GitHub UI/API, không qua workflow

**Chọn**: Thủ công enable một lần qua Settings → Pages, source = `main` branch, folder = `/docs`. Hoặc dùng `gh api -X POST /repos/mor-duongmh/claude-plugins/pages -f source[branch]=main -f source[path]=/docs`.

**Alternatives**:
- (A) `.github/workflows/deploy-docs.yml` push lên `gh-pages`: User đã từ chối.
- (B) Manual enable: ✓ Chọn. One-time setup, sau đó mỗi push lên `main` tự rebuild.

### D4: README link format

**Chọn**: Thêm section "🌐 Live site" hoặc badge ở đầu README, ngay sau title, dạng:
```markdown
**Live**: https://mor-duongmh.github.io/claude-plugins/
```
Và một badge shield.io ở header (cạnh License) để discoverability.

**Why**: User yêu cầu "update link live server vào readme.md ở root". Đặt high-up để nhìn thấy ngay.

### D5: Verification chiến lược

**Chọn**: Sau khi enable Pages + push, đợi 1-2 phút rồi `curl -sI https://mor-duongmh.github.io/claude-plugins/` kiểm tra HTTP 200. Cũng curl một trang con (`/commands/propose.html`) để xác nhận asset serve.

## Risks / Trade-offs

- **[Risk] Pages build chậm hoặc thất bại sau push.** → Mitigation: chạy `gh api /repos/mor-duongmh/claude-plugins/pages/builds/latest` xem status; nếu fail, đọc log và fix (thường là path sai hoặc Jekyll conflict).
- **[Risk] Jekyll xử lý ngầm có thể bỏ qua file/folder bắt đầu bằng `_` (như `docs/_scaffolder/`).** → Mitigation: thêm `docs/.nojekyll` (empty file) để disable Jekyll, serve file tĩnh y nguyên.
- **[Risk] Internal link còn sót `docs-v2.html` sau rename → 404.** → Mitigation: grep recursive `docs/` sau rename, đảm bảo không còn match `docs-v2.html`.
- **[Trade-off] Bookmark `/index-v2.html` cũ vỡ.** → Chấp nhận, vì site chưa public.
- **[Trade-off] Không có analytics/SEO setup.** → Defer sang change sau, không block deploy.
- **[Risk] User chưa có quyền admin repo để enable Pages.** → Mitigation: tasks.md list rõ bước này; nếu cần, document command `gh` để team có quyền chạy.

## Migration Plan

1. Branch off `main`: `feat/deploy-docs-v2-pages`.
2. `git rm docs/index.html docs/docs.html` (v1 cũ).
3. `git mv docs/index-v2.html docs/index.html`, `git mv docs/docs-v2.html docs/docs.html`.
4. Edit `docs/index.html`: replace `docs-v2.html` → `docs.html` (2 occurrences).
5. Touch `docs/.nojekyll` (empty file).
6. Update root `README.md`: thêm live link/badge.
7. Commit + push + open PR.
8. Sau merge: enable Pages qua Settings hoặc `gh api`.
9. Verify HTTP 200 trên live URL + 1 trang con.
10. Nếu fail: rollback bằng revert PR; Pages tiếp tục serve commit cũ.

**Rollback**: revert PR và (optionally) `gh api -X DELETE /repos/mor-duongmh/claude-plugins/pages` để tắt Pages.
