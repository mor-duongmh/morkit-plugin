---
phase: 3
title: "Doc Templates (30 skeletons)"
status: completed
priority: P1
effort: "1d"
dependencies: [2]
---

# Phase 3: Doc Templates (30 skeletons)

## Overview
Viết 30 template skeleton trong `doc-templates/` — phần lõi của skill. Mỗi template có structure đã chốt ở report review (front-matter, dòng ranh giới, placeholder, hint).

## Requirements
- Functional: mỗi template tự đủ để agent điền cho project bất kỳ (generic, có placeholder + hướng dẫn inline).
- Non-functional: ~100 LOC/template, flow text-arrow, cross-link tương đối, front-matter tối thiểu.

## Architecture
30 template (xem bảng index report review), nhóm theo taxonomy. **Tái dùng** structure `example/mail-history-admin/` (instance) → biến thành skeleton có placeholder + comment hướng dẫn.

## Related Code Files (tạo trong `plugins/morkit/skills/writing-docs/references/doc-templates/`)
- README (root + per-folder), 00-overview: DOCUMENT-MAP, SCOPE, SOURCE-MAP, DEPENDENCY-MAP, GLOSSARY, **STACK** (mới)
- 10-requirements: FEATURE-LIST, USER-FLOWS (index) + flows/`FR-NNN` example
- 20-design: DESIGN-MAP, ARCHITECTURE (**arc42-lite**), INVARIANTS, `*-SYS-SPEC` (core+optional sections), DATA-MAP (**2-mode**), API-MAP, UI-MAP, `*-REFERENCE` (pointer), **ADR/NNN-slug** (mới, MADR)
- 30-test: TEST-STRATEGY, TEST-RUNBOOK, TEST-MATRIX (Ref+Status)
- 40-ai-coding: AI-CODING-GUIDE (meta-index), CODE-SEARCH-GUIDE, COMMON-CHANGE-PLAYBOOKS, KNOWN-PITFALLS, RISK-REGISTER, **CODE-STANDARDS** (mới)
- 90-operations: LOCAL-RUNBOOK, TROUBLESHOOTING
- Read: `example/mail-history-admin/*` + `example/*-template.md` (cho 3 doc mới + arc42 + db full-mode)

## Implementation Steps
1. Tạo template per-folder README + root README (2 biến thể).
2. Nhóm 00-overview (6 template, gồm STACK mới).
3. Nhóm 10-requirements (FEATURE-LIST giàu + USER-FLOWS index + flows/ example).
4. Nhóm 20-design (10+ template; ARCHITECTURE từ system-architecture-template arc42; DATA-MAP map+full mode từ database-design-template; ADR MADR từ design-guidelines-template; SYS-SPEC core+optional + Known-Issues).
5. Nhóm 30-test (3), 40-ai-coding (6 gồm CODE-STANDARDS từ code-standards-template), 90-operations (2).
6. Mỗi template: front-matter tối thiểu + dòng ranh giới `> Doc này chứa X, cho Y xem [..]` + placeholder + hint inline.

## Success Criteria
- [ ] Đủ 30 template, mỗi cái ~100 LOC, có front-matter + ranh giới + cross-link mẫu
- [ ] 3 doc mới (STACK, CODE-STANDARDS, ADR) hoàn chỉnh
- [ ] ARCHITECTURE arc42-lite; DATA-MAP có cả map-mode + full-mode; SYS-SPEC có core+optional sections
- [ ] Traceability ID nhất quán (FR/NFR/INV/BR)

## Risk Assessment
- 30 file = khối lượng lớn → mitigate: dispatch song song theo nhóm (morkit dispatching-parallel-agents), mỗi agent 1 nhóm, tránh bloat context.
- Lệch giữa template ↔ reference → mitigate: cross-check anchor-conventions sau khi viết.
