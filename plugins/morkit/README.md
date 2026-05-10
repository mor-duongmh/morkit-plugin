# morkit — Mor's all-in-one Claude Code toolkit

> Một plugin, một namespace `/morkit:*` — từ brainstorm đến code review, từ scaffold đến doc generation.

## Cài đặt

```
/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install morkit@mor-duongmh
```

Cài xong là dùng được — không cần setup gì thêm trong project.

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

### Document generation (từ docs-hero)
| Command | Việc |
|---|---|
| `/morkit:setup` | Bootstrap Python venv (~30-60s, 1 lần) |
| `/morkit:init` | Sinh fresh SRS + API + DB từ ProjectModel JSON |
| `/morkit:update` | Apply change/plan vào doc |
| `/morkit:sync` | Scan codebase, đề xuất update API+DB doc |
| `/morkit:apply-sync` | Apply đề xuất từ sync |
| `/morkit:doctor` | Health-check docs-hero |

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

10 test files, 137 assertions, cross-platform CI matrix (macOS + Ubuntu).

## License

[MIT](../../LICENSE) © Mor.
