# Installing morkit for Codex CLI

Enable morkit skills + working agreements trong Codex qua native skill discovery + AGENTS.md. **Single-source:** Codex dùng chung `plugins/morkit/skills/` với bản Claude Code — không fork, không sync.

## Chế độ Advisory (quan trọng)

Bản Codex chạy **advisory**: review gate, slash-command, subagent-dispatch là *quy ước*, không cưỡng chế như Claude Code (Codex thiếu `Skill`/`Agent` tool và không auto-load hook). Cụ thể:

- Muốn **cưỡng chế review gate** (chặn execute tới khi checklist OK) → cài kèm hooks: `install-codex.sh --with-hooks`. Gate chỉ bắt đường skill `executing-plans`, không bắt edit file trực tiếp.
- Không bật hooks → kỷ luật chu trình do bạn + AGENTS.md giữ.

> Team cần guardrail tự động chặt chẽ → nên dùng bản Claude Code (`/plugin install morkit`). Bản Codex mạnh về *phương pháp + nội dung*, không thay lớp cưỡng chế.

## Prerequisites

- [Codex CLI](https://developers.openai.com/codex/) ≥ 0.120.0 (`codex --version`)
- Git
- (Deep-review subagent) `multi_agent = true` trong `~/.codex/config.toml` — xem dưới

## Installation (1-command — native Codex marketplace) ⭐

Nếu Codex CLI support `plugin marketplace`:

```bash
codex plugin marketplace add mor-duongmh/morkit-plugin
```

Codex đọc `.agents/plugins/marketplace.json` → plugin `morkit` (source `./plugins/morkit`) → auto-discover `skills/` + `hooks.json`.

Update / remove:
```bash
codex plugin marketplace upgrade mor-duongmh
codex plugin marketplace remove mor-duongmh
```

> Nếu CLI version chưa có `plugin marketplace`, dùng installer script dưới.

## Installation (script — mọi Codex ≥ 0.120.0)

```bash
git clone https://github.com/mor-duongmh/morkit-plugin.git ~/.codex/morkit-source
bash ~/.codex/morkit-source/plugins/morkit/scripts/install-codex.sh
```

`install-codex.sh` symlink `plugins/morkit/skills/` → `~/.agents/skills/morkit`, link AGENTS.md, export `MORKIT_PLUGIN_ROOT` vào shell rc, hỏi (interactive) có bật hooks không. Re-runnable an toàn.

Flags: `--yes` (defaults, hooks OFF), `--with-hooks` (enable hooks via `hooks.json`), `--uninstall`.

Verify + restart:
```bash
bash ~/.codex/morkit-source/plugins/morkit/scripts/doctor-codex.sh
# restart Codex (quit + relaunch) để discover skills + AGENTS.md
```

## Installation (manual)

1. **Clone:**
   ```bash
   git clone https://github.com/mor-duongmh/morkit-plugin.git ~/.codex/morkit-source
   ```

2. **Symlink skills:**
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/morkit-source/plugins/morkit/skills ~/.agents/skills/morkit
   ```
   **Windows (PowerShell):**
   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\morkit" "$env:USERPROFILE\.codex\morkit-source\plugins\morkit\skills"
   ```

3. **Symlink AGENTS.md** (working agreements + slash-command bridge + Advisory):
   ```bash
   ln -s ~/.codex/morkit-source/plugins/morkit/AGENTS.md ~/.codex/AGENTS.md
   ```
   Nếu đã có `~/.codex/AGENTS.md`, append nội dung morkit's AGENTS.md vào cuối.

4. **Export plugin root** (để skills resolve `${MORKIT_PLUGIN_ROOT}`):
   ```bash
   echo 'export MORKIT_PLUGIN_ROOT="$HOME/.codex/morkit-source/plugins/morkit"' >> ~/.zshrc  # hoặc .bashrc
   ```

5. **(Optional) Enable hooks** (review-gate cưỡng chế):
   ```bash
   bash ~/.codex/morkit-source/plugins/morkit/scripts/install-codex.sh --with-hooks
   # hoặc thủ công:
   codex features enable codex_hooks
   ln -s ~/.codex/morkit-source/plugins/morkit/hooks/hooks.json ~/.codex/hooks.json
   ```
   `hooks.json` matcher `Skill|apply_patch|Edit|Write` phù hợp cả hai harness.

6. **Restart Codex.**

## Verify

```bash
bash ~/.codex/morkit-source/plugins/morkit/scripts/doctor-codex.sh
```

Check: codex CLI version, skill symlink → `plugins/morkit/skills` + count ≥ 20, AGENTS.md, hooks state, `commands/` presence, deep-review prereqs. Exit 0 = healthy.

Trong Codex: `> Liệt kê morkit skills bạn thấy` → phải trả về ≥ 20 skills.

## Updating

```bash
cd ~/.codex/morkit-source && git pull
```
Skills + AGENTS.md update tức thì qua symlink (không cần re-sync — single source).

## Uninstalling

```bash
bash ~/.codex/morkit-source/plugins/morkit/scripts/install-codex.sh --uninstall
```
Chỉ remove symlink trỏ vào morkit checkout. Hooks.json + feature flag xoá tay nếu đã wire:
```bash
rm ~/.codex/hooks.json
codex features disable codex_hooks
```

## Deep-review (5–7 specialist, native multi_agent)

Trên Codex dùng native `multi_agent` thay vì subagent của Claude. Bật:
```toml
# ~/.codex/config.toml
[features]
multi_agent = true
```
Khi chạy `deep-review`: với mỗi specialist trong `agents/<name>.md`, agent gọi `spawn_agent(agent_type="worker", message=<nội dung agent .md>)`, `wait`, rồi tổng hợp YAML findings → Markdown matrix. Chi tiết: `skills/using-morkit/references/codex-tools.md` mục "Named agent dispatch".

Nếu `code-review-graph` MCP không config → specialists degraded mode (Read/Grep).

## Differences from Claude Code install

| Aspect | Claude Code | Codex |
|---|---|---|
| Install | `/plugin install morkit` | Clone + symlink |
| Skills location | `plugins/morkit/skills/` (auto-discover) | `plugins/morkit/skills/` (symlink `~/.agents/skills/morkit`) — **cùng nguồn** |
| Skill vocab | Native | Claude vocab + dịch qua `codex-tools.md` |
| Slash `/morkit:X` | Native discovery | Bridge qua AGENTS.md (đọc `commands/X.md`) |
| Subagents | Native `Agent` tool | Native `multi_agent` (`spawn_agent`) |
| Hooks | `hooks.json` auto-load | `hooks.json` → `~/.codex/hooks.json` (`--with-hooks`) |
| Review gate | Cưỡng chế | Advisory (xem trên) |

## Troubleshooting

- **`skills/ not found`** → checkout chưa đầy đủ; `git pull` lại.
- **Doctor báo "symlink expected skills"** → repoint:
  ```bash
  rm ~/.agents/skills/morkit
  ln -s ~/.codex/morkit-source/plugins/morkit/skills ~/.agents/skills/morkit
  ```
- **Hooks không trigger** → `codex features list | grep codex_hooks` (phải enabled) + `ls -la ~/.codex/hooks.json` (phải trỏ vào morkit's hooks.json).
- **Deep-review không spawn subagent** → kiểm tra `multi_agent = true` trong `~/.codex/config.toml`.
