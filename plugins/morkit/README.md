# morkit — Mor's all-in-one toolkit (Claude Code + Codex)

> Một plugin, một namespace `/morkit:*` — từ spec & brainstorm đến execute và code review.

## Cài đặt

### Claude Code

```
/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install morkit@mor-duongmh
```

Cài xong là dùng được — không cần setup gì thêm trong project.

### Codex CLI

**Native plugin marketplace** (Codex CLI ≥ 0.131):

```bash
codex plugin marketplace add mor-duongmh/claude-plugins
```

Codex sẽ list 2 plugins: `morkit` (Claude Code variant) và `morkit-codex` (Codex variant). **Codex users install `morkit-codex`** (skills + vocab Codex-friendly, hooks gate dùng matcher `apply_patch|Edit|Write`).

**Script install** (Codex < 0.131 hoặc fallback):

```bash
git clone https://github.com/mor-duongmh/claude-plugins.git ~/.codex/morkit-source
bash ~/.codex/morkit-source/plugins/morkit-codex/scripts/install-codex.sh
```

Verify: `bash ~/.codex/morkit-source/plugins/morkit-codex/scripts/doctor-codex.sh`. Chi tiết: [plugins/morkit-codex/.codex/INSTALL.md](../morkit-codex/.codex/INSTALL.md).

## Claude Code vs Codex CLI

| Aspect | Claude Code | Codex CLI |
|---|---|---|
| Install | `/plugin install morkit@mor-duongmh` | `codex plugin marketplace add mor-duongmh/claude-plugins` → install **`morkit-codex`** |
| Plugin folder | `plugins/morkit/` | `plugins/morkit-codex/` (**tách riêng**, không phải sub-folder) |
| Skills | `plugins/morkit/skills/` (Claude vocab) | `plugins/morkit-codex/skills/` (vocab-translated) |
| Commands | `plugins/morkit/commands/` | `plugins/morkit-codex/commands/` (suffix-stripped) |
| Hooks | `plugins/morkit/hooks/hooks.json` | `plugins/morkit-codex/hooks/hooks.json` (multi-tool gate matcher) |
| Slash | Native `/morkit:X` | `$morkit:X` picker hoặc AGENTS.md bridge cho `/morkit:X` |
| Doctor | `/plugin doctor` | `bash plugins/morkit-codex/scripts/doctor-codex.sh` |

### Separate-plugin approach (vì sao có `plugins/morkit-codex/`)

Claude Code và Codex CLI dùng vocab + tool naming khác nhau (`Skill tool` vs skill discovery, `TodoWrite` vs to-do, `ExitPlanMode` vs plan-confirm...). Earlier iteration đã thử sibling-folder pattern (`skills/` + `skills-codex/` trong cùng `plugins/morkit/`) — nhưng Codex CLI 0.130 walks ANY `skills/` directory inside an installed plugin folder, kể cả khi plugin.json explicitly declares `"skills": "./skills-codex/"`. Kết quả: mỗi skill xuất hiện 2 lần trong picker. Fix: tách hoàn toàn 2 plugins (`morkit/` cho CC, `morkit-codex/` cho Codex). Mỗi plugin có `skills/` riêng. Codex chỉ install plugin nó cần → no duplicate. CC users hoàn toàn không bị ảnh hưởng (marketplace.json giờ list 2 plugin tách biệt).

`plugins/morkit-codex/` được sinh **deterministically** từ `plugins/morkit/` qua `scripts/sync-codex-fork.sh` với vocab map `codex/vocab-map.yaml`. Tài liệu chi tiết: [`plugins/morkit-codex/AGENTS.md`](../morkit-codex/AGENTS.md), [`plugins/morkit-codex/.codex/INSTALL.md`](../morkit-codex/.codex/INSTALL.md).

**Cho contributors edit `plugins/morkit/skills/` hoặc `plugins/morkit/commands/`**: chạy `bash scripts/check-codex-drift.sh` trước khi commit để CI không cảnh báo về sự lệch giữa CC plugin và Codex plugin. Nếu drift, chạy `bash scripts/sync-codex-fork.sh` để regenerate `plugins/morkit-codex/skills/` + `plugins/morkit-codex/commands/` + baselines.

