# Mor Claude Plugins

> Marketplace plugin Claude Code của Mor — spec-driven, TDD-first, vendored Superpowers.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Cài đặt

Yêu cầu: [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) + Node.js ≥ 18.

```
/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install spec@mor-duongmh
/plugin install superpowers@mor-duongmh
```

> `superpowers@mor-duongmh` là bản vendored fork của [obra/superpowers](https://github.com/obra/superpowers). Cùng plugin name → không cài đồng thời với upstream.

## Verify install

Sau 3 lệnh trên, kiểm tra mọi thứ đúng:

```bash
# 1. Marketplace có cả 2 plugin
ls ~/.claude/plugins/marketplaces/mor-duongmh

# 2. Skills available trong session — gõ trong Claude Code:
#    "List skills with namespace superpowers:"
#    Phải thấy 14 skills (brainstorming, executing-plans, ...)
#    "List skills with namespace spec:" → 5 skills (openspec-*, spec-setup)

# 3. Slash commands available
#    /spec:setup --help     → in usage
#    /superpowers:brainstorm → invoke brainstorming skill

# 4. Companion tools state (sau session đầu tiên)
ls ~/.claude/plugins/data/spec/.tools-setup-* 2>/dev/null
# .tools-setup-done   = đã setup (RTK đã cài hoặc skip)
# .tools-setup-skip   = "don't ask again"
```

## Workflow at a glance

```
   ┌─────────────────────────────────────────────────────────────────┐
   │  /spec:explore         (optional — think before committing)      │
   └────────────────────────────┬────────────────────────────────────┘
                                ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │  /spec:propose                                                   │
   │    → proposal.md  (what & why)                                   │
   │    → design.md    (how + Tech Stack — verified via Context7)     │
   │    → tasks.md     (Superpowers header + Files block + TDD steps) │
   └────────────────────────────┬────────────────────────────────────┘
                                ▼
       ┌────────────────────────┼────────────────────────┐
       ▼                        ▼                        ▼
   /spec:apply       /superpowers:execute-plan    /superpowers:
   (native runner)    (single agent, TDD)          subagent-driven-
                                                    development
                                                    (parallel agents)
                                ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │  /spec:archive          (after merge)                            │
   └─────────────────────────────────────────────────────────────────┘
```

## Plugins

| Plugin | Mục đích |
|--------|----------|
| [`spec`](./plugins/spec) | Spec-driven workflow trên OpenSpec với schema `superpowers-driven`. Artifacts plug thẳng vào Superpowers. |
| [`superpowers`](./plugins/superpowers) | Vendored fork của obra/superpowers, sync qua script. **6 high-ROI skills (`brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `systematic-debugging`, `test-driven-development`) đã được overlay với Context7 research guidance** — agent sẽ tự verify library API thay vì hallucinate. Custom thêm qua `overlay/`. |

## Slash commands

| Command | Plugin | Mục đích |
|---------|--------|----------|
| `/spec:setup [path]` | spec | Cài schema vào project |
| `/spec:explore` | spec | Suy nghĩ trước khi implement |
| `/spec:propose [desc]` | spec | Sinh proposal + design + tasks (TDD) |
| `/spec:apply [name]` | spec | Native runner thực thi tasks |
| `/spec:archive [name]` | spec | Đóng change sau merge |
| `/superpowers:brainstorm` | superpowers | Brainstorming skill |
| `/superpowers:write-plan` | superpowers | Writing-plans skill |
| `/superpowers:execute-plan` | superpowers | Executing-plans skill |

Workflow điển hình: `/spec:propose` → `tasks.md` ready-for-Superpowers → `/superpowers:execute-plan` (hoặc `subagent-driven-development`).

## Schema `superpowers-driven` khác default ở 3 chỗ

1. `design.md` bắt buộc section **`## Tech Stack`**.
2. `tasks.md` mở đầu bằng **Superpowers header** + chú thích `REQUIRED SUB-SKILL`.
3. Mỗi task group có **Files block** + **5 bước TDD bắt buộc**.

## Auto-suggestion

Project có `openspec/` nhưng chưa cài schema → plugin gợi ý `/spec:setup` ở đầu session. Tắt vĩnh viễn:

```bash
touch openspec/.spec-setup-skip
```

## Companion tools (Context7 + RTK)

Hai tool optional làm tăng chất lượng research và giảm token consumption — plugin tự dò khi mở session đầu tiên và xử lý lịch sự:

| Tool | Vai trò | Cài kiểu nào |
|------|---------|-------------|
| **[Context7](https://github.com/upstash/context7)** | Trả về docs/API version-specific cho library, tránh hallucinated calls | **Lazy via npx** — không cần cài trước. Skill gọi `npx -y ctx7 library ... && npx -y ctx7 docs ...` (two-step: resolve ID rồi query docs). Nếu user đã setup MCP (`mcp.context7.com`), plugin tự ưu tiên dùng MCP tools `mcp__context7__resolve-library-id` + `mcp__context7__query-docs`. |
| **[RTK](https://github.com/rtk-ai/rtk)** | Rewrite + nén output Bash → giảm 60-90% tokens | **Ask once** — session đầu tiên, plugin hỏi user qua AskUserQuestion: cài RTK ngay không? User chọn `Yes`/`Skip`/`Don't ask again`. Không tự cài silent. |

> **🎯 Context7 đã active trong 6 high-ROI Superpowers skills sau khi cài** — `brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `systematic-debugging`, `test-driven-development`. Khi gặp library API không chắc chắn, agent sẽ tự gọi Context7 (qua MCP nếu có, fallback `npx`) thay vì đoán. Cộng với 3 Mor skills (`/spec:explore`, `/spec:propose`, `/spec:apply`) → **9 skills tổng có Context7 guidance built-in**.

State files trong `~/.claude/plugins/data/spec/`:
- `.tools-setup-done` — đã setup hoặc skip
- `.tools-setup-skip` — không hỏi nữa

Cài RTK thủ công bất kỳ lúc nào:
```bash
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
rtk init -g
```

Cài Context7 dạng MCP (full features qua OAuth):
```bash
npx -y ctx7 setup
```

## Sync upstream Superpowers

```bash
cd plugins/superpowers
./scripts/sync-superpowers.sh                    # use pinned version
./scripts/sync-superpowers.sh 5.1.0              # bump
./scripts/sync-superpowers.sh --dry-run 5.1.0    # preview
./scripts/verify-vendor.sh                       # check sha256 still matches
```

Customization → đọc [plugins/superpowers/overlay/README.md](plugins/superpowers/overlay/README.md).

> ⚠️ **Reconcile overlay khi sync upstream version mới.** 6 skills đang có overlay (`brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `systematic-debugging`, `test-driven-development`). Overlay dùng full-file replace mode → nếu upstream cập nhật chính SKILL.md của 6 skills này, sync sẽ ghi đè bản upstream bằng overlay (giữ Mor's customization, mất upstream changes).
>
> **Sau mỗi sync version mới:**
> 1. Xem `.overlay-meta.json` mỗi overlay → ghi `based_on_upstream_version` cũ.
> 2. Diff manually giữa upstream new vs overlay để biết upstream sửa gì cần merge vào.
> 3. Cập nhật `overlay/skills/<name>/SKILL.md` với upstream changes + giữ Mor's appended block.
> 4. Update `.overlay-meta.json` → `based_on_upstream_version` thành version mới.
> 5. Run `sync-superpowers.sh` lại để apply overlay đã reconcile.
>
> Drift detection tự động — defer cho v2 sync script.

## Troubleshooting

- **Commands hiện `/mor-openspec:*` thay vì `/spec:*`** → `/plugin update spec@mor-duongmh`.
- **`schema validate` báo lỗi** → xóa `openspec/schemas/superpowers-driven/` và chạy lại `/spec:setup`.
- **Đã cài upstream `superpowers@obra` trước đó** → `/plugin uninstall superpowers@obra` rồi cài lại Mor's bản.

## License

[MIT](LICENSE) © Mor. See [plugins/superpowers/ATTRIBUTION.md](plugins/superpowers/ATTRIBUTION.md) for upstream attribution.
