---
gate: G2
role: "BrSE"
artifact: ["user-story-list.md"]
decisions: { proceed: proceed, another-round: adjust, abort: null }
required: [G2-A1, G2-A2, G2-C1]
---

# [G2] Checklist Human Gate — Phân rã yêu cầu (Requirement Decomposition)

> Nguồn gate cho `/morkit:greenfield`. Orchestrator đọc `required` (front-matter)
> để render mục bắt buộc vào gate và chặn `advance` tới khi đủ. Vẫn tick tay được
> khi chạy offline ngoài orchestrator.
> Gate gốc: `../greenfield-conventions.md` §2–3 · Vai trò: **BrSE**
> Mục đích: soát chất lượng **phân rã yêu cầu** từ tài liệu khách thành danh sách có cấu trúc.
> Artifact: `morkit/output/greenfield/<proj>/user-story-list.md` — dạng
> **Function List (機能一覧, `--format brse`)** hoặc **User Story (`--format agile`)**.

## Thông tin
- Dự án: ____________________
- Người soát (BrSE): ____________________
- Ngày: ____________________
- Định dạng: &nbsp; [ ] Function List (brse) &nbsp; [ ] User Story (agile)

## Hạng mục kiểm

### A. Truy vết với yêu cầu khách
- [ ] [G2-A1] **Mỗi mục có nguồn (truy vết xuôi)** — không mục nào tự nghĩ ra.
  Tiêu chí: cột `Source` của mọi dòng trỏ tới được tài liệu/mục cụ thể của khách.
- [ ] [G2-A2] **Không sót yêu cầu (truy vết ngược)** — yêu cầu nào trong tài liệu cũng được phân rã.
  Tiêu chí: rà lại tài liệu nguồn, mỗi yêu cầu trong phạm vi đều ra ≥1 mục trong danh sách.
- [ ] [G2-A3] **Chỗ khách chưa rõ thì đánh dấu hỏi, không đoán** — không tự suy diễn lấp đầy.
  Tiêu chí: điểm mơ hồ đã hỏi và ghi vào `g2-clarification-log.md`, hoặc để `<TBD>` chờ làm rõ.

### B. Chất lượng phân rã
- [ ] [G2-B1] **Mức phân rã hợp lý** — mỗi mục là 1 chức năng độc lập, ước lượng/test được.
  Tiêu chí: không mục nào gộp nhiều chức năng (vd "quản lý + báo cáo + xuất file"), cũng không vụn tới mức thao tác UI lẻ.
- [ ] [G2-B2] **Đủ luồng phụ & ngoại lệ** — không chỉ luồng chính (happy path).
  Tiêu chí: CRUD đủ bộ khi cần, có tính tới lỗi/ngoại lệ/phân quyền, không chỉ "tạo/xem".
- [ ] [G2-B3] **Không trùng, không chồng chéo** — mỗi chức năng xuất hiện đúng 1 lần.
  Tiêu chí: không 2 mục mô tả cùng một việc, không mục nào bao trùm mục khác.
- [ ] [G2-B4] **Mô tả rõ, dev/QA đọc là hiểu** — không mơ hồ.
  Tiêu chí: mỗi mục nêu rõ actor + làm gì, không câu chung chung kiểu "xử lý dữ liệu".
- [ ] [G2-B5] **ID, ưu tiên, phân nhóm nhất quán** — danh sách có cấu trúc.
  Tiêu chí: mỗi mục có ID ổn định (FUNC-/US-) + Priority; nhóm theo module/màn hình/actor rõ ràng.

### C. Đủ trường theo định dạng (chỉ 1 — theo phần Thông tin)
- [ ] [G2-C1] **Đủ trường bắt buộc** — kiểm theo đúng định dạng đã chọn, không tick cả hai nhánh.
  Tiêu chí — mỗi dòng đủ trường:
  - Nếu **Function List (brse)**: `機能名/Function`, `概要/Description`, `アクター/Actor`, `優先度/Priority`, `Source`.
  - Nếu **User Story (agile)**: `As-a (role)`, `I-want (goal)`, `So-that (benefit)`, `Acceptance criteria`, `Priority`, `Source`.

## Ký duyệt gate (G2)
- Quyết định: &nbsp; [ ] **Proceed** — chốt danh sách (`proceed`) &nbsp; [ ] **Another round** — phân rã/hỏi thêm (`adjust`) &nbsp; [ ] **Abort** — dừng
- Ghi chú: ________________________________________________
- Người duyệt (BrSE): ____________________ &nbsp; Ngày: __________
