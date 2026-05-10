# Mor Claude Plugins

> Marketplace plugin Claude Code của Mor — spec-driven, TDD-first, vendored Superpowers.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Cài đặt

Yêu cầu: [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) + Node.js ≥ 18.

```
/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install mor-kit@mor-duongmh
/plugin install superpowers@mor-duongmh
```

> `superpowers@mor-duongmh` là bản vendored fork của [obra/superpowers](https://github.com/obra/superpowers). Cùng plugin name → không cài đồng thời với upstream.

## Verify install

```bash
# 1. Marketplace có cả plugin
ls ~/.claude/plugins/marketplaces/mor-duongmh

# 2. Skills available trong session — gõ trong Claude Code:
#    "List skills with namespace superpowers:"  → 14 upstream skills
#    "List skills with namespace mor-kit:"       → 3 skills (propose, review, archive)

# 3. Slash commands available
#    /mor-kit:propose --help   → invoke propose skill
#    /superpowers:brainstorm   → invoke upstream brainstorming skill

# 4. Companion tools state (sau session đầu tiên)
ls ~/.claude/plugins/data/mor-kit/.tools-setup-* 2>/dev/null
# .tools-setup-done   = đã setup (RTK đã cài hoặc skip)
# .tools-setup-skip   = "don't ask again"
```

## Workflow at a glance

> **`mor-kit` is self-contained.** Marketplace install = ready in any project. No per-project setup, no schema copy. Brainstorming and execution come from `superpowers` (no duplication).

```
   ┌─────────────────────────────────────────────────────────────────┐
   │  /superpowers:brainstorm   (think before committing)             │
   └────────────────────────────┬────────────────────────────────────┘
                                ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │  /mor-kit:propose                                                │
   │    → mor-kit/changes/<name>/proposal.md   (what & why)           │
   │    → mor-kit/changes/<name>/design.md     (how + Tech Stack)     │
   │    → mor-kit/changes/<name>/tasks.md      (Superpowers + TDD)    │
   │    → mor-kit/changes/<name>/.meta.json    (name, schema, etc)    │
   │    → review-checklist.md   (auto: BE/FE × Feat/Bug/Refactor)     │
   └────────────────────────────┬────────────────────────────────────┘
                                ▼
              🚦 HUMAN GATE — review-checklist.md
                    Tick items, fill summary,
                    set "Overall Decision: OK"
                                │
              [Plugin's PreToolUse hook + skill-level check
               BLOCK every implementation skill until OK]
                                ▼
                                ▼
   /superpowers:execute-plan   (or  subagent-driven-development)
                                ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │  /mor-kit:archive          (after merge)                         │
   └─────────────────────────────────────────────────────────────────┘
```

**Folder convention:** `mor-kit/changes/<name>/` (active) and `mor-kit/changes/archive/<name>/` (archived). Marker file `mor-kit/changes/.mor-kit` distinguishes plugin-owned `mor-kit/` from any other tooling. Override via `MOR_KIT_ROOT` env.

> Need to regenerate or refresh the checklist for an existing change?
> Run **`/mor-kit:review`** (auto-detects variant) or **`/mor-kit:review --variant FE-BugFix --refresh`**.

## Plugins

| Plugin | Mục đích |
|--------|----------|
| [`mor-kit`](./plugins/mor-kit) | **Self-contained spec-driven toolkit.** Scaffold proposal/design/tasks dưới `mor-kit/changes/<name>/` + Google-Doc-driven review-checklist gate. Không duplicate brainstorming hay execution — pair với `superpowers`. |
| [`superpowers`](./plugins/superpowers) | Vendored fork của obra/superpowers, sync qua script. **6 high-ROI skills (`brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `systematic-debugging`, `test-driven-development`) đã được overlay với Context7 research guidance** — agent sẽ tự verify library API thay vì hallucinate. Custom thêm qua `overlay/`. |
| [`deep-review`](./plugins/deep-review) | Multi-language deep code review agent: chạy 5 specialist subagents (risk, security, pattern, tests, convention) song song trên git diff hoặc PR. Powered by [code-review-graph](https://github.com/tirth8205/code-review-graph) MCP (bundled qua `uvx`). Ưu tiên `CLAUDE.md` của project hơn language profile mặc định. |
| [`docs-hero`](./plugins/docs-hero) | BrSE document generation: SRS + API + DB cho ITO Japan offshore. Init/update/sync với conflict-minimal diff engine. Synergy với `mor-kit`: `/mor-kit:propose` → `/docs-hero:update --from-openspec`. Python venv tại `~/.claude/plugins/data/docs-hero/.venv` (one-time `/docs-hero:setup`). |

## Slash commands

| Command | Plugin | Mục đích |
|---------|--------|----------|
| `/mor-kit:propose [desc]` | mor-kit | Sinh proposal + design + tasks (TDD) **+ review-checklist** |
| `/mor-kit:review [name]` | mor-kit | (Re)generate developer review checklist (human gate) |
| `/mor-kit:archive [name]` | mor-kit | Đóng change sau merge |
| `/superpowers:brainstorm` | superpowers | Brainstorming skill — thay thế `/spec:brainstorm` của v1/v2 |
| `/superpowers:write-plan` | superpowers | Writing-plans skill |
| `/superpowers:execute-plan` | superpowers | Executing-plans skill — gated bởi mor-kit's review-checklist |
| `/deep-review [target]` | deep-review | Chạy deep code review trên PR hoặc git diff (5 subagents song song) |
| `/deep-review-doctor` | deep-review | Kiểm tra trạng thái cài đặt deep-review (uvx, code-review-graph, gh, graph build) |
| `/docs-hero:setup` | docs-hero | Bootstrap Python venv (~30-60s, one-time) |
| `/docs-hero:init` | docs-hero | Generate fresh SRS + API docs + DB design from ProjectModel JSON |
| `/docs-hero:update` | docs-hero | Apply OpenSpec change or brainstorm plan to docs (preserves manual edits) |
| `/docs-hero:sync` | docs-hero | Scan codebase, propose changes to API + DB docs (read-only) |
| `/docs-hero:apply-sync` | docs-hero | Apply user-approved sync proposal (ticked checkboxes) |
| `/docs-hero:doctor` | docs-hero | Health-check installation |

Workflow điển hình: `/superpowers:brainstorm` → `/mor-kit:propose` → tick review-checklist → `/superpowers:execute-plan` (hoặc `subagent-driven-development`) → `/deep-review --diff` → `/mor-kit:archive`.

## Schema `superpowers-driven` khác default ở 3 chỗ

1. `design.md` bắt buộc section **`## Tech Stack`**.
2. `tasks.md` mở đầu bằng **Superpowers header** + chú thích `REQUIRED SUB-SKILL`.
3. Mỗi task group có **Files block** + **5 bước TDD bắt buộc**.

`mor-kit:review` dùng `validate-tasks.sh` để check rules R1-R6 — bash regex không phụ thuộc OpenSpec CLI.

## Migration

### From spec@mor-duongmh v1 (OpenSpec) → mor-kit@mor-duongmh

```bash
# Preview
bash ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-from-openspec.sh --dry-run

# Execute
bash ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-from-openspec.sh
```

Script `mv openspec/changes` → `mor-kit/changes`, preserve `archive/` subfolder, ensure `.mor-kit` marker. Hook có dual-read fallback một version cho legacy `openspec/changes/` — sau migration thì mor-kit sẽ là primary.

### From spec@mor-duongmh v0.x

Plugin trước đây có command `/spec:setup`, `/spec:apply`, `/spec:brainstorm` — đã bỏ trong `mor-kit@1.0.0`. Replacements:
- `/spec:setup` → không cần (self-contained)
- `/spec:apply` → `/superpowers:execute-plan` hoặc `subagent-driven-development`
- `/spec:brainstorm` → `/superpowers:brainstorm`

## Plan review gate

Sau `/mor-kit:propose`, plugin tự sinh `mor-kit/changes/<name>/review-checklist.md` từ canonical [Mor Developer Review Checklist Google Doc](https://docs.google.com/document/d/184wY2N2WOUExmZrClvHCfcRCnSQsJYvav6gc6JwL6xc) — auto-detect variant (BE/FE × Feature/BugFix/Refactor), fetch live (cache 24h), điền meta header, mặc định `Overall Decision: PENDING`.

**Hai layer enforcement:**

| Layer | Cơ chế | Khi nào fire |
|-------|--------|-------------|
| **PreToolUse hook** | `pre-tool-checklist-gate.sh` — Claude Code harness chặn tool call | Khi Claude invoke `Skill superpowers:executing-plans` / `subagent-driven-development` (hoặc legacy openspec-apply-change) |
| **Skill content** | Mỗi skill có pre-flight check ở Step 0 — refuse to proceed | Khi skill tự đọc nội dung của mình |

Defense-in-depth: nếu một layer bị bypass, layer kia vẫn block.

**Override variant:** `/mor-kit:review --variant FE-BugFix` (BE-Feature, BE-BugFix, BE-Refactor, FE-Feature, FE-BugFix, FE-Refactor)
**Refresh source:** `/mor-kit:review --refresh` (force re-fetch Google Doc, bypass cache)

```diff
- Overall Decision: PENDING
+ Overall Decision: OK
```
→ Implementation skills mở khoá.

## Companion tools (Context7 + RTK)

| Tool | Vai trò | Cài kiểu nào |
|------|---------|-------------|
| **[Context7](https://github.com/upstash/context7)** | Trả về docs/API version-specific cho library, tránh hallucinated calls | **Lazy via npx** — không cần cài trước. Plugin gọi `npx -y ctx7 library ... && npx -y ctx7 docs ...`. MCP optional. |
| **[RTK](https://github.com/rtk-ai/rtk)** | Rewrite + nén output Bash → giảm 60-90% tokens | **Ask once** — session đầu tiên, plugin hỏi user qua AskUserQuestion. |

> **🎯 Context7 đã active trong 6 high-ROI Superpowers skills + 3 mor-kit skills** — agent sẽ tự gọi Context7 thay vì đoán API.

State files trong `~/.claude/plugins/data/mor-kit/`:
- `.tools-setup-done` — đã setup hoặc skip
- `.tools-setup-skip` — không hỏi nữa

Cài RTK thủ công:
```bash
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
rtk init -g
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

> ⚠️ **Reconcile overlay khi sync upstream version mới.** 6 skills đang có overlay. Overlay dùng full-file replace mode → mất upstream changes nếu không reconcile.

## Troubleshooting

- **Đã cài `spec@mor-duongmh` trước đó** → `/plugin uninstall spec@mor-duongmh` rồi `/plugin install mor-kit@mor-duongmh`. Migrate `openspec/changes/` → `mor-kit/changes/` qua `migrate-from-openspec.sh`.
- **Đã cài upstream `superpowers@obra` trước đó** → `/plugin uninstall superpowers@obra` rồi cài lại Mor's bản.
- **CI/CD chạy `npx openspec`** → không còn cần; remove từ pipeline.

## License

[MIT](LICENSE) © Mor. See [plugins/superpowers/ATTRIBUTION.md](plugins/superpowers/ATTRIBUTION.md) for upstream attribution.
