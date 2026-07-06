# morkit — Mor's all-in-one toolkit (Claude Code + Codex)

> Một plugin, một namespace `/morkit:*` — từ spec & brainstorm đến execute và code review.

## Cài đặt

### Claude Code

```
/plugin add marketplace github:mor-duongmh/morkit-plugin
/plugin install morkit@mor-duongmh
```

Cài xong là dùng được — không cần setup gì thêm trong project.

### Codex CLI

**Native plugin marketplace** (Codex CLI ≥ 0.131):

```bash
codex plugin marketplace add mor-duongmh/morkit-plugin
```

Codex sẽ list plugin `morkit`. **Codex users install `morkit`** — cùng một nguồn với Claude Code; skills giữ Claude vocab và được dịch lúc chạy qua `using-morkit/references/codex-tools.md`.

**Script install** (Codex < 0.131 hoặc fallback):

```bash
git clone https://github.com/mor-duongmh/morkit-plugin.git ~/.codex/morkit-source
bash ~/.codex/morkit-source/plugins/morkit/scripts/install-codex.sh
```

Verify: `bash ~/.codex/morkit-source/plugins/morkit/scripts/doctor-codex.sh`. Chi tiết: [plugins/morkit/.codex/INSTALL.md](.codex/INSTALL.md).

## Claude Code vs Codex CLI

| Aspect | Claude Code | Codex CLI |
|---|---|---|
| Install | `/plugin install morkit@mor-duongmh` | `codex plugin marketplace add mor-duongmh/morkit-plugin` → install **`morkit`** |
| Plugin folder | `plugins/morkit/` | `plugins/morkit/` (**cùng nguồn**) |
| Skills | `plugins/morkit/skills/` (Claude vocab) | `plugins/morkit/skills/` (symlink `~/.agents/skills/morkit`; dịch qua `codex-tools.md`) |
| Commands | `plugins/morkit/commands/` | `plugins/morkit/commands/` (bridge qua AGENTS.md) |
| Hooks | `plugins/morkit/hooks/hooks.json` (matcher `Skill\|apply_patch\|Edit\|Write`) | cùng file, wire qua `--with-hooks` |
| Slash | Native `/morkit:X` | AGENTS.md bridge cho `/morkit:X` (đọc `commands/X.md`) |
| Subagent | Native `Agent` tool | Native `multi_agent` (`spawn_agent`) |
| Doctor | `/plugin doctor` | `bash plugins/morkit/scripts/doctor-codex.sh` |
| Review gate | Cưỡng chế | Advisory (mặc định OFF; `--with-hooks` để bật) |

### Single-source approach (vì sao KHÔNG fork)

Trước đây morkit fork sang `plugins/morkit-codex/` (vocab-swap qua `sync-codex-fork.sh`). Cách đó gây duplication + drift (2 bản skill phải đồng bộ tay) và scale `O(harness × skills)`. Theo mô hình của superpowers, morkit nay dùng **một nguồn** `plugins/morkit/skills/` cho cả hai harness:

- **Claude Code**: harness auto-load `skills/`.
- **Codex**: symlink `~/.agents/skills/morkit` → `plugins/morkit/skills/`; agent đọc `using-morkit/references/codex-tools.md` để dịch vocab (`Skill tool`→skill discovery, `Agent tool`→`spawn_agent`, `TodoWrite`→`update_plan`) và dùng native Codex features.

Không còn `vocab-map.yaml`, `sync-codex-fork.sh`, hay drift detector — không có bản fork để lệch. Lưu ý: trên Codex, review gate/slash/subagent là **advisory** (xem [.codex/INSTALL.md](.codex/INSTALL.md) — "Chế độ Advisory").

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
- Override path: `MORKIT_ROOT=path/to/changes` env var (chỉ thư mục changes; design log của brainstorming nằm ở `design-logs/` cạnh thư mục đó, không nằm trong)

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

### Documentation (docs-hero)
| Command | Việc |
|---|---|
| `/morkit:setup` | Bootstrap Python venv (~30-60s, 1 lần) |
| `/morkit:init` | **Cửa chính tạo docs** — hỏi loại dự án rồi route: *greenfield* (pipeline BA từ tài liệu yêu cầu) hoặc *brownfield* (render từ ProjectModel + quét code). Chọn 1+ trong 7 outputs (SRS / API / DB / system-architecture / code-standards / codebase-summary / design-guidelines) |
| `/morkit:greenfield` | Shortcut thẳng vào nhánh greenfield của init — pipeline BA G0→G7 (brainstorm → user stories → gap/risk → clarify → ProjectModel → docs), 3 human gate, resume-able |
| `/morkit:docs-update` | Apply change/plan vào doc |
| `/morkit:sync` | Quét codebase, đề xuất update (API / DB / arch / standards / summary) |
| `/morkit:apply-sync` | Apply đề xuất từ sync |
| `/morkit:kb-sync` | Sync số liệu/cấu trúc (RPC/route/table/commands) của task vào knowledge pack convention-driven (`knowledge/.kb-sync.json`) + sổ cái tuần. Batch, do PM/lead chạy; propose→tick→apply |
| `/morkit:doctor` | Health-check docs-hero |

### Test cases (standalone)
| Command | Việc |
|---|---|
| `/morkit:generate-test-cases [feature]` | Viết test-case spec vào Excel template cho tester — bao gồm hiểu feature, brainstorm, duyệt scope, tạo file test case. Chạy độc lập, KHÔNG thuộc `morkit` workflow, KHÔNG thuộc docs-hero; chỉ viết spec (không chạy test). |

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

15 test files (single-source Codex install/marketplace/docs/doctor + spec workflow), cross-platform CI matrix (macOS + Ubuntu).

## License

[MIT](../../LICENSE) © Mor.
