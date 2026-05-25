---
phase: 2
title: "References & Workflows"
status: completed
priority: P1
effort: "5h"
dependencies: [1]
---

# Phase 2: References & Workflows

## Overview
Viết các reference định nghĩa taxonomy, quy ước mỏ neo, và 3 workflow (init/update/summarize) mà SKILL.md route tới.

## Requirements
- Functional: init-workflow sinh taxonomy đúng thứ tự (nội dung trước, MAP sau); taxonomy.md + anchor-conventions.md đủ để agent tự sinh nhất quán.
- Non-functional: mỗi reference cô đọng, agent đọc là làm được; không lặp giữa các reference.

## Architecture
- `references/taxonomy.md`: vai trò 6 nhóm + sub-taxonomy 20-design; phân loại core/conditional/optional; quy tắc project-level vs per-module; khi nào tạo folder mở rộng (00-review/50-migration/60-security/70-performance/80-release).
- `references/anchor-conventions.md`: 4 cơ chế mỏ neo; front-matter tối thiểu (`updated`/`status`/`source_files`); ID policy (FR/NFR/INV/BR) + traceability loop; quy tắc DRY (dòng ranh giới + cross-link); flow text-arrow.
- `references/init-workflow.md`: 6 stage (chi tiết bên dưới).
- `references/update-workflow.md` + `references/summarize-workflow.md`: xem mục riêng.

### init-workflow chi tiết (6 stage)
Cú pháp: `/morkit:docs init [path] [--scope project|module] [--yes]`
- **STAGE 0 Preflight & Scope:** kiểm `docs/` tồn tại — đã có taxonomy mới → **CHẶN, gợi ý `/morkit:docs update`** (init chỉ lần đầu); docs/ phẳng cũ → đánh dấu MIGRATE (Stage 6); trống → init. **Scale: LUÔN hỏi user** (AskUserQuestion project vs per-module; `--scope` override để bỏ hỏi).
- **STAGE 1 Scout** (morkit-native dispatch song song, read-only): cây thư mục+LOC, entry points, tech stack (manifest), routes/API, data models/migration, UI, test setup, lint/commit, CI. Phát hiện thành phần → quyết CONDITIONAL folder: schema/ORM→20-data; route/API→30-api; UI→40-ui; lint/commit→40-ai-coding/CODE-STANDARDS.
- **STAGE 2 Docs Plan + GATE:** liệt kê folder/file sẽ tạo (core+conditional) + feature list + scope → trình user **Proceed/Adjust/Abort** (**bỏ qua khi `--yes`**).
- **STAGE 3 Generate Content (TRƯỚC):** dispatch song song theo nhóm (file ownership tách biệt): 10-req · 20-design (SYS-SPEC/feature) · 30-test · 40-ai-coding · 90-ops · 00-overview (SCOPE/STACK/GLOSSARY/DEPENDENCY-MAP). Mỗi file: front-matter `source_files` + nội dung + placeholder cross-link.
- **STAGE 4 Generate Anchors (SAU):** SOURCE-MAP, DOCUMENT-MAP, DESIGN-MAP, README(root+per-folder) — sinh từ nội dung Stage 3 để link đúng file thật.
- **STAGE 5 Validate:** size ~100 LOC (trần 800→split); cross-link không gãy; front-matter đủ; traceability FR/NFR/INV + TEST-MATRIX.Ref; report (tạo gì/gaps/oversize).
- **STAGE 6 Migrate** (chỉ khi Stage 0 thấy docs cũ): hỏi hấp thụ vào taxonomy / giữ song song / bỏ qua.

Nguyên tắc cốt lõi: **Scout→Content→MAP** (không sinh MAP trước nội dung); chỉ tạo folder khi scout thấy thành phần (chống folder rỗng).
- `references/update-workflow.md`: dùng front-matter `source_files` so code↔doc, sửa phần lệch (thủ công).
- `references/summarize-workflow.md`: tóm tắt nhanh (SOURCE-MAP + DOCUMENT-MAP refresh).

## Related Code Files
- Create: `plugins/morkit/skills/writing-docs/references/{taxonomy,anchor-conventions,init-workflow,update-workflow,summarize-workflow}.md`
- Read: 2 report nguồn (brainstorm + review) để trích quyết định.

## Implementation Steps
1. Viết taxonomy.md từ bảng index + sub-taxonomy trong report review.
2. Viết anchor-conventions.md từ mục "Nguyên tắc template" + "Traceability" trong report review.
3. Viết init-workflow.md (thứ tự sinh + size check + detect docs cũ).
4. Viết update/summarize workflow (gọn, hoãn auto-sync).
5. Cross-check: reference không lặp nội dung doc-templates (templates ở phase 3).

## Success Criteria
- [ ] taxonomy.md liệt kê đủ 6 nhóm + core/conditional/optional + scale rules
- [ ] anchor-conventions.md đủ 4 cơ chế + ID policy + traceability loop
- [ ] init-workflow ép thứ tự "nội dung trước, MAP sau"
- [ ] 5 reference, không lặp chéo

## Risk Assessment
- Reference phình to → mitigate: giữ cô đọng, đẩy chi tiết structure xuống doc-templates.
