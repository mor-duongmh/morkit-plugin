# codex-fork-skills-clone — Implementation Tasks

> **For agentic workers:** REQUIRED SUB-SKILL: Use morkit:subagent-driven-development (recommended) or morkit:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> ⚠️ **PLAN-REVIEW-GATE REQUIRED:** Before executing this plan, run `/morkit:review` to generate a developer review checklist, tick all applicable items, and set `Overall Decision: OK`. Implementation skills will refuse to proceed until the gate is open.

**Goal:** Clone morkit skills/commands/hooks cần diverge sang folder song song `-codex` để Codex CLI dùng được vocab tự nhiên, giữ Claude Code path zero-impact.

**Architecture:** Sibling-folder fork trong cùng plugin. `install-codex.sh` quyết định symlink target tại install time. Env vars cascade (`MORKIT_PLUGIN_ROOT` → `CLAUDE_PLUGIN_ROOT` → fallback) cho phép scripts share giữa 2 paths. **Lưu ý**: dùng `MORKIT_PLUGIN_ROOT`, KHÔNG `MORKIT_ROOT` (đã có nghĩa cũ là spec folder — xem design.md Resolved R1).

**Tech Stack:** Bash 4+, Python 3, jq, YAML (sed-based parsing), GitHub Actions, Codex CLI ≥ 0.120.0. Không runtime dependency mới.

---

## File Structure

### New files

- `plugins/morkit/skills-codex/` — 26 SKILL.md clone với vocab trung tính (sinh ra từ sync-codex-fork.sh)
- `plugins/morkit/commands-codex/` — 15 command .md mirror
- `plugins/morkit/hooks/hooks-codex.json` — Codex schema
- `plugins/morkit/codex/vocab-map.yaml` — vocab swap rules
- `plugins/morkit/scripts/sync-codex-fork.sh` — helper apply vocab swap
- `plugins/morkit/scripts/check-codex-drift.sh` — CI guard
- `plugins/morkit/.codex/.drift-baseline` — hash cache cho drift detector

### Modified files

- `plugins/morkit/scripts/doctor.sh` — env cascade
- `plugins/morkit/scripts/scaffold-change.sh` — env cascade
- `plugins/morkit/scripts/setup-venv.sh` — env cascade + `MORKIT_DATA` fallback
- `plugins/morkit/scripts/migrate-from-openspec.sh` — env cascade
- `plugins/morkit/scripts/install-codex.sh` — target `skills-codex/`, write `hooks-codex.json`
- `plugins/morkit/scripts/doctor-codex.sh` — verify codex fork
- `plugins/morkit/scripts/lib/common.sh` — env cascade
- `plugins/morkit/hooks/hooks.json` — env var rename (CLAUDE_PLUGIN_ROOT fallback giữ)
- `plugins/morkit/hooks/pre-tool-checklist-gate.sh` — multi-tool matcher + Codex context detect
- `plugins/morkit/hooks/dh-session-start.sh` — env cascade + `MORKIT_DATA` fallback
- `plugins/morkit/hooks/first-run-tools.sh` — env cascade + `MORKIT_DATA` fallback
- `plugins/morkit/hooks/session-start.sh` — env cascade
- `plugins/morkit/skills/**/*.md` — ~13 file đổi `${CLAUDE_PLUGIN_ROOT}` → `${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` (chỉ env var, text khác giữ nguyên)
- `plugins/morkit/skills/docs-hero-orchestrator/scripts/dispatch_coordinator.py` — Python cascade: `os.environ.get("MORKIT_PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")`
- `plugins/morkit/AGENTS.md` — bridge map trỏ `commands-codex/`
- `plugins/morkit/.codex/INSTALL.md` — new install flow
- `plugins/morkit/ci/github-actions.yml` — drift-check job mới

### Deleted files

- (none)

---

## Task 1: Env var cascade refactor (Phase 1 foundation)

**Files:**

- Modify: `plugins/morkit/scripts/doctor.sh`
- Modify: `plugins/morkit/scripts/scaffold-change.sh`
- Modify: `plugins/morkit/scripts/setup-venv.sh`
- Modify: `plugins/morkit/scripts/migrate-from-openspec.sh`
- Modify: `plugins/morkit/scripts/install-codex.sh`
- Modify: `plugins/morkit/scripts/doctor-codex.sh`
- Modify: `plugins/morkit/scripts/lib/common.sh`
- Modify: `plugins/morkit/hooks/hooks.json`
- Modify: `plugins/morkit/hooks/pre-tool-checklist-gate.sh`
- Modify: `plugins/morkit/hooks/dh-session-start.sh`
- Modify: `plugins/morkit/hooks/first-run-tools.sh`
- Modify: `plugins/morkit/hooks/session-start.sh`
- Modify: `plugins/morkit/skills/**/*.md` (14 file)

