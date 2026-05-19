# Design: codex-fork-skills-clone

## Architecture

Sibling-folder fork trong cùng plugin. Folder gốc (`skills/`, `commands/`, `hooks/hooks.json`) phục vụ Claude Code; folder `-codex` song song phục vụ Codex CLI. `install-codex.sh` quyết định trỏ vào nhánh nào tại install time.

```
plugins/morkit/
│
├── skills/                ← Claude Code (zero text change, chỉ rename env var)
├── commands/              ← Claude Code (zero touch)
├── hooks/hooks.json       ← Claude Code (zero touch)
│
├── skills-codex/          ← NEW: vocab trung tính, Codex-native
├── commands-codex/        ← NEW: mirror, bỏ "using the Skill tool"
├── hooks/hooks-codex.json ← NEW: schema Codex, matcher apply_patch|Edit|Write
│
├── codex/
│   └── vocab-map.yaml     ← NEW: swap rules cho sync script
│
├── scripts/
│   ├── sync-codex-fork.sh    ← NEW: apply vocab swap (optional helper)
│   ├── check-codex-drift.sh  ← NEW: CI guard (warn, không fail)
│   ├── install-codex.sh      ← UPDATE: target skills-codex/
│   ├── doctor-codex.sh       ← UPDATE: verify codex fork
│   └── *.sh                  ← UPDATE: env cascade
│
├── hooks/
│   ├── pre-tool-checklist-gate.sh  ← UPDATE: nhận apply_patch|Edit|Write
│   └── *.sh                        ← UPDATE: env cascade
│
├── AGENTS.md              ← UPDATE: bridge trỏ commands-codex/
└── .codex/INSTALL.md      ← UPDATE: new install flow
```

**Flow Claude Code** (unchanged):
```
user gõ /morkit:propose
  → Claude đọc commands/propose.md
  → Invoke skills/propose/SKILL.md qua Skill tool
  → hooks/hooks.json gate via PreToolUse matcher "Skill"
```

**Flow Codex** (new):
```
install-codex.sh symlink:
  ~/.agents/skills/morkit → plugins/morkit/skills-codex/
  ~/.codex/AGENTS.md → plugins/morkit/AGENTS.md
  ~/.codex/hooks.json ← merge từ plugins/morkit/hooks/hooks-codex.json

user gõ /morkit:propose (pattern)
  → Codex agent đọc AGENTS.md bridge
  → Đọc commands-codex/propose.md ("Load the propose skill")
  → Invoke skills-codex/propose/SKILL.md (vocab trung tính)
  → hooks-codex.json gate via PreToolUse matcher apply_patch|Edit|Write
    (chỉ khi đang trong skill executing-plans + checklist not OK)
```

## Tech Stack

- **Bash 4+** (POSIX-compatible khi có thể) — toàn bộ script + hooks
- **Python 3** — `codex-deep-review-aggregate.py` (đã có); không thêm Python dependencies mới
- **jq** — đã required bởi `pre-tool-checklist-gate.sh`; được mở rộng để match thêm tool_name
- **YAML** — vocab-map.yaml; không cần parser bên ngoài (sed-based swap)
- **GitHub Actions** — drift detector trong `ci/github-actions.yml`
- **Codex CLI ≥ 0.120.0** — required, `codex features enable codex_hooks` cho hook gate

Không thêm runtime dependency mới ngoài hệ sinh thái đã có.

## Data model

### `codex/vocab-map.yaml` schema

```yaml
# Vocab swap rules áp dụng skills/ → skills-codex/
# Rule type: literal | regex | block
rules:
  - id: skill-tool-invoke
    type: regex
    pattern: '(Use the )?Skill tool( to invoke)?'
    replacement: 'skill discovery'
    apply_to: ['*.md']

  - id: agent-tool-dispatch
    type: regex
    pattern: '(Use the )?Agent tool with subagent_type=([A-Za-z_-]+)'
    replacement: 'delegate to a $2 specialist'
    apply_to: ['*.md']

  - id: todowrite-task-list
    type: literal
    pattern: 'TodoWrite'
    replacement: 'task list'
    apply_to: ['*.md']

  - id: exit-plan-mode
    type: literal
    pattern: 'ExitPlanMode'
    replacement: 'present plan and pause for confirmation'
    apply_to: ['*.md']

  - id: notebook-edit-removed
    type: literal
    pattern: 'NotebookEdit'
    replacement: '(no equivalent — skip)'
    apply_to: ['*.md']

# Files trong skills/ KHÔNG cần swap (override list, copy nguyên)
preserve:
  - 'using-morkit/references/codex-tools.md'  # đã là Codex docs
  - 'using-morkit/references/copilot-tools.md'
  - 'using-morkit/references/gemini-tools.md'
```

