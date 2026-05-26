---
phase: 3
title: "Templates, anchors + versioning"
status: completed
priority: P2
effort: "2-3h"
dependencies: [1, 2]
---

# Phase 3: Templates, anchors + versioning

## Overview
Hợp nhất hai tính năng: ghi canonical-source rule meta vào DOCUMENT-MAP template, làm copy "brownfield or greenfield" thành thật + flag, thêm sequencing note "docs update trước archive", bump plugin version.

## Requirements
- Functional: template/command/skill phản ánh đúng hành vi mới; version bump.
- Non-functional: DRY (không lặp rule đã ở workflow); chỉ thêm meta-pointer ở template.

## Architecture

**DOCUMENT-MAP template:** mục "Canonical Source Rules" hiện có (dòng 67-75) đang nói về *source-of-truth theo concern code* (route truth: router.ts). Thêm 1 hint NGẮN phân tầng nguồn DOC (meta), tránh lặp toàn bộ rule:
```
<!-- hint: doc-source canonical — HOW từ code; WHY từ design.md/ADR; WHAT từ spec.md/FEATURE-LIST. Khi lệch → drift. -->
```
KHÔNG nhồi cả bảng (đã nằm ở update-workflow). Giữ template ~100 LOC.

**Command copy:** `commands/init.md` đang ghi "brownfield or greenfield" — giờ đúng. Bổ sung mô tả ngắn nhánh greenfield + (nếu chốt ở Phase 1) flag `--seed-intent` cho STACK/ARCH. Đồng bộ `flags pass through` nếu thêm flag.

**Sequencing note:** "chạy `/morkit:docs update` TRƯỚC `/morkit:archive`" — đặt ở nơi mô tả vòng đời change. Ứng viên: `skills/using-morkit/SKILL.md` (hoặc reference của nó) + nhắc lại 1 dòng trong `commands/archive.md` ("Tip: chạy /morkit:docs update trước để bắt rationale/spec vào docs").

**Version:** `1.6.0 → 1.7.0` (minor: thêm hành vi, không breaking). Cả `.claude-plugin/plugin.json` + `.codex-plugin/plugin.json`.

## Related Code Files
- Modify: `plugins/morkit/skills/writing-docs/references/doc-templates/00-overview/DOCUMENT-MAP.md` (hint doc-source canonical)
- Modify: `plugins/morkit/commands/init.md` (mô tả greenfield + flag nếu có)
- Modify: `plugins/morkit/skills/using-morkit/SKILL.md` (hoặc reference) — sequencing note
- Modify: `plugins/morkit/commands/archive.md` (1 dòng tip "docs update trước archive")
- Modify: `plugins/morkit/.claude-plugin/plugin.json` + `plugins/morkit/.codex-plugin/plugin.json` (version 1.7.0)

## Implementation Steps
1. Đọc các file đích để khớp giọng + xác nhận vị trí chèn (đặc biệt `using-morkit` mô tả vòng đời ở đâu).
2. Thêm hint doc-source canonical vào DOCUMENT-MAP template (ngắn, không lặp).
3. Cập nhật `init.md` (greenfield + flag); đồng bộ dòng "Flags pass through".
4. Thêm sequencing note (using-morkit + tip ở archive.md).
5. Bump version 1.7.0 ở cả 2 plugin.json.
6. (Nếu Phase 1 thêm flag) đồng bộ tên flag ở init.md ↔ SKILL.md ↔ init-workflow.md.

## Success Criteria
- [ ] DOCUMENT-MAP template có hint doc-source canonical, không lặp bảng workflow, vẫn ~100 LOC.
- [ ] `init.md` mô tả đúng greenfield + flag (nếu có), copy không còn "hứa suông".
- [ ] Sequencing note "docs update trước archive" xuất hiện ở using-morkit + tip archive.md.
- [ ] Cả 2 plugin.json = 1.7.0, đồng nhất.
- [ ] Tên flag nhất quán across init.md/SKILL.md/init-workflow.md.

## Risk Assessment
- **Lặp rule (vi phạm DRY)** → mitigation: template chỉ pointer/hint; rule đầy đủ ở update-workflow.
- **Quên 1 trong 2 plugin.json** → mitigation: checklist 2 file; grep version sau khi sửa.
- **Docs site lệch** → ngoài scope (thuộc plan 260526-0930 re-sync); chỉ ghi note bàn giao.
