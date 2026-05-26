# Phase 01 — Đóng băng docs hiện tại → v1.0.0

**Mục tiêu:** Lưu nguyên trạng site đang publish (stale, mô tả docs-hero) thành snapshot lịch sử
`docs/v1.0.0/` TRƯỚC khi sửa root. Đây là bản history trung thực ứng với plugin thời docs-hero.

> ⚠️ Phải chạy phase này trước phase 02. Sau khi 02 sửa root thì không còn nguyên trạng để đóng băng.

## Tasks

- [ ] Xác định tập "site publish được" cần copy: `index.html`, `docs.html`, `skills/`, `commands/`,
      `.nojekyll`. **KHÔNG** copy: `_scaffolder/` (build tooling), `journals/`, `.claude-flow/`,
      `superpowers/` (untracked).
- [ ] Xác nhận asset: kiểm tra trang có inline CSS/JS (`<style>`/`<script>` trong file) hay tham
      chiếu file ngoài. Nếu có asset ngoài (css/js/img) → copy kèm. (Quan sát ban đầu: CSS inline.)
- [ ] Tạo `docs/v1.0.0/` và copy tập trên vào đó, giữ nguyên cấu trúc thư mục con
      (`docs/v1.0.0/skills/*.html`, `docs/v1.0.0/commands/*.html`).
- [ ] KHÔNG sửa nội dung snapshot ở phase này (giữ nguyên cả URL `claude-plugins` cũ — đó là
      history). Việc nhúng selector vào snapshot làm ở phase 04.
- [ ] Mở thử `docs/v1.0.0/index.html` → trang load được, nav nội bộ trong snapshot không gãy.

## Verify

- [ ] `docs/v1.0.0/` có đủ `index.html` + `docs.html` + 26 trang skill + 15 trang command (đúng số
      lượng stale hiện tại, gồm cả các trang `generate-*`/`docs-hero`/`sync`...).
- [ ] Browse offline: link giữa các trang trong snapshot hoạt động (relative path còn nguyên).
