---
phase: 2
title: "Docs-update spec bridge"
status: completed
priority: P1
effort: "4-6h"
dependencies: []
---

# Phase 2: Docs-update spec bridge

## Overview
Mở rộng `/morkit:docs update`: ngoài scout code, đọc thêm change-spec **active** (4 file) và fold vào docs theo canonical-source rule, có drift-flag + FR-### dedup. Đây là phần lõi của B+bridge.

## Requirements
- Functional:
  - Phát hiện change bridge-eligible và đọc full 4 file (proposal/design/tasks/spec).
  - Map nội dung sang đúng doc theo canonical-source rule.
  - Đánh dấu drift khi spec không có bằng chứng code; liệt kê ở report.
  - Dedup FR-### theo capability-slug; honor delta ops ADDED/MODIFIED/RENAMED/REMOVED.
  - KHÔNG đọc `archive/`.
- Non-functional: LLM-driven; code vẫn canonical cho phần HOW; không tin spec mù quáng.

## Architecture

**"active/just-merged" (quyết định đã chốt):** change dưới `morkit/output/spec/`, NOT `archive/` (`.meta.json.archived==false`), VÀ `tasks.md` tick hết (`grep -cE '^\s*-\s+\[ \]' == 0`). Change còn task dở → BỎ QUA mặc định (spec chưa xong không đổ vào docs); có thể surface cảnh báo.
- Liệt kê qua quy ước thư mục (giống `list-changes.sh --json` nhưng đây là chỉ thị LLM đọc folder; không bắt buộc gọi script).

**Mapping (canonical-source rule — đã chốt):**
```
design.md  Decisions+alternatives  → 20-design/ADR/NNN-slug.md (MADR)         [design canonical]
design.md  Risks/Trade-offs         → 40-ai-coding/RISK-REGISTER + KNOWN-PITFALLS
design.md  Tech Stack               → 00-overview/STACK            (đối chiếu manifest thật)
design.md  Non-Goals                → 00-overview/SCOPE (ranh giới)
spec.md    ### Requirement (SHALL)  → 10-requirements/FEATURE-LIST (FR-###)    [spec canonical]
spec.md    #### Scenario WHEN/THEN  → 10-requirements/flows/FR-NNN-*  +  30-test/TEST-MATRIX (mỗi scenario = 1 row)
spec.md    SHALL chi tiết           → 20-design/.../SYS-SPEC Business Rules (BR-###)
proposal.md Why + Capabilities      → SCOPE + mô tả FR
tasks.md   Files (Create/Modify/Test) → SYS-SPEC Source Anchors + SOURCE-MAP   (hint; verify file tồn tại)
CODE (scout)                         → SYS-SPEC behavior, SOURCE-MAP, DATA/API/UI [CODE canonical]
```

**Drift handling (đã chốt — hybrid):**
- Doc code-derived (HOW): tạo/refresh từ scout như cũ.
- Doc bridge (WHAT/WHY): GHI nội dung, nhưng nếu 1 requirement/scenario KHÔNG tìm thấy bằng chứng code (scout không thấy symbol/route/test khớp) → gắn `status: drift` + chú thích "⚠ spec asserts X — chưa thấy trong code". KHÔNG ghi ngầm thành sự thật.
- Stage validate xuất **Drift list** để người xử lý. Code thắng khi mâu thuẫn trực tiếp.

**FR-### dedup (đã chốt):** FEATURE-LIST là registry duy nhất cấp FR-###.
- Match capability theo slug kebab với FR có sẵn:
  - trùng → MODIFIED (cập nhật tại chỗ, GIỮ FR-###)
  - mới → cấp FR-### kế tiếp
- spec delta ops: `ADDED`→FR mới · `MODIFIED`→update FR · `RENAMED`→đổi tên giữ ID · `REMOVED`→đánh dấu deprecated (kèm Reason/Migration). KHÔNG tạo FR trùng cho cùng capability.

**Vị trí trong flow (đã chốt):** bridge chạy như 1 bước của `docs update`, TRƯỚC `archive`. Thêm bước giữa Step 4 (update content) và Step 5/6, hoặc thành Step mới "4c — Bridge active change-specs".

## Related Code Files
- Modify: `plugins/morkit/skills/writing-docs/references/update-workflow.md`
  - Thêm **Step "Bridge active change-specs"**: định nghĩa eligible, đọc 4 file, bảng mapping, canonical rule, drift, dedup.
  - Step 7 (Validate) / Step 8 (Report): thêm mục **Drift list** + "specs bridged: N changes, M FR touched".
  - Notes: ghi rõ "đọc active changes, KHÔNG archive/"; "chạy trước /morkit:archive".
- Modify (nếu cần): `plugins/morkit/skills/writing-docs/SKILL.md` — 1 dòng ở Routing/Constraints nhắc update có bridge.

## Implementation Steps
1. Đọc `update-workflow.md`, `schemas/morkit-driven/schema.yaml` (format spec.md), template `proposal/design/tasks` + doc-template `FEATURE-LIST`, `ADR`, `RISK-REGISTER`, `TEST-MATRIX`, `SYS-SPEC` để map chính xác section.
2. Soạn định nghĩa **bridge-eligible** + cách liệt kê change active (không archive, tasks ticked).
3. Soạn **bảng mapping** + **canonical-source rule** (ai thắng theo loại doc).
4. Soạn **drift handling** (điều kiện gắn `status: drift`, chú thích, đưa vào report).
5. Soạn **FR-### dedup** + ánh xạ delta ops.
6. Chèn bước bridge đúng vị trí (trước archive); cập nhật Validate + Report.
7. Kiểm cross-link tới template ADR/RISK/TEST-MATRIX/flows/SYS-SPEC tồn tại.

## Success Criteria
- [ ] `update-workflow.md` có bước Bridge: eligible rõ ràng, đọc đủ 4 file, KHÔNG đụng `archive/`.
- [ ] Bảng mapping + canonical-source rule đầy đủ (code/design/spec/proposal/tasks).
- [ ] Drift: spec-không-có-code → `status: drift` + xuất Drift list ở report; code thắng xung đột.
- [ ] FR-### dedup theo slug + honor 4 delta ops; không tạo FR trùng.
- [ ] Ghi rõ sequencing "bridge trước archive".
- [ ] Cross-link template giải đúng.

## Risk Assessment
- **Spec lỗi thời đổ rác vào docs** → mitigation: drift-flag bắt buộc khi thiếu bằng chứng code; code canonical; report liệt kê để người duyệt.
- **Dedup sai → FR trùng/đè nhầm** → mitigation: match theo slug + map delta ops tường minh; khi mơ hồ → giữ riêng + flag.
- **Bridge phình logic (KISS)** → mitigation: chỉ active + tasks-ticked (giảm số change xử lý); không reconcile tự động phức tạp, chỉ flag.
- **Đọc 4 file × nhiều change tốn context** → mitigation: chỉ change eligible; đọc theo nhóm; tóm tắt trước khi fold.
