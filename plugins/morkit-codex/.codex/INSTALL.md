# Installing morkit for Codex CLI

Enable morkit skills + working agreements trong Codex qua native skill discovery + AGENTS.md.

## Prerequisites

- [Codex CLI](https://developers.openai.com/codex/) ≥ 0.120.0 (`codex --version` để kiểm tra)
- Git

## Installation (1-command — native Codex marketplace) ⭐

Nếu Codex CLI version của bạn support `plugin marketplace` (kiểm tra: `codex plugin marketplace --help`):

```bash
codex plugin marketplace add mor-duongmh/claude-plugins
```

Codex sẽ tự:
- Clone repo về cache (`~/.codex/plugins/marketplaces/mor-duongmh/`)
- Đọc `.agents/plugins/marketplace.json` (marketplace index)
- Đọc `plugins/morkit/.codex-plugin/plugin.json` (plugin manifest)
- Auto-discover `plugins/morkit-codex/skills/` + `hooks.json` qua manifest fields
- List plugin `morkit` available để install

Sau đó install plugin (hoặc Codex auto-install nếu UI cho phép):
```bash
# Tuỳ Codex UI/CLI version — có thể là menu, có thể là command
```

Update sau này:
```bash
codex plugin marketplace upgrade mor-duongmh
```

Remove:
```bash
codex plugin marketplace remove mor-duongmh
```

> **Lưu ý**: `codex plugin marketplace` là feature mới của Codex CLI. Nếu command không tồn tại trong CLI version của bạn, dùng installer script ở section dưới.

## Installation (script — works trên mọi Codex ≥ 0.120.0)

```bash
git clone https://github.com/mor-duongmh/claude-plugins.git ~/.codex/morkit-source
bash ~/.codex/morkit-source/plugins/morkit-codex/scripts/install-codex.sh
```

`install-codex.sh` symlink `plugins/morkit-codex/skills/` + AGENTS.md, hỏi (interactive) có bật hooks hay không. Re-runnable an toàn.

Flags: `--yes` (accept defaults, hooks OFF), `--with-hooks` (force enable hooks via `hooks.json`), `--uninstall` (remove symlinks).

> **Bootstrap note**: installer expects `plugins/morkit-codex/skills/` + `plugins/morkit-codex/commands/` đã tồn tại trong checkout. Nếu mới `git clone` xong và thấy lỗi "morkit-codex/skills/ not found", chạy `bash ~/.codex/morkit-source/plugins/morkit/scripts/sync-codex-fork.sh` để generate fork từ `skills/` + `commands/`.

Sau đó verify:
```bash
bash ~/.codex/morkit-source/plugins/morkit-codex/scripts/doctor-codex.sh
```

Restart Codex (quit + relaunch) để discover skills + AGENTS.md.

## Installation (manual — if you prefer)

1. **Clone repo:**
   ```bash
   git clone https://github.com/mor-duongmh/claude-plugins.git ~/.codex/morkit-source
   ```

2. **Symlink skills (bắt buộc):**
   Target là `plugins/morkit-codex/skills/` (Codex fork — đã rewrite `${CLAUDE_PLUGIN_ROOT}` → `${MORKIT_PLUGIN_ROOT}` và vocab khác), **không phải** `skills/` (Claude Code source).
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/morkit-source/plugins/morkit-codex/skills ~/.agents/skills/morkit
   ```

   **Windows (PowerShell):**
   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\morkit" "$env:USERPROFILE\.codex\morkit-source\plugins\morkit-codex\skills"
   ```

   Nếu `plugins/morkit-codex/skills/` không tồn tại trong checkout, chạy trước: `bash ~/.codex/morkit-source/plugins/morkit/scripts/sync-codex-fork.sh`.

3. **Symlink AGENTS.md (khuyến nghị):**
   Để Codex auto-load working agreements + slash-command bridge:
   ```bash
   ln -s ~/.codex/morkit-source/plugins/morkit/AGENTS.md ~/.codex/AGENTS.md
   ```

   Nếu đã có `~/.codex/AGENTS.md`, append nội dung morkit's AGENTS.md vào cuối.

4. **(Optional) Enable hooks:**
   Morkit's `SessionStart` + `PreToolUse` hooks **không auto-load** trong Codex 0.120.0. Cách nhanh nhất là dùng installer flag (tự `cp` / symlink `hooks.json` + enable feature flag):

   ```bash
   bash ~/.codex/morkit-source/plugins/morkit-codex/scripts/install-codex.sh --with-hooks
   ```

   Hoặc thủ công:

   ```bash
   codex features enable codex_hooks
   ln -s ~/.codex/morkit-source/plugins/morkit-codex/hooks/hooks.json ~/.codex/hooks.json
   ```

   `hooks.json` đã được fork sẵn với matcher phù hợp Codex (`apply_patch|shell|Edit|Write` thay vì Claude's `Skill`). Không edit `hooks/hooks.json` (Claude Code source) — nó không match Codex tool names.

5. **Restart Codex** (quit + relaunch CLI) để discover skills + AGENTS.md.

## Verify

```bash
bash ~/.codex/morkit-source/plugins/morkit-codex/scripts/doctor-codex.sh
```

`doctor-codex.sh` check: codex CLI version, skill symlink → `plugins/morkit-codex/skills/` + count ≥ 20, AGENTS.md, hooks state (`hooks.json`), `plugins/morkit-codex/commands/` presence, drift check (`scripts/check-codex-drift.sh`), deep-review prereqs. Exit 0 = healthy, 1 = có FAIL.

Hoặc check thủ công:
```bash
ls -la ~/.agents/skills/morkit
ls -la ~/.codex/AGENTS.md
codex features list | grep codex_hooks
```

Trong Codex CLI:
```
> Liệt kê morkit skills bạn thấy
```
Phải trả về ≥ 25 skills (archive, brainstorming, propose, deep-review, ...).

## Updating

```bash
cd ~/.codex/morkit-source && git pull
```

Skills + AGENTS.md update tức thì qua symlink.

## Uninstalling

```bash
bash ~/.codex/morkit-source/plugins/morkit-codex/scripts/install-codex.sh --uninstall
```

Script chỉ remove các symlink thật sự trỏ vào morkit checkout — file thủ công người dùng tự thêm sẽ được giữ lại. Hooks.json + feature flag cần xoá tay:
```bash
rm ~/.codex/hooks.json          # nếu đã wire hooks
codex features disable codex_hooks
```

Optional: `rm -rf ~/.codex/morkit-source`.

## Deep-review (5-specialist parallel)

Trong Claude Code, `/morkit:deep-review` dispatch parallel subagents qua `Agent` tool. Codex không có subagent native → dùng wrapper bash:

```bash
# Default = git diff HEAD
~/.codex/morkit-source/plugins/morkit/scripts/codex-deep-review.sh

# Other targets
codex-deep-review.sh --diff main     # vs branch
codex-deep-review.sh '#123'          # PR #123 (needs gh)
codex-deep-review.sh --json          # JSON output
codex-deep-review.sh --agents=security-auditor,test-coverage-auditor  # subset
```

**Cách hoạt động**: spawn N `codex exec` processes song song (default: 7 specialists từ `agents/*.md`), mỗi process review cùng một diff trong sandbox read-only, output YAML findings; Python aggregator merge + dedupe + rank → render Markdown.

**Optional alias** để gọi gọn:

```bash
ln -s ~/.codex/morkit-source/plugins/morkit/scripts/codex-deep-review.sh ~/.local/bin/morkit-deep-review
```

Sau đó chỉ cần `morkit-deep-review --diff` từ bất cứ git repo nào.

**Requirements**: `codex ≥ 0.120.0`, `git`, `python3`. `gh` chỉ cần cho PR target.

**Note**: morkit's code-review-graph MCP (Claude Code only) không có equivalent trong Codex. Specialists fall back sang Read/Grep → tốc độ chậm hơn, ít context-aware hơn, nhưng vẫn catch được Security/Convention/Pattern findings cơ bản.

## Differences from Claude Code install

| Aspect | Claude Code | Codex |
|---|---|---|
| Install method | `/plugin install morkit@mor-duongmh` | Clone + symlink (thủ công) |
| Slash commands `/morkit:X` | Native discovery từ `commands/` | Bridge qua AGENTS.md (model đọc `morkit-codex/commands/X.md`) |
| Skills location | `skills/` (auto-discover) | `plugins/morkit-codex/skills/` (fork — symlink target từ `~/.agents/skills/morkit`) |
| Skills auto-invoke | Native via Skill tool | Native via skill discovery |
| Hooks config | `hooks/hooks.json` (auto-load) | `hooks/hooks.json` → wire vào `~/.codex/hooks.json` (qua `--with-hooks`) |
| Env var marker | `${CLAUDE_PLUGIN_ROOT}` | `${MORKIT_PLUGIN_ROOT}` (rewrite tự động trong `plugins/morkit-codex/skills/` + `plugins/morkit-codex/commands/`) |
| Subagents (deep-review specialists) | Native subagent dispatch | `codex exec` parallel wrapper (`scripts/codex-deep-review.sh`) |

## Troubleshooting

- **`morkit-codex/skills/ not found`** khi chạy installer hoặc doctor → checkout chưa có fork. Chạy:
  ```bash
  bash ~/.codex/morkit-source/plugins/morkit/scripts/sync-codex-fork.sh
  ```
  Sau đó re-run installer. Script này regenerate `plugins/morkit-codex/skills/` + `plugins/morkit-codex/commands/` từ `skills/` + `commands/` với vocab Claude→Codex.

- **Doctor báo "symlink expected skills"** → symlink cũ trỏ vào sai chỗ. Fix:
  ```bash
  rm ~/.agents/skills/morkit
  ln -s ~/.codex/morkit-source/plugins/morkit-codex/skills ~/.agents/skills/morkit
  ```

- **Doctor báo "drift"** → user edit trực tiếp `plugins/morkit-codex/skills/` hoặc `skills/` mà không re-sync. Chạy `scripts/check-codex-drift.sh` để xem file nào lệch, rồi `scripts/sync-codex-fork.sh` để regenerate fork.

- **Hooks không trigger** → kiểm tra `codex features list | grep codex_hooks` (phải enabled) và `ls -la ~/.codex/hooks.json` (phải trỏ vào `hooks.json`, không phải `hooks.json` cũ).
