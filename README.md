# Mor Claude Plugins

> Marketplace của Mor — một plugin `morkit` consolidates tất cả: spec workflow, brainstorm/execute, code review, doc generation. Một namespace `/morkit:*` cho tất cả.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 1. Cài đặt (1 plugin, 1 lệnh)

Yêu cầu: [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) và Node.js ≥ 18.

```
/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install morkit@mor-duongmh
```

Cài xong là dùng được luôn — không cần setup gì thêm trong từng project.

---

## 2. `morkit` có những gì?

Một plugin chứa 4 nhóm chức năng dưới namespace `/morkit:*`:

| Nhóm | Bao gồm | Để làm gì |
|---|---|---|
| **Spec workflow** | `propose`, `review`, `archive` | Scaffold proposal/design/tasks + review-checklist gate |
| **Plan & build** | `brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `test-driven-development`, `systematic-debugging`, +8 skills khác | Brainstorm, viết plan, thực thi plan, debug, TDD |
| **Code review** | `deep-review`, `deep-review-doctor`, `deep-review-post` | Review code bằng 5 chuyên gia AI song song |
| **Doc generation** | `setup`, `init`, `update`, `sync`, `apply-sync`, `doctor` | Sinh SRS + API + DB doc cho ITO Japan offshore |

Tổng cộng: **22 skills + 9 specialist agents + 15 slash commands** đều có prefix `/morkit:`.

---

## 3. Quy trình điển hình một feature

```
  1. /morkit:brainstorming           → Suy nghĩ, không code
              ↓
  2. /morkit:propose                 → Sinh proposal + design + tasks + checklist
              ↓
  3. 🚦 Mở review-checklist.md, tick từng mục, đặt "Overall Decision: OK"
              ↓
  4. /morkit:executing-plans          → Chạy plan, code TDD
        (hoặc /morkit:subagent-driven-development cho parallel agents)
              ↓
  5. /morkit:deep-review               → Review code (5 chuyên gia AI)
              ↓
  6. /morkit:archive                   → Đóng change sau khi merge
```

Bước 3 là **chốt chặn của con người**. Plugin chặn `/morkit:executing-plans` cho tới khi `Overall Decision: OK`.

---

## 4. Slash command đầy đủ

### Spec workflow
| Command | Việc |
|---|---|
| `/morkit:propose [mô tả]` | Sinh đầy đủ proposal + design + tasks + review-checklist |
| `/morkit:review [tên]` | Tạo lại review-checklist từ Google Doc |
| `/morkit:archive [tên]` | Đóng change sau merge |

### Plan & build (brainstorm, plan, execute, debug, TDD)
14 skills under `/morkit:*` namespace. Most-used:
- `/morkit:brainstorming` — suy nghĩ + investigate codebase, không code
- `/morkit:writing-plans` — viết plan từ ý tưởng
- `/morkit:executing-plans` — thực thi plan từng bước (bị review-gate chặn)
- `/morkit:subagent-driven-development` — parallel agents, fast iteration
- `/morkit:test-driven-development` — TDD discipline
- `/morkit:systematic-debugging` — debug có hệ thống

### Code review
| Command | Việc |
|---|---|
| `/morkit:deep-review [target]` | Review trên git diff hoặc PR (5 specialists song song) |
| `/morkit:deep-review-doctor` | Health-check |
| `/morkit:deep-review-post` | Post-review hook |

### Doc generation
| Command | Việc |
|---|---|
| `/morkit:setup` | Bootstrap Python venv (~30-60s, 1 lần) |
| `/morkit:init` | Sinh fresh SRS + API + DB từ ProjectModel JSON |
| `/morkit:update` | Apply change/plan vào doc |
| `/morkit:sync` | Scan codebase, đề xuất update |
| `/morkit:apply-sync` | Apply đề xuất từ sync |
| `/morkit:doctor` | Health-check docs |

---

## 5. Plan review gate (chốt chặn human-in-the-loop)

Sau `/morkit:propose`, plugin sinh `morkit/output/spec/<tên>/review-checklist.md` từ [Google Doc canonical của Mor](https://docs.google.com/document/d/184wY2N2WOUExmZrClvHCfcRCnSQsJYvav6gc6JwL6xc).

Auto-detect variant (BE/FE × Feature/BugFix/Refactor). Override:

```
/morkit:review --variant FE-BugFix
/morkit:review --refresh
```

Bạn mở file, tick từng mục, sửa dòng cuối:

```diff
- Overall Decision: PENDING
+ Overall Decision: OK
```

→ `/morkit:executing-plans` mở khoá.

**Hai lớp bảo vệ song song** (defense-in-depth):
1. **PreToolUse hook** — Claude Code chặn tool call ngay từ harness
2. **Skill content** — mỗi skill tự kiểm tra ở Step 0 trước khi làm việc

---

## 6. Companion tools (Context7 + RTK)

Hai tool nâng chất lượng research và giảm token. Plugin xử lý lịch sự — không cài silent.

| Tool | Vai trò | Cách cài |
|---|---|---|
| **[Context7](https://github.com/upstash/context7)** | Trả docs/API version-specific cho library, agent không cần đoán | **Lazy** — plugin tự `npx -y ctx7` khi cần. MCP optional. |
| **[RTK](https://github.com/rtk-ai/rtk)** | Nén output bash, giảm 60-90% token | **Hỏi 1 lần** session đầu — bạn chọn `Yes`/`Skip`/`Don't ask again`. |

> 🎯 Context7 đã active trong 6 brainstorm/execute skills + 3 spec-workflow skill — agent sẽ tự gọi Context7 thay vì đoán API.

Cài RTK thủ công:

```bash
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
rtk init -g
```

Cài Context7 dạng MCP (full features):

```bash
npx -y ctx7 setup
```

---

## 7. License

[MIT](LICENSE) © Mor.
