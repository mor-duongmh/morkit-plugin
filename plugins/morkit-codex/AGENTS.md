# morkit — Codex agent guidance

Bạn có quyền truy cập **morkit**, một bộ công cụ all-in-one cho spec workflow, brainstorm/plan/execute, deep code review, và BrSE document generation. Tất cả skills nằm dưới `~/.agents/skills/morkit/`.

## Skills khả dụng

Codex auto-discover qua `~/.agents/skills/morkit/<name>/SKILL.md`. Invoke bằng cách đề cập tên trong reasoning:

- **Spec workflow**: `propose`, `review`, `archive`
- **Brainstorm/plan/execute**: `brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `test-driven-development`, `systematic-debugging`, `verification-before-completion`, `using-git-worktrees`, `finishing-a-development-branch`, `requesting-code-review`, `receiving-code-review`, `dispatching-parallel-agents`, `writing-skills`, `using-morkit`
- **Deep review**: `deep-review`
- **Docs generation**: `docs-hero` (alias của `docs-hero-orchestrator`) và sub-skills `generate-srs`, `generate-api-docs`, `generate-db-design`, `generate-system-architecture`, `generate-code-standards`, `generate-codebase-summary`, `generate-design-guidelines`

## Slash-command bridge (Claude Code parity)

Codex không có native slash command auto-discovery. Khi user gõ pattern `/morkit:<name>` (cú pháp Claude Code), xử lý như sau:

1. Đọc file `${MORKIT_PLUGIN_ROOT}/morkit-codex/commands/<name>.md` nếu tồn tại (Codex fork — các marker `${CLAUDE_PLUGIN_ROOT}` đã được rewrite sang `${MORKIT_PLUGIN_ROOT}` qua `scripts/sync-codex-fork.sh`)
2. Follow nội dung command — đa số chỉ wrap một skill cùng tên
3. Nếu không có command file trong `morkit-codex/commands/`, fallback sang skill cùng tên trong `~/.agents/skills/morkit/`

> **Lưu ý fork**: `commands/` (Claude Code source) **không** được Codex auto-discover. Chỉ `morkit-codex/commands/` là canonical cho Codex; nếu thiếu, chạy `bash ${MORKIT_PLUGIN_ROOT}/scripts/sync-codex-fork.sh` để regenerate từ `commands/`.

## Tool mapping (Claude Code → Codex)

Skill files được viết cho Claude Code; khi đọc một SKILL.md đề cập các tool/identifier dưới đây, dịch sang Codex equivalent rồi mới hành động:

| SKILL.md says | Codex equivalent |
|---|---|
| `Skill tool` / `Invoke Skill tool` | Mention skill name trong reasoning — Codex auto-discover từ `~/.agents/skills/morkit/` |
| `Agent tool` / `subagent_type: X` | Cho code review: dùng `scripts/codex-deep-review.sh`. Cho parallel work khác: chạy `codex exec` trong background hoặc skill chain tuần tự |
| `TodoWrite` / "create TodoWrite todo" | Maintain task list nội bộ trong head (Codex không expose TodoWrite); vẫn track checkpoint giống skill hướng dẫn |
| `Read` / `Write` / `Edit` | Native trong Codex — không thay đổi |
| `Bash` | Codex `shell` tool — không thay đổi |
| `${CLAUDE_PLUGIN_ROOT}` | Trong Codex, canonical env var là **`${MORKIT_PLUGIN_ROOT}`** (export bởi `install-codex.sh` vào shell rc). `morkit-codex/commands/` đã được rewrite sẵn marker này; nếu thấy `${CLAUDE_PLUGIN_ROOT}` trong skill file, treat như alias. Fallback nếu unset: `~/.codex/morkit-source/plugins/morkit` |
| `mcp__code-review-graph__*` | Optional — nếu MCP không config, fallback sang Read+Grep (đã hardcode trong wrapper) |
| `ExitPlanMode` / `NotebookEdit` | Không có equivalent — skip hoặc thông báo user |

## Working agreements

- **Trước khi code**: ưu tiên `brainstorming` skill — không nhảy thẳng vào implementation khi yêu cầu chưa rõ
- **Spec change**: chu trình bắt buộc `propose → review-checklist OK → executing-plans → archive`. KHÔNG bỏ qua review gate
- **TDD discipline**: dùng `test-driven-development` skill cho mọi feature/bugfix có thể test được
- **Code review**: gợi ý user chạy `deep-review` skill trước khi merge PR
- **Folder convention**: spec changes sống tại `${MORKIT_ROOT:-morkit/output/spec}/<name>/`. Marker file `.morkit` đánh dấu morkit root

## Deep-review trong Codex

Claude Code dispatch 5-7 specialist subagents song song qua `Agent` tool. Codex không có native subagent → dùng wrapper bash `scripts/codex-deep-review.sh`:

```bash
$PLUGIN_ROOT/scripts/codex-deep-review.sh --diff        # current uncommitted changes
$PLUGIN_ROOT/scripts/codex-deep-review.sh --diff main   # vs branch
$PLUGIN_ROOT/scripts/codex-deep-review.sh '#123'        # PR #123 via gh
$PLUGIN_ROOT/scripts/codex-deep-review.sh --json        # JSON output
$PLUGIN_ROOT/scripts/codex-deep-review.sh --agents=security-auditor,convention-checker  # subset
```

Cơ chế: wrapper spawn N `codex exec` processes song song (mỗi process 1 specialist từ `agents/<name>.md`), aggregator Python merge YAML findings, render Markdown/JSON. Mỗi specialist chạy độc lập trong sandbox `read-only`.

Khi user yêu cầu `/morkit:deep-review`, ưu tiên gọi wrapper bash thay vì cố mô phỏng subagent dispatch trong một conversation.

## Limitations trong Codex

- **Plugin-bundled hooks không auto-load** trong Codex 0.120.0 (`plugin_hooks` flag chưa tồn tại). Hooks của morkit (`hooks/hooks.json`) cần wire thủ công vào `~/.codex/hooks.json` hoặc `<repo>/.codex/hooks.json` với `codex_hooks = true` trong config.toml — hoặc dùng `install-codex.sh --with-hooks` để tự động
- **PreToolUse checklist gate** chỉ hoạt động khi hooks được wire (xem trên). Nếu chưa wire, agent phải tự verify review-checklist `Overall Decision: OK` trước khi gọi `executing-plans`
- **Deep-review code-review-graph MCP**: nếu MCP không config trong Codex, specialists chạy degraded mode (Read/Grep only)

## Drift detection (morkit-codex/skills/ vs skills/ sync)

`morkit-codex/skills/` và `morkit-codex/commands/` là **fork** auto-generated từ `skills/` + `commands/` qua `scripts/sync-codex-fork.sh` (rewrite vocab Claude→Codex). Nếu user edit trực tiếp một bên mà không re-sync, hai bên drift.

Để verify checkout đang in-sync:

```bash
bash ${MORKIT_PLUGIN_ROOT}/scripts/check-codex-drift.sh
```

Exit 0 = synced; non-zero kèm danh sách file lệch. Khi drift, chạy `scripts/sync-codex-fork.sh` để regenerate `morkit-codex/skills/` + `morkit-codex/commands/` từ source. `doctor-codex.sh` cũng surface drift check trong output tổng.
