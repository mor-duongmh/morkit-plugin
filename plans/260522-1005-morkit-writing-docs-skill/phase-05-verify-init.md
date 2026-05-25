---
phase: 5
title: "Verify Init E2E"
status: completed
priority: P2
effort: "3h"
dependencies: [3, 4]
---

# Phase 5: Verify Init E2E

## Overview
Chạy thật `/morkit:docs init` trên 1 codebase mẫu, kiểm tra output taxonomy + mỏ neo + cross-link, iterate tới khi đạt.

## Requirements
- Functional: init sinh đúng core-6 taxonomy cho codebase mẫu; MAP/anchor chính xác; cross-link không gãy.
- Non-functional: mỗi file <200 LOC; không Python; chạy trong 1 phiên agent.

## Architecture
Chọn codebase mẫu nhỏ-vừa (đề xuất: chính `plugins/morkit/` hoặc 1 sub-project thật). Chạy init → đối chiếu output với reference `example/mail-history-admin/`.

## Related Code Files
- Read: output `docs/` sinh ra (ở project mẫu hoặc thư mục test tạm)
- Possibly fix: SKILL.md, references/*, doc-templates/* theo lỗi phát hiện

## Implementation Steps
1. Chọn codebase mẫu; chạy `/morkit:docs init`.
2. Kiểm: cấu trúc folder core-6 đúng; chỉ tạo conditional folder khi có DB/API/UI.
3. Kiểm DOCUMENT-MAP read paths trỏ file tồn tại; SOURCE-MAP concern→file spot-check đúng với code thật.
4. Kiểm cross-link tương đối không gãy; front-matter có `source_files`.
5. Kiểm size (~100 LOC) + flow text-arrow.
6. Test `/morkit:docs summarize` + phát hiện docs/ phẳng cũ (nếu có) → hỏi migrate.
7. Fix lỗi → chạy lại.

## Success Criteria
- [ ] init sinh core-6 taxonomy đúng trên codebase mẫu
- [ ] DOCUMENT-MAP + SOURCE-MAP chính xác (spot-check)
- [ ] Cross-link không gãy, front-matter đủ
- [ ] Files <200 LOC, không Python
- [ ] summarize chạy được

## Risk Assessment
- LLM sinh MAP lệch code thật → mitigate: init-workflow ép "MAP sinh sau nội dung" + spot-check ở bước verify.
- Output quá dài/lệch reference → mitigate: iterate, đối chiếu example/mail-history-admin.
