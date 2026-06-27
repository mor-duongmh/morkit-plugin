# [G3] Checklist Human Gate — Phân tích Gap & Risk (BA soát)

> Template thủ công — copy ra workspace dự án, tick tay. KHÔNG nối vào workflow.
> Gate gốc: `greenfield-conventions.md` §2–3, §6 · Vai trò: **BA**
> Mục đích: BA soát Gap Analysis + Risk Register trước khi dựng SRS.
> Artifact: `morkit/output/greenfield/<proj>/gap-analysis.md`, `risk-register.md`

## Thông tin
- Dự án: ____________________
- Người soát (BA): ____________________
- Ngày: ____________________

## A. Gap Analysis (`gap-analysis.md`)
- [ ] **Mỗi gap đủ thông tin** — đọc là hiểu thiếu gì, ảnh hưởng đâu, định làm gì.
  Tiêu chí: mỗi dòng có Description + Affected US/FR + Recommended Action, không bỏ trống các cột này.
- [ ] **Phân loại & mức độ rõ** — biết ngay gap nào chặn việc dựng SRS.
  Tiêu chí: mỗi gap có Type (`new-requirement` / `out-of-scope`) + Severity (`blocker` / `warning` / `info`); gap `blocker` nhìn ra được ngay.
- [ ] **Đã ghi đủ vào file quản lý** — không gap nào nằm ngoài file.
  Tiêu chí: mọi gap phát hiện đều có 1 dòng trong `gap-analysis.md`, không ghi tạm chỗ khác (chat, note rời).
- [ ] **Thiếu dữ liệu thì đánh dấu chờ, không tự điền** — không bịa cho đủ.
  Tiêu chí: chỗ chưa có thông tin (vd ngưỡng NFR, thứ phải có code mới biết) để `<TBD: …>` hoặc gắn `out-of-scope`, không đặt giá trị giả. (Greenfield chưa có code.)
- [ ] **Gap cần khách trả lời được đánh dấu để hỏi** — đẩy sang bước hỏi-đáp.
  Tiêu chí: gap `new-requirement` cần khách quyết → Recommended Action ghi "hỏi khách", Resolution để `_open_` chờ giải đáp ở **bước Clarify (G4 — bước hỏi-đáp với khách ngay sau G3)**.

## B. Risk Register (`risk-register.md`)
- [ ] **Mỗi risk chấm điểm đúng cách** — điểm số không tùy hứng.
  Tiêu chí: Probability và Impact đều ở thang Cao/Trung bình/Thấp (H/M/L); **Score = Probability × Impact**, với H=3, M=2, L=1 → điểm 1–9. Ví dụ: M × H = 2 × 3 = 6.
- [ ] **Risk cao có biện pháp giảm thiểu** — không để trống.
  Tiêu chí: mọi risk **Score ≥ 6** (cột High? = ✅) đều có Mitigation + Owner; thiếu một trong hai là chưa đạt.
- [ ] **Đã ghi đủ vào file quản lý** — không risk nào nằm ngoài file.
  Tiêu chí: mọi risk đều có 1 dòng trong `risk-register.md`, đủ cột (ID, Category, Description, Probability, Impact, Score, Mitigation, Owner, Status).
- [ ] **Mâu thuẫn giữa tài liệu được ghi nhận** — nguồn đá nhau không bị bỏ qua.
  Tiêu chí: chỗ 2 tài liệu khách nói khác nhau được ghi thành 1 mục để xử lý (risk `Category=Gaps` hoặc 1 gap tương ứng), không lờ đi.

## Ký duyệt gate (G3)
- Quyết định: &nbsp; [ ] **Proceed** (`proceed`) &nbsp; [ ] **Adjust** — sửa lại, soát lại G3 (`adjust`) &nbsp; [ ] **Abort** — dừng
- Ghi chú: ________________________________________________
- Người duyệt (BA): ____________________ &nbsp; Ngày: __________
