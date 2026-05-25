---
phase: 4
title: "Migrate Old Templates & Cleanup"
status: completed
priority: P2
effort: "2h"
dependencies: [3]
---

# Phase 4: Migrate Old Templates & Cleanup

## Overview
Hợp nhất 5 template phẳng cũ (`example/*-template.md`) vào doc-templates mới, quyết định giữ/bỏ, và dọn dẹp.

## Requirements
- Functional: nội dung giá trị của 5 template cũ đã được hấp thụ vào template mới; không còn template mồ côi gây nhầm lẫn.
- Non-functional: giữ `example/mail-history-admin/` làm reference example (không xóa).

## Architecture
Mapping đã chốt (report review §"5 template phẳng cũ"):
- system-architecture-template → ARCHITECTURE (arc42-lite base)
- database-design-template → DATA-MAP full-mode
- codebase-summary-template → STACK + README root + LOCAL-RUNBOOK
- code-standards-template → CODE-STANDARDS
- design-guidelines-template → ADR + ARCHITECTURE patterns + KNOWN-PITFALLS

## Related Code Files
- Modify/absorb: `example/code-standards-template.md`, `example/codebase-summary-template.md`, `example/database-design-template.md`, `example/design-guidelines-template.md`, `example/system-architecture-template.md`
- Decide: giữ 5 file cũ làm "flat-mode legacy" hay xóa sau khi hấp thụ (đề xuất: xóa để tránh trùng, vì đã có doc-templates/).
- Keep: `example/mail-history-admin/` (reference example, không đụng).

## Implementation Steps
1. Xác nhận mỗi template cũ đã được phản ánh trong doc-templates phase 3.
2. Quyết định số phận 5 file cũ (xóa hoặc move vào doc-templates làm full-mode variant).
3. Cập nhật mọi tham chiếu tới `example/*-template.md` (README, docs skill cũ ck:docs nếu có).
4. Dọn các tham chiếu docs-hero còn sót (nếu phát hiện).

## Success Criteria
- [ ] 5 template cũ đã hấp thụ hết giá trị vào template mới
- [ ] Không còn tham chiếu gãy tới template cũ
- [ ] `example/mail-history-admin/` giữ nguyên làm reference

## Risk Assessment
- Xóa nhầm nội dung chưa hấp thụ → mitigate: checklist mapping 1-1 trước khi xóa.