### `hooks/hooks-codex.json` schema

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear",
        "hooks": [{
          "type": "command",
          "command": "bash \"${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/hooks/session-start.sh\"",
          "async": false
        }]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "apply_patch|Edit|Write",
        "hooks": [{
          "type": "command",
          "command": "bash \"${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/hooks/pre-tool-checklist-gate.sh\"",
          "async": false
        }]
      }
    ]
  }
}
```

### `pre-tool-checklist-gate.sh` extended matcher

```bash
# Existing: chỉ chấp nhận tool_name == "Skill"
# New: chấp nhận thêm apply_patch|Edit|Write
case "$tool_name" in
    Skill) ;;                              # Claude Code path
    apply_patch|Edit|Write) ;;             # Codex path
    *) exit 0 ;;
esac

# Existing logic: check executing-plans skill active + change_dir + checklist OK
# New: cần thêm signal "đang trong executing-plans context" cho Codex
#   → fallback: check if MORKIT_CURRENT_CHANGE env exists (set by executing-plans)
#   → hoặc: check git diff có file mới trong morkit/output/spec/<name>/ recent
```

## API contract

Không có API mới. Chỉ thay đổi hành vi 2 entry points:

| Script | Behaviour cũ | Behaviour mới |
|---|---|---|
| `install-codex.sh` | Symlink `skills/` | Symlink `skills-codex/`; write `~/.codex/hooks.json` từ `hooks-codex.json` |
| `doctor-codex.sh` | Verify symlink `skills/` | Verify symlink `skills-codex/`; verify hooks-codex wired |
| `pre-tool-checklist-gate.sh` | Match `tool_name == "Skill"` | Match `Skill` (CC) HOẶC `apply_patch|Edit|Write` (Codex) |

## Resolved during execution

- **R1 (Task 1, 2026-05-18)**: Var name cho plugin install root là `MORKIT_PLUGIN_ROOT`, KHÔNG dùng `MORKIT_ROOT`. Lý do: `MORKIT_ROOT` đã được dùng với nghĩa "spec changes folder" (default `morkit/output/spec`) trong `lib/common.sh::morkit_root()`, `scaffold-change.sh`, `pre-tool-checklist-gate.sh`, `list-changes.sh`, `generate-checklist.sh`, và 4 test files. Cùng env var = 2 nghĩa khác nhau sẽ gây silent breakage. Cascade pattern mới: `${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}`.
- **R2 (Task 1)**: `MORKIT_DATA` cascade cũng đi qua `CLAUDE_PLUGIN_DATA` (đã có trong fetch-checklist.sh): `${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data}}`.
- **R3 (Task 1)**: Python file `dispatch_coordinator.py` cũng áp cascade: `os.environ.get("MORKIT_PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")`.
- **R4 (Task 1)**: `commands/*.md` KHÔNG trong scope Task 1 — CC backward compat không cần (CC export CLAUDE_PLUGIN_ROOT tự động); commands sẽ được clone sang commands-codex/ trong Task 6.

## Open questions

1. **Vocab map có cần rule cho `Bash tool` → `your shell` không?** Codex hiểu "Bash" như command, không phải tool name → có thể giữ nguyên. Đề xuất: không swap để giảm noise; reverify trong Phase 2 nếu Codex agent confused.

2. **`hooks-codex.json` matcher có quá rộng?** `apply_patch|Edit|Write` triggers cho mọi file mutation, không chỉ khi đang chạy executing-plans. Gate logic phải tự detect "đang trong executing-plans context" — đề xuất 2 cách (env var hoặc git heuristic), cần thử trước khi chốt.

3. **Drift detector dùng mtime hay content hash?** mtime đơn giản nhưng dễ false-positive (git checkout reset mtime). Content hash chính xác hơn nhưng cần loại trừ vocab-swap-only diffs. Đề xuất: hash sau khi áp vocab map, so sánh với cached hash trong `.codex/.drift-baseline`.

4. **`commands-codex/` có cần khác hẳn `commands/` không?** Hiện tại swap chỉ 1 câu. Nếu Codex bridge map trong AGENTS.md đủ chi tiết, có thể tối giản `commands-codex/X.md` xuống còn 1-2 dòng "Load the X skill, pass arguments". Trade-off: ngắn hơn nhưng mất parity với Claude side.

5. **CI guard ở repo nào?** GitHub Actions của `mor-duongmh/claude-plugins` đã có `ci/github-actions.yml` — đề xuất thêm job mới `drift-check`, không sửa job hiện tại. Reviewer xem warning trong PR check summary.

---

*Generated: 2026-05-18T07:54:11Z*