**TDD steps:**

- [ ] Write failing test: `tests/test-env-cascade.sh` — assert scripts dùng `${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-...}}` pattern
- [ ] Refactor scripts/hooks/skills sed-based: `${CLAUDE_PLUGIN_ROOT}` → `${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}`
- [ ] Refactor hardcode `~/.claude/plugins/data` → `${MORKIT_DATA:-$HOME/.claude/plugins/data}`
- [ ] Test cross-shell: bash 3.x (macOS default) + bash 5.x + zsh
- [ ] CC regression test: chạy `/morkit:propose test-env-1` dưới Claude Code → vẫn hoạt động
- [ ] Codex test: chạy `/morkit:propose test-env-1` dưới Codex → vẫn hoạt động
- [ ] Commit

---

## Task 2: Drift detector + CI guard (Phase 1)

**Files:**

- Create: `plugins/morkit/scripts/check-codex-drift.sh`
- Create: `plugins/morkit/.codex/.drift-baseline` (initially empty, populated by sync)
- Modify: `plugins/morkit/ci/github-actions.yml`

**TDD steps:**

- [ ] Write failing test: `tests/test-drift-detector.sh` — assert script exit 0 với warn message khi skills/X.md mtime > skills-codex/X.md mtime
- [ ] Implement `check-codex-drift.sh`:
  - Iterate skills/**/*.md
  - For each file: compute hash of post-swap content (apply vocab-map.yaml), compare với `.drift-baseline`
  - Warn (echo to stderr) nếu khác, exit 0 không fail
- [ ] Add GitHub Action job `drift-check`: trigger on PR sửa `plugins/morkit/skills/**`, gọi `check-codex-drift.sh`, post warning vào PR check summary
- [ ] Test: tạo PR giả lập sửa 1 skill → CI fires warning
- [ ] Commit

---

## Task 3: Vocab map YAML (Phase 2 prep)

**Files:**

- Create: `plugins/morkit/codex/vocab-map.yaml`

**TDD steps:**

- [ ] Write failing test: `tests/test-vocab-map.sh` — apply map vào fixture text, assert output match expected
- [ ] Define minimum 5 rules: skill-tool, agent-tool, todowrite, exit-plan-mode, notebook-edit
- [ ] Define `preserve:` list cho files đã là Codex docs (references/codex-tools.md, copilot-tools.md, gemini-tools.md)
- [ ] Edge cases: rule trong code block (preserve as-is), rule trong frontmatter (apply)
- [ ] Commit

---

## Task 4: Sync helper script (Phase 2 enabler)

**Files:**

- Create: `plugins/morkit/scripts/sync-codex-fork.sh`

**TDD steps:**

- [ ] Write failing test: `tests/test-sync-codex-fork.sh` — chạy script trên fixture skills/, assert skills-codex/ chứa swapped content
- [ ] Implement sync script:
  - Parse vocab-map.yaml (sed-based extract rules block)
  - Mirror skills/ → skills-codex/ (rsync or cp -r)
  - Apply each rule với sed -i (BSD vs GNU sed compat)
  - Skip files in preserve list (copy as-is)
  - Update .drift-baseline hashes
- [ ] Idempotent test: chạy 2 lần liên tiếp → output giống nhau
- [ ] Commit

---

## Task 5: Generate skills-codex/ (Phase 2)

**Files:**

- Create: `plugins/morkit/skills-codex/` (26 SKILL.md + assets, generated)

**TDD steps:**

- [ ] Write failing test: `tests/test-skills-codex-vocab.sh` — assert skills-codex/**/*.md không chứa "Skill tool", "Agent tool", "TodoWrite" (trừ preserve list)
- [ ] Chạy `bash scripts/sync-codex-fork.sh` để generate
- [ ] Spot-check 5 file điển hình (brainstorming, writing-plans, executing-plans, deep-review, subagent-driven-development): đọc tự nhiên không?
- [ ] Codex E2E test: chạy 1 spec change qua Codex dùng `skills-codex/` symlink
- [ ] Commit skills-codex/ (yes — commit generated artifact để Codex user clone về dùng ngay)

