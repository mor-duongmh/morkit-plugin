---
title: "morkit writing-docs skill — AI-optimized project docs generator"
status: completed
created: 2026-05-22
source: skill
blockedBy: []
blocks: []
---

# morkit `writing-docs` skill — AI-optimized project docs generator

## Context

Tạo skill morkit `writing-docs` (command `/morkit:docs`) sinh bộ tài liệu dự án tối ưu cho AI agent: dễ đọc, làm **mỏ neo** để agent bám, **phân rã nhỏ + liên kết** để agent nạp đúng context tối thiểu mỗi task. Thay thế `docs-hero` cũ (đã xóa 2026-05-21 — quá nặng: Python venv + parser + diff engine). Lần này KISS: LLM-driven, không Python, 1 skill + references.

Mọi quyết định thiết kế + 30 template skeleton đã chốt qua 2 phiên brainstorm — phase dưới chỉ thực thi, KHÔNG brainstorm lại.

**Reports nguồn (đọc trước khi implement):**
- Thiết kế skill: `plans/reports/brainstorm-260521-1607-morkit-writing-docs-skill.md`
- Review 30 template: `plans/reports/review-260522-0015-morkit-doc-templates-review.md`
- Reference impl đã có: `example/mail-history-admin/` (34 file, ~100 LOC/file)

## Quyết định đã khóa
- Vị trí: `plugins/morkit/skills/writing-docs/` + `plugins/morkit/commands/docs.md`. 1 skill + `references/`, LLM-driven, morkit-native dispatch (KHÔNG phụ thuộc ck:docs-manager).
- Output: `docs/` ở root project đích. Taxonomy core-6, mở rộng khi cần. Hỗ trợ project-level + per-module.
- Mode: `init|update|summarize`, standalone. Sync hoãn (front-matter `source_files` đặt nền).
- Mỏ neo: MAP files + cross-link (chính), front-matter nhẹ, ID (FR/NFR ở FEATURE-LIST, INV ở INVARIANTS → TEST-MATRIX.Ref, BR-### local/SYS-SPEC).
- 30 template (27 + 3 mới: STACK, CODE-STANDARDS, ADR). ARCHITECTURE=arc42-lite, DATA-MAP 2-mode.

## Phases

| # | Phase | Status | Priority | Depends |
|---|-------|--------|----------|---------|
| 01 | [Skill Scaffold & Routing](phase-01-skill-scaffold-routing.md) | completed | P1 | — |
| 02 | [References & Workflows](phase-02-references-workflows.md) | completed | P1 | 01 |
| 03 | [Doc Templates (30 skeletons)](phase-03-doc-templates.md) | completed | P1 | 02 |
| 04 | [Migrate Old Templates & Cleanup](phase-04-migrate-cleanup.md) | completed | P2 | 03 |
| 05 | [Verify Init E2E](phase-05-verify-init.md) | completed | P2 | 03,04 |

## Key dependencies
- Convention morkit: `plugins/morkit/skills/*/SKILL.md` (frontmatter tối giản name+description), `commands/*.md` (chỉ "Invoke skill").
- Tái dùng: `example/mail-history-admin/` (structure) + `example/*-template.md` (5 template cũ → migrate ở phase 04).
- Không Python, không phụ thuộc ck plugin.

## Success criteria (toàn plan)
- `/morkit:docs init` chạy trên 1 codebase thật → sinh core-6 taxonomy, mỗi file <200 LOC, DOCUMENT-MAP + SOURCE-MAP chính xác, cross-link không gãy.
- Skill self-contained trong morkit, không Python/venv.
