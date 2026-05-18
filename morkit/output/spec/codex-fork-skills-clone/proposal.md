# codex-fork-skills-clone

## Why

Morkit plugin hiện được build cho Claude Code, dùng vocab Claude-specific trong skill text (`Skill tool`, `Agent tool`, `TodoWrite`, env var `${CLAUDE_PLUGIN_ROOT}`, ...). Trước đó đã có một lớp runtime-translation qua `AGENTS.md` + `install-codex.sh` để Codex CLI dùng được, nhưng cách này brittle: Codex agent phải tự dịch vocab mỗi lần đọc skill, sót một chỗ là sai; các diagram graphviz nhúng "Invoke Skill tool" trong nhãn không cover được bằng runtime translation.

Cần một path Codex-native — skill/command/hook đọc tự nhiên trên Codex — nhưng KHÔNG được làm vỡ trải nghiệm hiện tại của Claude Code users. Mục tiêu: clone các thành phần cần diverge sang folder song song (`-codex`) trong cùng plugin, giữ folder gốc nguyên trạng.

## What changes

- Tạo `plugins/morkit/skills-codex/` — clone 26 SKILL.md với vocab trung tính (Claude + Codex đều đọc tự nhiên)
- Tạo `plugins/morkit/commands-codex/` — clone 15 command file mirror, bỏ cụm "using the Skill tool"
- Tạo `plugins/morkit/hooks/hooks-codex.json` — schema Codex, matcher `apply_patch|Edit|Write` thay cho `Skill`
- Refactor `pre-tool-checklist-gate.sh` để nhận thêm tool_name `apply_patch|Edit|Write`, gate condition giữ nguyên semantics
- Cascade env vars cross-platform: `${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-fallback}}` + `${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-~/.claude/plugins/data}}` áp cho 8 scripts + 4 hooks + ~13 skills + 1 Python file (skills/ gốc chỉ đổi tên env, không đổi nội dung text). **Lưu ý**: dùng `MORKIT_PLUGIN_ROOT` (KHÔNG dùng `MORKIT_ROOT`) vì `MORKIT_ROOT` đã có nghĩa cũ là spec changes folder (default `morkit/output/spec`) — không thể overload.
- Tạo `plugins/morkit/codex/vocab-map.yaml` — định nghĩa rule swap (Skill tool → skill discovery, Agent tool → delegate to specialist, TodoWrite → task list, ExitPlanMode → present plan + pause, ...)
- Tạo `plugins/morkit/scripts/sync-codex-fork.sh` — helper optional apply vocab swap từ skills/ → skills-codex/
- Tạo `plugins/morkit/scripts/check-codex-drift.sh` — CI guard, warn (không fail) khi skills/ thay đổi mà skills-codex/ chưa sync
- Update `install-codex.sh` — symlink target đổi `skills/` → `skills-codex/`, ghi `~/.codex/hooks.json` từ `hooks-codex.json`
- Update `doctor-codex.sh` — verify `skills-codex/`, `hooks-codex.json` wired
- Update `AGENTS.md` — bridge map đổi `commands/X.md` → `commands-codex/X.md`
- Update `.codex/INSTALL.md` — new install flow
- Update `ci/github-actions.yml` — invoke drift detector trên PR sửa skills/

## Impact

- **Affected components:** `plugins/morkit/skills/` (env var rename only, content untouched), `plugins/morkit/commands/` (zero touch), `plugins/morkit/hooks/hooks.json` (zero touch), `plugins/morkit/scripts/*.sh` (env cascade), `plugins/morkit/hooks/*.sh` (env cascade). NEW: `skills-codex/`, `commands-codex/`, `hooks/hooks-codex.json`, `codex/vocab-map.yaml`, drift scripts.
- **Affected users:**
  - Claude Code users: zero behaviour change (marketplace.json vẫn trỏ `skills/`, `commands/`, `hooks/hooks.json`). Env var refactor là backward-compatible (cascade fallback giữ `CLAUDE_PLUGIN_ROOT`).
  - Codex users: skill/command/hook đọc tự nhiên hơn, không cần Codex agent runtime-translate. `install-codex.sh` rerun để repoint symlink.
- **Migration required:** Yes (Codex users đã cài cần rerun `install-codex.sh`). No migration cho Claude Code users.

## Out of scope

- Generator-based approach (Option 3) — single source + auto-gen `dist-codex/`. Có thể revisit nếu drift trở thành vấn đề nghiêm trọng.
- Full fork `plugins/morkit-codex/` (Option 1) — đã loại trừ vì vi phạm "không động cấu trúc nhiều".
- Codex MCP integration cho `code-review-graph` — giữ degraded mode (Read/Grep fallback) như hiện tại.
- Windows-native install path — POSIX bash giả định; Windows users dùng WSL hoặc Git Bash.
- Refactor `dh-session-start.sh` để dùng XDG paths — defer, hiện hardcode `~/.claude/plugins/data/` vẫn work nhờ env cascade.

---

*Generated: 2026-05-18T07:54:11Z*
