---
gate: G4
role: "BrSE/BA"
artifact: ["clarification-log.md"]
decisions: { close-loop: proceed, another-round: adjust, force-close: force-close }
required: [G4-1, G4-2]
---

# [G4] Checklist Human Gate — Làm rõ câu hỏi (Clarify)

> Nguồn gate cho `/morkit:greenfield`. Orchestrator đọc `required` (front-matter)
> để render mục bắt buộc vào gate và chặn `advance` tới khi đủ. Vẫn tick tay được
> khi chạy offline ngoài orchestrator.
> Gate gốc: `../greenfield-conventions.md` §2–3 · Vai trò: **BrSE/BA**
> Mục đích: chốt vòng hỏi-đáp với khách — các điểm mơ hồ ở G3 đã được làm rõ trước khi dựng SRS.
> Artifact: `morkit/output/greenfield/<proj>/clarification-log.md`
> (bảng hỏi-đáp, cột `Q-ID | Question | Status | Answer | Forwarded-to | Resolved-FR`).

## Thông tin
- Dự án: ____________________
- Người soát (BrSE/BA): ____________________
- Ngày: ____________________

## Hạng mục kiểm
- [ ] [G4-1] **Không câu hỏi nào bị bỏ lửng** — mỗi câu đều có tình trạng rõ ràng.
  Tiêu chí: cột Status mỗi dòng là một trong: `answered` (đã có câu trả lời) · `forwarded` (đã chuyển cho người liên quan, đang chờ) · `open` (còn để mở có chủ đích). Không dòng nào trống Status.
- [ ] [G4-2] **Câu hỏi quan trọng đã được trả lời** — không còn chặn việc dựng SRS.
  Tiêu chí: các câu sinh ra từ gap `blocker` (ở G3) đều đã `answered`, không còn `open`.
- [ ] [G4-3] **Câu trả lời là thật, không bịa** — đúng ý khách / người được hỏi.
  Tiêu chí: nội dung cột Answer đến từ khách hoặc stakeholder, không tự nghĩ ra cho xong vòng.
- [ ] [G4-4] **Câu đã trả lời được phản ánh lại** — trả lời xong không để đó.
  Tiêu chí: dòng `answered` có điền Answer và gắn `Resolved-FR` (hoặc đã lấp `<TBD>` ở chỗ liên quan).
- [ ] [G4-5] **Câu đang chờ ghi rõ chờ ai** — biết đang vướng ở đâu.
  Tiêu chí: dòng `forwarded` có điền `Forwarded-to` (tên người / bộ phận đang chờ trả lời).
- [ ] [G4-6] **Đóng sớm thì nêu lý do + giữ lại câu chưa xong** — không âm thầm bỏ.
  Tiêu chí: nếu còn câu `open`/`forwarded` mà vẫn đóng vòng, ghi lý do; câu chưa xong được giữ thành `<TBD>`/Open để xử lý sau, không xóa đi.

## Ký duyệt gate (G4)
- Quyết định: &nbsp; [ ] **Close loop** — đủ câu trả lời, đóng vòng (`proceed`) &nbsp; [ ] **Another round** — hỏi thêm 1 vòng (`adjust`) &nbsp; [ ] **Force-close** — đóng dù còn câu mở (`force-close`)
- Ghi chú / lý do force-close: ____________________________________
- Người duyệt (BrSE/BA): ____________________ &nbsp; Ngày: __________
