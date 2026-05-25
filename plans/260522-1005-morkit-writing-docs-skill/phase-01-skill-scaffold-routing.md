---
phase: 1
title: "Skill Scaffold & Routing"
status: completed
priority: P1
effort: "3h"
dependencies: []
---

# Phase 1: Skill Scaffold & Routing

## Overview
Dựng khung skill `writing-docs` trong morkit: SKILL.md router (init|update|summarize), command `/morkit:docs`, đăng ký plugin, dọn rác docs-hero còn sót.

## Requirements
- Functional: `/morkit:docs [init|update|summarize]` route đúng tới reference workflow; không tham số → AskUserQuestion chọn operation.
- Non-functional: theo convention morkit (frontmatter tối giản `name`+`description`); KHÔNG Python; self-contained.

## Architecture
- `SKILL.md` = router mỏng: parse arg đầu → load `references/{mode}-workflow.md`. Shared Context mô tả taxonomy core-6 + output `docs/` project đích.
- `commands/docs.md` = chỉ "Invoke the `writing-docs` skill, pass args" (giống commands morkit khác).
- Dispatch morkit-native (Task tool inline / skill `dispatching-parallel-agents`), KHÔNG gọi ck:docs-manager.

## Related Code Files
- Create: `plugins/morkit/skills/writing-docs/SKILL.md`
- Create: `plugins/morkit/commands/docs.md`
- Modify: `plugins/morkit/README.md` (thêm dòng command), `plugins/morkit/.claude-plugin/plugin.json` (keywords nếu cần)
- Delete: `plugins/docs-hero/.pytest_cache/` (untracked leftover)
- Read for convention: `plugins/morkit/skills/brainstorming/SKILL.md`, `plugins/morkit/commands/brainstorming.md`

## Implementation Steps
1. Đọc 1-2 SKILL.md + command morkit hiện có để khớp style/frontmatter.
2. Viết `SKILL.md`: frontmatter `name: writing-docs` + description; Default (no-arg → AskUserQuestion); routing table init|update|summarize → references; Shared Context (taxonomy core-6, output docs/, core/conditional/optional, ~100 LOC/file); ràng buộc "không implement code, không Python".
3. Viết `commands/docs.md` (frontmatter `name: "morkit:docs"` + invoke skill).
4. Cập nhật README morkit + plugin.json.
5. `rm -rf plugins/docs-hero/.pytest_cache` (xác nhận untracked trước khi xóa).

## Success Criteria
- [ ] `/morkit:docs` (no-arg) hiện AskUserQuestion 3 mode
- [ ] `/morkit:docs init` load đúng init-workflow
- [ ] Frontmatter + style khớp convention morkit
- [ ] Không còn rác docs-hero, không ref Python

## Risk Assessment
- Style lệch convention morkit → mitigate: đọc skill mẫu trước. Rủi ro thấp.