---

## Task 6: Commands clone (Phase 3)

**Files:**

- Create: `plugins/morkit/commands-codex/` (15 .md)

**TDD steps:**

- [ ] Write failing test: assert commands-codex/X.md tồn tại tương ứng commands/X.md
- [ ] Mirror commands/ → commands-codex/ qua sync-codex-fork.sh (extend rule cho commands)
- [ ] Apply rule "using the Skill tool" → "" (strip)
- [ ] Spot-check propose.md, executing-plans.md
- [ ] Commit

---

## Task 7: Codex hooks variant (Phase 4)

**Files:**

- Create: `plugins/morkit/hooks/hooks-codex.json`
- Modify: `plugins/morkit/hooks/pre-tool-checklist-gate.sh`

**TDD steps:**

- [ ] Write failing test: `tests/test-pre-tool-gate-codex.sh` — pipe JSON `{"tool_name":"apply_patch",...}` + context "đang trong executing-plans" + checklist not OK → assert exit non-zero + stderr error message
- [ ] Refactor gate script:
  - Accept tool_name in {Skill, apply_patch, Edit, Write}
  - Codex context detect: env `MORKIT_CURRENT_CHANGE` set hoặc git diff có file mới trong morkit/output/spec recent (< 30 phút)
  - Logic chính (CHANGE_DIR, CHECKLIST, Overall Decision OK) giữ nguyên
- [ ] Write hooks-codex.json với matcher `apply_patch|Edit|Write`
- [ ] CC regression test: gate vẫn block Skill tool như cũ
- [ ] Codex test: gate block apply_patch khi trong executing-plans + checklist PENDING
- [ ] Codex test: gate cho phép apply_patch ngoài executing-plans context
- [ ] Commit

---

## Task 8: Install-codex + doctor-codex update (Phase 4)

**Files:**

- Modify: `plugins/morkit/scripts/install-codex.sh`
- Modify: `plugins/morkit/scripts/doctor-codex.sh`

**TDD steps:**

- [ ] Write failing test: `tests/test-install-codex.sh` — assume `~/.agents/skills/morkit` symlink trỏ `skills-codex/` (không phải `skills/`); assert `~/.codex/hooks.json` chứa reference đến `hooks-codex.json`
- [ ] Update install-codex.sh:
  - Step 1 symlink target: `skills/` → `skills-codex/`
  - Step 4 hooks: write từ `hooks-codex.json` (đọc, không hardcode JSON in-line)
- [ ] Update doctor-codex.sh:
  - Verify symlink trỏ `skills-codex/`
  - Verify hooks.json reference `hooks-codex.json`
  - Skill count check vẫn ≥ 20
- [ ] Test idempotency: chạy 2 lần → no error
- [ ] Uninstall test: `--uninstall` xóa symlink + cleanup
- [ ] Commit

---

## Task 9: AGENTS.md + INSTALL.md update (Phase 5)

**Files:**

- Modify: `plugins/morkit/AGENTS.md`
- Modify: `plugins/morkit/.codex/INSTALL.md`

**TDD steps:**

- [ ] Write failing test: grep AGENTS.md cho "commands-codex/" reference; grep INSTALL.md cho "skills-codex/"
- [ ] Update AGENTS.md bridge: "khi user gõ `/morkit:<name>` → đọc `<MORKIT_PLUGIN_ROOT>/commands-codex/<name>.md`"
- [ ] Update Tool mapping section: thêm note "skills/ vs skills-codex/"
- [ ] Update INSTALL.md: clone repo + chạy install-codex.sh → symlink skills-codex/ (mention rõ folder mới)
- [ ] Commit

---

## Task 10: README + E2E verification (Phase 5)

**Files:**

- Modify: `plugins/morkit/README.md`

**TDD steps:**

- [ ] Write failing test: README có section "Claude Code vs Codex paths" với 2 install commands
- [ ] Update README tóm tắt 2 paths
- [ ] Manual E2E test scenarios:
  - [ ] CC: `/morkit:propose e2e-cc-test` → tasks fill → `/morkit:review` → tick OK → `/morkit:executing-plans` → 1 task complete
  - [ ] Codex: same flow nhưng qua Codex CLI với install-codex.sh đã run
  - [ ] Drift detector: sửa skills/brainstorming/SKILL.md, PR → CI warn (không fail)
- [ ] Commit + tag release candidate

---

*Generated: 2026-05-18T07:54:11Z*
