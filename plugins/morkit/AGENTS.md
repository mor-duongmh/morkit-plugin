# morkit — Codex agent guidance

Bạn có quyền truy cập **morkit**, một bộ công cụ all-in-one cho spec workflow, brainstorm/plan/execute, deep code review, và AI-agent doc generation. Skills nằm dưới `~/.agents/skills/morkit/` — symlink tới `plugins/morkit/skills/`, **cùng một nguồn** với bản Claude Code (không fork).

## ⚠️ Chế độ hoạt động trên Codex: ADVISORY (đọc trước khi làm)

morkit thiết kế gốc cho Claude Code, nơi harness **cưỡng chế** guardrail. Codex không có `Skill` tool, không có native slash-command, và (mặc định) không auto-load hook — nên các cơ chế sau là **quy ước (advisory), KHÔNG cưỡng chế**:

- **Review gate** (`propose → review OK → execute → archive`): chỉ cháy nếu bật hooks (`install-codex.sh --with-hooks` + `codex features enable codex_hooks`) VÀ đi qua skill `executing-plans` (export `MORKIT_CURRENT_CHANGE` — xem `codex-tools.md`). Mặc định **gate KHÔNG cháy** → agent + user tự giữ kỷ luật chu trình.
- **Slash command** `/morkit:<name>`: không tự định tuyến — coi như gợi ý (xem mục dưới).
- **Subagent**: dùng native `multi_agent` của Codex (xem `codex-tools.md`).

**Hệ quả:** kỷ luật workflow nằm ở việc bạn chủ động tuân thủ Working agreements bên dưới, không ở hàng rào tự động.

## Skills khả dụng

Codex auto-discover qua `~/.agents/skills/morkit/<name>/SKILL.md`. Skill files dùng Claude Code vocab — dịch sang Codex equivalent qua `using-morkit/references/codex-tools.md`. Invoke bằng cách đề cập tên trong reasoning:

- **Spec workflow**: `propose`, `review`, `archive`
- **Brainstorm/plan/execute**: `brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `test-driven-development`, `systematic-debugging`, `verification-before-completion`, `using-git-worktrees`, `finishing-a-development-branch`, `requesting-code-review`, `receiving-code-review`, `dispatching-parallel-agents`, `writing-skills`, `using-morkit`
- **Deep review**: `deep-review`
- **Docs generation**: `writing-docs` (chế độ init / update / summarize — sinh bộ tài liệu `docs/` tối ưu cho AI agent: taxonomy + anchor, kèm con trỏ vào AGENTS.md/CLAUDE.md ở root)

## Slash-command bridge (Claude Code parity)

Codex không có native slash-command auto-discovery. Khi user gõ `/morkit:<name>` (cú pháp Claude Code), xử lý:

1. Đọc `${MORKIT_PLUGIN_ROOT}/commands/<name>.md` nếu tồn tại
2. Follow nội dung command — đa số chỉ wrap một skill cùng tên
3. Nếu không có command file, fallback sang skill cùng tên trong `~/.agents/skills/morkit/`

## Tool mapping (Claude Code → Codex)

Skill files viết cho Claude Code; khi gặp tool/identifier dưới đây, dịch sang Codex equivalent rồi mới hành động. Chi tiết đầy đủ: `using-morkit/references/codex-tools.md`.

| SKILL.md says | Codex equivalent |
|---|---|
| `Skill tool` / `Invoke Skill tool` | Mention skill name trong reasoning — Codex auto-discover từ `~/.agents/skills/morkit/` |
| `Agent tool` / `subagent_type: X` | Native `spawn_agent` (cần `multi_agent = true` trong `~/.codex/config.toml`) — xem codex-tools.md "Named agent dispatch" |
| `TodoWrite` | `update_plan` (hoặc track nội bộ) |
| `Read` / `Write` / `Edit` | Native — không đổi |
| `Bash` | Codex `shell` tool — không đổi |
| `${CLAUDE_PLUGIN_ROOT}` | Cascade `${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}`; `MORKIT_PLUGIN_ROOT` export bởi `install-codex.sh`. Không cần rewrite file — xem codex-tools.md "Plugin root resolution" |
| `mcp__code-review-graph__*` | Optional — không config thì fallback Read+Grep |
| `ExitPlanMode` / `NotebookEdit` | Không có equivalent — skip hoặc báo user |

## Working agreements

> **Bắt buộc tự giác (Codex không enforce):** coi các điều dưới đây là mệnh lệnh, không phải gợi ý — đây là thứ duy nhất giữ chu trình đúng trên Codex.

- **Trước khi code**: ưu tiên `brainstorming` skill — không nhảy thẳng vào implementation khi yêu cầu chưa rõ
- **Spec change**: chu trình bắt buộc `propose → review-checklist OK → executing-plans → archive`. KHÔNG bỏ qua review gate
- **TDD discipline**: dùng `test-driven-development` skill cho mọi feature/bugfix có thể test được
- **Code review**: gợi ý user chạy `deep-review` skill trước khi merge PR
- **Folder convention**: spec changes sống tại `${MORKIT_ROOT:-morkit/output/spec}/<name>/`. Marker file `.morkit` đánh dấu morkit root

## Deep-review trong Codex

Claude Code dispatch 5–7 specialist subagents song song qua `Agent` tool. Trên Codex dùng **native `multi_agent`**: với mỗi specialist trong `agents/<name>.md`, gọi `spawn_agent(agent_type="worker", message=<nội dung agent .md đã fill placeholder>)`, rồi `wait` và tổng hợp YAML findings thành Markdown matrix. Bật `multi_agent = true` trong `~/.codex/config.toml`. Framing message chi tiết: `codex-tools.md` mục "Named agent dispatch".

Nếu `code-review-graph` MCP không config → specialists chạy degraded mode (Read/Grep).

## Limitations trong Codex

- **Plugin-bundled hooks không auto-load** trong Codex 0.120.0. Hooks của morkit (`hooks/hooks.json`) cần wire vào `~/.codex/hooks.json` với `codex_hooks = true` trong config.toml — hoặc dùng `install-codex.sh --with-hooks`.
- **PreToolUse checklist gate** chỉ hoạt động khi hooks được wire. Nếu chưa wire, agent phải tự verify review-checklist `Overall Decision: OK` trước khi gọi `executing-plans` (xem Advisory ở trên).
- **code-review-graph MCP**: nếu không config trong Codex, deep-review specialists chạy degraded mode (Read/Grep only).
