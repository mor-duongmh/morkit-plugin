# Greenfield Human-Gate Checklists (thủ công)

Bộ checklist **thủ công** cho các human gate của luồng `/morkit:greenfield`.
Dành cho **team dự án tick tay** — KHÔNG nối vào workflow/orchestrator/hook.

## Khi nào dùng
Mỗi khi luồng greenfield chạy tới một gate cần người duyệt (**G2, G3, G4, G6**),
mở checklist tương ứng, soát artifact, tick, rồi ký duyệt.

## Cách dùng
1. Copy cả folder này vào workspace dự án, ví dụ:
   `morkit/output/greenfield/<proj-slug>/checklists/`
2. Mở file gate đang tới, điền phần **Thông tin**.
3. Soát artifact, tick từng mục — **chỉ tick khi thỏa dòng `Tiêu chí:`**.
4. Điền **block ký duyệt** ở cuối: chọn quyết định + người duyệt + ngày.
5. (Tùy chọn) nhập lại quyết định vào `state.json` để đồng bộ — xem mapping bên dưới.

## Danh sách file
| File | Gate | Vai trò soát | Artifact |
|---|---|---|---|
| `g2-requirement-decomposition-checklist.md` | G2 Phân rã yêu cầu | BrSE | `user-story-list.md` (Function List/User Story) |
| `g3-analysis-checklist.md` | G3 Analysis | BA | `gap-analysis.md`, `risk-register.md` |
| `g4-clarify-checklist.md` | G4 Clarify | BrSE/BA | `clarification-log.md` |
| `g6-srs-review-checklist.md` | G6 SRS | BrSE/BA | `docs/srs.md`, `docs/srs.html` |

## Nguyên tắc
- **Trỏ về nguồn chân lý, không chép luật.** Định nghĩa gate gốc nằm ở
  `plugins/morkit/skills/greenfield-orchestrator/references/greenfield-conventions.md` (§2–3).
  Nếu gate/enum đổi, cập nhật checklist theo.
- **Chống tick mù.** Chỉ tick khi thỏa dòng `Tiêu chí:`.
- **No-fiction.** Không có gì được "bịa" — thiếu nguồn thì là `<TBD>`/OpenQuestion.

## Mapping quyết định → `state.json` (nếu muốn đồng bộ)
`state.json` dùng enum: `proceed` | `adjust` | `force-close` (Abort = dừng, không lưu).

| Gate | Nhãn trên checklist → enum |
|---|---|
| G2 | Proceed→`proceed` · Another round→`adjust` · Abort→dừng |
| G3 | Proceed→`proceed` · Adjust→`adjust` · Abort→dừng |
| G4 | Close loop→`proceed` · Another round→`adjust` · Force-close→`force-close` |
| G6 | Proceed→`proceed` · Revise→`adjust` · Abort→dừng |

## Ngoài phạm vi (chưa có ở đây)
- **QA gate sau G7** (`docs-reviewer`) — là checkpoint người-thật nhưng chưa làm checklist.
- **Gate G7 "Architecture"** — đã duyệt brainstorm nhưng chưa implement; thêm
  `g7-architecture-checklist.md` khi nào gate đó vào code.