## Quy trình điển hình

```
/morkit:brainstorming         → suy nghĩ trước khi code
        ↓
/morkit:propose               → scaffold proposal + design + tasks + review-checklist
        ↓
🚦 Mở review-checklist.md, tick mục, đặt "Overall Decision: OK"
        ↓
/morkit:executing-plans       → chạy plan, code TDD
   (hoặc /morkit:subagent-driven-development cho parallel agents)
        ↓
/morkit:deep-review            → review code (5 chuyên gia AI song song)
        ↓
/morkit:archive                → đóng change sau khi merge
```

## Folder convention

`morkit/output/spec/<name>/` (active) hoặc `morkit/output/spec/archive/<name>/` (đã archive).
- Marker: `.morkit` trong root folder
- Override path: `MORKIT_ROOT=path/to/changes` env var

## Tất cả slash command (sau merge)

### Spec workflow (từ mor-kit)
| Command | Việc |
|---|---|
| `/morkit:propose [desc]` | Sinh proposal + design + tasks + review-checklist |
| `/morkit:review [name]` | Tạo lại review-checklist từ Google Doc |
| `/morkit:archive [name]` | Đóng change sau merge |

### Brainstorm + execute (brainstorm/plan/execute, vendored)
14 skills under `/morkit:` namespace. Most-used:
- `/morkit:brainstorming` — suy nghĩ + investigate codebase, không code
- `/morkit:writing-plans` — viết plan từ ý tưởng
- `/morkit:executing-plans` — thực thi plan từng bước
- `/morkit:subagent-driven-development` — parallel agents
- `/morkit:test-driven-development` — TDD discipline
- `/morkit:systematic-debugging` — debug có hệ thống

Plus: using-git-worktrees, finishing-a-development-branch, requesting-code-review, receiving-code-review, dispatching-parallel-agents, verification-before-completion, writing-skills, using-morkit.

### Code review (từ deep-review)
| Command | Việc |
|---|---|
| `/morkit:deep-review [target]` | Code review trên git diff hoặc PR (5 chuyên gia AI song song) |
| `/morkit:deep-review-doctor` | Health-check cài đặt |
| `/morkit:deep-review-post` | Post-review hook |

### Documentation (writing-docs)
| Command | Việc |
|---|---|
| `/morkit:docs [init\|update\|summarize]` | Sinh/cập nhật bộ tài liệu AI-optimized trong `docs/` (taxonomy 00-overview…90-operations + mỏ neo) + con trỏ `CLAUDE.md`/`AGENTS.md` ở root. LLM-driven, không Python |

## Plan review gate

Sau `/morkit:propose`, plugin sinh `morkit/output/spec/<name>/review-checklist.md` từ canonical Google Doc. Auto-detect variant (BE/FE × Feature/BugFix/Refactor).

Override variant: `/morkit:review --variant FE-BugFix`
Force refresh: `/morkit:review --refresh`

Sửa file rồi đặt `Overall Decision: OK` → `/morkit:executing-plans` mở khoá.

Hai lớp gate:
1. **PreToolUse hook** — Claude Code chặn tool call ở harness
2. **Skill content** — pre-flight check trong từng skill

## Schema rules (validate-tasks.sh)

`tasks.md` phải pass R1-R6:
- **R1:** Header `> **For agentic workers:** REQUIRED SUB-SKILL ...`
- **R2:** ≥1 `## Task <N>:`
- **R3:** Mỗi task block có `**Files:**`
- **R4:** Mỗi task block có ≥1 `- [ ]` checkbox
- **R5:** Tổng checkbox ≥ 3
- **R6:** Sibling `.meta.json.schema_version` match validator

Run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate-tasks.sh --explain` để xem chi tiết.

## Tests

```bash
cd plugins/morkit/tests
bash run-all.sh
```

20 test files (incl. Codex fork sync + E2E), cross-platform CI matrix (macOS + Ubuntu).

## License

[MIT](../../LICENSE) © Mor.
