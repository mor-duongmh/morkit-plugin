# Greenfield Human-Gate Checklists — đã chuyển vào skill

> **Canonical đã move** sang skill để orchestrator đọc được runtime ở mọi project:
> `plugins/morkit/skills/greenfield-orchestrator/references/gate-checklists/`
> Các file ở thư mục này giờ chỉ là **con trỏ** về canonical (chống trùng/lệch — DRY).

Bộ checklist cho các human gate của luồng `/morkit:greenfield` (**G2, G3, G4, G6**).
Trước đây tách rời thủ công; nay **nối thẳng vào workflow**: orchestrator đọc front-matter
`required` của mỗi checklist, render mục bắt buộc vào gate, và `state_manager.advance`
**chặn cứng** tới khi `decision==proceed` + đủ `required` confirmed (G4 `force-close` kèm note).

## Cách hoạt động (tích hợp)
1. Orchestrator: `checklist_loader.py show --gate Gx` → lấy `required` + tiêu đề mục.
2. Render mục bắt buộc + `Tiêu chí:` → `AskUserQuestion` (multiSelect "đã đạt?") + câu quyết định.
3. `state_manager set-gate … --checklist-required … --checklist-confirmed …`.
4. `advance` → thiếu required hoặc chưa proceed ⇒ raise, ở lại gate.

## Tick tay offline (fallback)
Chạy ngoài orchestrator vẫn được: mở bản **canonical** trong skill, điền **Thông tin**,
soát artifact, **chỉ tick khi thỏa dòng `Tiêu chí:`** (chống tick mù), rồi ký block cuối.

## Danh sách (trỏ về canonical trong skill)
| Gate | Vai trò | Artifact | Canonical |
|---|---|---|---|
| G2 Phân rã yêu cầu | BrSE | `user-story-list.md` | `…/gate-checklists/g2-requirement-decomposition-checklist.md` |
| G3 Analysis | BA | `gap-analysis.md`, `risk-register.md` | `…/gate-checklists/g3-analysis-checklist.md` |
| G4 Clarify | BrSE/BA | `clarification-log.md` | `…/gate-checklists/g4-clarify-checklist.md` |
| G6 SRS | BrSE/BA | `docs/srs.md`, `docs/srs.html` | `…/gate-checklists/g6-srs-review-checklist.md` |

## Nguyên tắc
- **1 nguồn chân lý:** chỉ sửa bản canonical trong skill. File ở đây chỉ trỏ đường.
- **Chống tick mù:** chỉ tick khi thỏa dòng `Tiêu chí:`. `required` là subset bắt buộc chặn gate.
- **No-fiction:** thiếu nguồn → `<TBD>`/OpenQuestion, không bịa.

## Mapping quyết định → `state.json`
`proceed` | `adjust` | `force-close` (Abort = dừng, không lưu). Mapping nhãn→enum nằm ở
front-matter `decisions` của từng checklist canonical.
