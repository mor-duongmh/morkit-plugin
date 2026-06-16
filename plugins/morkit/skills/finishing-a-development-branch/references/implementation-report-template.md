# Implementation Report — Template

> **Cách dùng:** In chat mặc định; mục trống ghi —; ghi file chỉ khi user yêu cầu (gợi ý `plans/reports/`).
> Điền từ context phiên làm việc (controller đã biết tasks/commits/files/tests/reviews); chỉ dùng `git log --oneline <base>..HEAD` và `git show --stat` để xác nhận chính xác SHA/file. Ngôn ngữ theo user (VN/EN).

---

## 1. Tóm tắt điều hành

> 2–3 câu: làm gì, vì sao, kết quả ra sao.

<điền tóm tắt — hoặc —>

## 2. Công việc đã thực hiện

> Bảng: mỗi task một dòng. Thay đổi nhỏ (1–2 file) thì bảng tự co lại; ô trống ghi —.

| Task | Commit | Files changed |
|------|--------|---------------|
| <task> | <SHA ngắn> | <đường dẫn file> |

## 3. Tests & review

> Test suite chạy gì, pass/fail; review (self-review hay reviewer) phát hiện gì.

<điền — hoặc —>

## 4. Ảnh hưởng đến dự án

> Hành vi thay đổi · người dùng cần làm gì · migration · thành phần KHÔNG bị ảnh hưởng.

- **Hành vi thay đổi:** <… hoặc —>
- **Người dùng cần làm gì:** <… hoặc —>
- **Migration:** <… hoặc —>
- **KHÔNG bị ảnh hưởng:** <… hoặc —>

## 5. Rủi ro / nợ kỹ thuật & follow-up

> Rủi ro còn lại, nợ kỹ thuật, việc cần làm tiếp.

<điền — hoặc —>

## 6. Truy vết

> Branch · commit SHA · gate status.

- **Branch:** <feature-branch>
- **Commit SHA:** <SHA list>
- **Gate status:** <Overall Decision của review-checklist — hoặc —>
