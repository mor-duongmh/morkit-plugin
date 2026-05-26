---
phase: 4
title: "Verify + consistency"
status: completed
priority: P2
effort: "2h"
dependencies: [1, 2, 3]
---

# Phase 4: Verify + consistency

## Overview
Kiểm chứng instruction mới chạy đúng + nhất quán. Vì skill LLM-driven (không có script để unit-test hành vi), verify = walkthrough trên fixture + kiểm static cross-link/ID.

## Requirements
- Functional: chứng minh greenfield seed + bridge cho output đúng kỳ vọng trên ví dụ tối thiểu.
- Non-functional: không thêm Python/CLI dependency; tái dùng `tests/` bash nếu hợp.

## Architecture

**A. Walkthrough greenfield (dry-run thủ công):**
- Tạo thư mục tạm rỗng (chỉ README) → đọc init-workflow → xác nhận: detector ra greenfield, seed đúng 4 file, KHÔNG file code-derived nào được liệt kê, CLAUDE.md pointer hợp lệ.
- Tạo thư mục có `package.json` + 1 file `src/` → xác nhận rẽ brownfield (không seed).

**B. Walkthrough bridge (fixture change-spec):**
- Dựng 1 change active giả dưới `morkit/output/spec/demo-export/` (proposal+design+tasks tick hết+spec với 1 ADDED Requirement + 1 Scenario) + vài file code khớp + 1 requirement KHÔNG có code.
- Đọc update-workflow → xác nhận: decision→ADR, scenario→TEST-MATRIX row + flow, requirement→FR-### ở FEATURE-LIST, Files→Source Anchors; requirement-không-code → `status: drift` + vào Drift list. Đổi capability trùng slug → MODIFIED giữ FR-###.

**C. Kiểm static:**
- Mọi cross-link trong init-workflow.md/update-workflow.md/SKILL.md/DOCUMENT-MAP.md trỏ tới file template TỒN TẠI.
- ID nhất quán: FR-###/NFR-### (FEATURE-LIST) ↔ INV-### (INVARIANTS) ↔ TEST-MATRIX.Ref; BR-### local SYS-SPEC.
- `tests/run-all.sh` vẫn pass (không vỡ test scaffold/validate/list-changes sẵn có).
- grep version: cả 2 plugin.json = 1.7.0.

## Related Code Files
- Create (tạm, xoá sau verify): fixture dưới thư mục tạm + `morkit/output/spec/demo-export/` (KHÔNG commit).
- Read: tất cả file đã sửa ở Phase 1-3.
- Run: `plugins/morkit/tests/run-all.sh` (đảm bảo không regression).

## Implementation Steps
1. Walkthrough A (greenfield empty + scaffold) — ghi nhận khớp/không.
2. Walkthrough B (bridge fixture) — kiểm 4 mapping + drift + dedup.
3. Kiểm static cross-link + ID (grep các link tương đối → file tồn tại).
4. Chạy `tests/run-all.sh` — xác nhận xanh.
5. grep `"version"` 2 plugin.json = 1.7.0.
6. Dọn fixture tạm. Viết report ngắn (created/gaps/oversize) vào `plans/reports/`.

## Success Criteria
- [ ] Walkthrough greenfield: empty→seed đúng, scaffold→brownfield; ZERO file code-derived khi rỗng.
- [ ] Walkthrough bridge: 4 mapping đúng + drift-flag + FR dedup hoạt động trên fixture.
- [ ] Không cross-link gãy; ID traceable.
- [ ] `tests/run-all.sh` pass.
- [ ] 2 plugin.json = 1.7.0.
- [ ] Fixture tạm đã dọn; report verify lưu ở `plans/reports/`.

## Risk Assessment
- **Walkthrough chủ quan (không có assert tự động)** → mitigation: checklist kỳ vọng cụ thể từng bước; fixture có sẵn case drift + dedup để buộc kiểm.
- **Fixture lỡ commit** → mitigation: dùng thư mục tạm ngoài repo / thêm vào .gitignore tạm; bước dọn bắt buộc.
- **Regression test scaffold** → mitigation: chạy run-all.sh; chỉ sửa markdown nên rủi ro thấp.
