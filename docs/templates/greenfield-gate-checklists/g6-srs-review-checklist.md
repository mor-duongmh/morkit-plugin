# [G6] Checklist Human Gate — SRS Review (BrSE/BA soát SRS)

> Template thủ công — copy ra workspace dự án, tick tay. KHÔNG nối vào workflow.
> Gate gốc: `greenfield-conventions.md` §2–3 · Vai trò: **BrSE/BA**
> Artifact soát: `docs/srs.md`, `docs/srs.html` (render từ `project-model.json`)

## Thông tin
- Dự án: ____________________
- Người soát (BrSE/BA): ____________________
- Ngày: ____________________

## A. Đầy đủ & truy vết
- [ ] **Đủ section bắt buộc** — SRS có đủ mục chuẩn BrSE (chỉ kiểm có mặt; chất lượng để §B).
  Tiêu chí: có Doc Control, Mục đích tài liệu, Luồng nghiệp vụ, FR (danh sách + chi tiết),
  Business Rules, Roles, NFR, Data Items, External Interfaces, Reports, Acceptance/UAT, RTM,
  Open Q&A, Constraints/Assumptions/Risks, Screen Index. (Glossary đã gộp vào §1.5 Thuật ngữ —
  không còn Phụ lục B.)
- [ ] **Hết `<TBD>` ở mục bắt buộc** — Không còn chỗ trống treo.
  Tiêu chí: không còn `<TBD>`, hoặc TBD còn lại đều có OpenQuestion tương ứng.
- [ ] **RTM không đứt** — Truy vết hai chiều đầy đủ.
  Tiêu chí: FR ↔ UseCase ↔ Screen map đủ, không mục nào mồ côi.
- [ ] **Khớp G2** — FR khớp danh sách chức năng đã chốt.
  Tiêu chí: không FR nào tự phát sinh hay rơi rớt so với `user-story-list.md` (G2).

## B. Chất lượng từng section
- [ ] **§1 Mục đích đủ chất** — bối cảnh/khó khăn rõ, điểm mạnh hệ thống, phạm vi theo giai đoạn.
  Tiêu chí: §1.1–1.3 không bỏ trống (bối cảnh/khó khăn, điểm mạnh, phạm vi giai đoạn đầu/sau);
  bảng Thuật ngữ (§1.5) và Đối tượng sử dụng (§1.6) có dữ liệu.
- [ ] **UC chi tiết đủ** — mỗi UC có sơ đồ + đủ trường + màn hình gắn theo UC.
  Tiêu chí: §2.3 mỗi UC có Mermaid (start→end, có actor), Description/Actor/Priority/Trigger/
  Pre/Post, Basic/Alternative/Exception Flow, Business Rule (nếu có), và màn hình liên quan gắn
  inline (không chỉ liệt kê rời ở Phụ lục A).
- [ ] **Business Rules rõ & gắn FR/UC** — quy tắc nghiệp vụ phát biểu được, không treo lơ lửng.
  Tiêu chí: mỗi rule nêu được điều kiện → hệ quả (không câu chung chung); mỗi rule gắn ≥1 FR
  hoặc UC dùng nó; rule do khách quyết mà chưa chốt để `<TBD>`/OpenQuestion, không tự đặt.
- [ ] **Roles & Permissions đủ** — ai làm được gì, không role mồ côi.
  Tiêu chí: §Roles có ma trận Role × chức năng (hoặc Role × FR); mỗi role xuất hiện trong UC/
  §Roles đều có trong ma trận; mỗi FR nhạy cảm (tạo/sửa/xóa/duyệt) có ≥1 role được phép; không
  ô để trống không lý do.
- [ ] **NFR đo được** — NFR có số đo cụ thể, phủ đủ nhóm.
  Tiêu chí: không dùng "nhanh/ổn định/dễ dùng" chung chung — mỗi NFR có ngưỡng + đơn vị; phủ các
  nhóm IPA-6 ở mức áp dụng được; nhóm Security/PII có mục cụ thể (không bỏ trống).
- [ ] **Data Items đủ** — dữ liệu rõ kiểu & vòng đời.
  Tiêu chí: mỗi data item có kiểu + ràng buộc (bắt buộc/độ dài/định dạng); item chứa dữ liệu cá
  nhân đánh dấu PII + có thời hạn lưu (retention); không item nào chỉ có tên trống nghĩa.
- [ ] **External Interfaces rõ** — giao tiếp ngoài nêu đủ thông tin tích hợp.
  Tiêu chí: mỗi giao tiếp ngoài có hướng (gửi/nhận) + giao thức/định dạng + dữ liệu trao đổi +
  hệ thống đối tác; phần chưa chốt để `<TBD>`, không bịa endpoint.
- [ ] **Reports đủ** — mỗi báo cáo rõ nguồn & người dùng.
  Tiêu chí: mỗi report nêu nguồn dữ liệu + tần suất/kỳ + người nhận + định dạng xuất; report suy
  từ FR/Data có đường truy vết, không đứng rời.
- [ ] **Acceptance/UAT đo được** — nghiệm thu kiểm chứng được.
  Tiêu chí: mỗi tiêu chí nghiệm thu nêu điều kiện + kết quả mong đợi (verify được, không "hệ
  thống chạy ổn"); mỗi tiêu chí map tới ≥1 FR/UC; FR ưu tiên cao đều có tiêu chí nghiệm thu.
- [ ] **Constraints/Assumptions/Risks ghi rõ** — ràng buộc & giả định không bị bỏ lửng.
  Tiêu chí: Constraints (kỹ thuật/pháp lý/thời gian) ghi cụ thể, không để "không có" mà chưa xác
  nhận; Assumptions nêu rõ điều đang giả định + ai xác nhận; risk lớn có hướng giảm thiểu.

## C. Đủ điều kiện chuyển tiếp
- [ ] **SRS đủ chất để chuyển bước sau** — BrSE/BA xác nhận.
  Tiêu chí: §A+§B đã soát đạt; phạm vi SRS rõ + tiêu chí nghiệm thu (§B — Acceptance/UAT) verify
  được; điểm còn vướng đã ghi `<TBD>`/OpenQuestion, không bỏ qua.

## Ký duyệt gate (G6)
- Quyết định: &nbsp; [ ] **Proceed** (`proceed`) &nbsp; [ ] **Revise** — sửa rồi render lại (`adjust`) &nbsp; [ ] **Abort** — dừng
- Ghi chú: ________________________________________________
- Người duyệt (BrSE/BA): ____________________ &nbsp; Ngày: __________
