# codex-single-source-migration — Implementation Tasks

> **For agentic workers:** REQUIRED SUB-SKILL: Use morkit:subagent-driven-development (recommended) or morkit:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> ⚠️ **PLAN-REVIEW-GATE REQUIRED:** Before executing this plan, run `/morkit:review` to generate a developer review checklist, tick all applicable items, and set `Overall Decision: OK`. Implementation skills will refuse to proceed until the gate is open.

**Goal:** Chuyển morkit từ fork-based Codex support sang single-source + mapping (kiểu superpowers), gỡ cỗ máy fork, giữ Claude path zero-impact. Staged A→B→C, revert-được.

**Architecture:** Một `plugins/morkit/skills/` (Claude vocab) phục vụ cả Claude (auto-load) và Codex (symlink `~/.agents/skills/morkit` + `using-morkit/references/codex-tools.md` mapping + native `multi_agent`/skill-discovery). Giữ `hooks.json` gate, `agents/*.md`, writing-docs. Xem design.md D1–D8.

**Tech Stack:** Bash 4+, jq, Python 3 (aggregator nếu giữ), Markdown, symlink/junction, Codex CLI native (`multi_agent`, skill-discovery). Không runtime dependency mới.

**Stage gates:** A-gate (sau Task 4), B-gate (sau Task 8), C-gate (sau Task 11). Mỗi gate: full test suite ≥ mốc A0. Task 9–11 (delete) CHỈ chạy sau B-gate xanh.

---

## Task 1: Env-alias cho `${CLAUDE_PLUGIN_ROOT}` (Stage A1)

**Files:**

- Modify: `plugins/morkit/scripts/install-codex.sh`
- Modify: `plugins/morkit/skills/using-morkit/references/codex-tools.md`
- Modify: `plugins/morkit/tests/test-env-cascade.sh`

**TDD steps:**

- [ ] Baseline (A0): chạy `for t in plugins/morkit/tests/*.sh; do bash "$t"; done`, ghi pass count làm mốc
- [ ] Grep hardcode: `grep -rn 'CLAUDE_PLUGIN_ROOT\|MORKIT_PLUGIN_ROOT' plugins/morkit/skills plugins/morkit/commands plugins/morkit/scripts`
- [ ] Write failing test trong `test-env-cascade.sh`: unset `CLAUDE_PLUGIN_ROOT` → script resolve root đúng qua `MORKIT_PLUGIN_ROOT` fallback
- [ ] Thêm export alias `MORKIT_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT:-<fallback>}` (rc-marker block, idempotent) trong `install-codex.sh`
- [ ] Thêm mục "Plugin root resolution" trong `codex-tools.md` giải thích alias cho agent
- [ ] Verify: `test-env-cascade.sh` xanh; không phân biệt nhầm với `MORKIT_ROOT` (spec folder)
- [ ] Commit

## Task 2: Chuyển R1 pre-flight vào codex-tools.md (Stage A2)

**Files:**

- Modify: `plugins/morkit/skills/using-morkit/references/codex-tools.md`
- Modify: `plugins/morkit/tests/test-pre-tool-gate.sh`

**TDD steps:**

- [ ] Write assertion: `codex-tools.md` chứa mục "Codex executing-plans pre-flight" + `MORKIT_CURRENT_CHANGE`
- [ ] Viết mục pre-flight (export var + lệnh detect change) — nội dung từ khối R1 hiện hành
- [ ] Verify: `test-pre-tool-gate.sh` vẫn 29/29 (gate logic không đổi); fail-open vẫn an toàn (không fail-closed sai)
- [ ] Commit (khối R1 fork-only sẽ biến mất ở Task 9 — không xoá tay)

## Task 3: Deep-review → native multi_agent (Stage A3)

**Files:**

- Modify: `plugins/morkit/skills/deep-review/SKILL.md`
- Modify: `plugins/morkit/skills/using-morkit/references/codex-tools.md`
- Read-only: `plugins/morkit/agents/*.md`

**TDD steps:**

- [ ] Verify 7 specialist `agents/*.md` còn đầy đủ
- [ ] Cập nhật `codex-tools.md` + skill deep-review: mô tả `spawn_agent(worker, message=<agents/*.md fill>)` + `wait`/`close_agent`, thay hướng dẫn bash wrapper
- [ ] Đánh dấu `codex-deep-review.sh` + aggregator `deprecated` (chưa xoá — OQ1)
- [ ] Verify: skill deep-review không còn ép bash wrapper; test mới assert mô tả native dispatch
- [ ] Commit

## Task 4: Slash-command bridge + Advisory note (Stage A4)

**Files:**

- Modify: `plugins/morkit/AGENTS.md`
- Modify: `plugins/morkit/CLAUDE.md`
- Modify: `plugins/morkit/.codex/INSTALL.md`

**TDD steps:**

- [ ] Hợp nhất hướng dẫn `/morkit:<name>` → đọc `commands/<name>.md` vào AGENTS.md + CLAUDE.md (một bản)
- [ ] Thêm section "Chế độ Advisory" (draft phiên trước) vào AGENTS.md + `.codex/INSTALL.md`
- [ ] Verify: `test-commands-codex.sh` xanh; grep AGENTS.md có section Advisory
- [ ] **A-gate:** full test ≥ mốc A0; smoke-test Claude load 1 skill (behavior không đổi)
- [ ] Commit

## Task 5: Đưa file per-platform vào plugins/morkit (Stage B3 — trước B2, OQ4)

**Files:**

- Create/Modify: `plugins/morkit/AGENTS.md`, `plugins/morkit/hooks/hooks.json`, `plugins/morkit/.codex/INSTALL.md`

**TDD steps:**

- [ ] Đồng bộ `AGENTS.md`, `hooks/hooks.json` (Codex matcher `apply_patch|Edit|Write|Skill`), `.codex/INSTALL.md` từ morkit-codex vào `plugins/morkit/`
- [ ] Verify: file tồn tại + `hooks.json` hợp lệ JSON (`python3 -c 'import json;...'`)
- [ ] Commit

## Task 6: install-codex.sh trỏ nguồn đơn (Stage B1)

**Files:**

- Modify: `plugins/morkit/scripts/install-codex.sh`
- Modify: `plugins/morkit/tests/test-install-codex.sh`

**TDD steps:**

- [ ] Sửa symlink target → `plugins/morkit/skills` (bỏ morkit-codex); cập nhật uninstall + Windows junction
- [ ] Write/retarget `test-install-codex.sh`: dry-run trong sandbox tạm → symlink trỏ `plugins/morkit/skills`
- [ ] Verify: test xanh; uninstall chỉ gỡ symlink trỏ vào checkout
- [ ] Commit

## Task 7: Marketplace source (Stage B2)

**Files:**

- Modify: `.agents/plugins/marketplace.json`
- Modify: `plugins/morkit/tests/test-codex-marketplace.sh`

**TDD steps:**

- [ ] `.agents/plugins/marketplace.json`: source `./plugins/morkit-codex` → `./plugins/morkit`
- [ ] Verify: `test-codex-marketplace.sh` retarget + xanh; JSON hợp lệ
- [ ] Commit

## Task 8: Verify nguồn đơn end-to-end (Stage B4)

**Files:**

- Modify: `plugins/morkit/.codex/INSTALL.md`
- Read-only: `plugins/morkit/scripts/doctor*.sh`

**TDD steps:**

- [ ] Chạy `doctor` trỏ nguồn mới → skill discovery + gate state OK
- [ ] Xác minh OQ3: Codex CLI version có `multi_agent`; ghi min version vào INSTALL
- [ ] Verify: **B-gate** — Codex path chạy từ `plugins/morkit` (discovery + deep-review native + gate khi --with-hooks)
- [ ] Commit

## Task 9: Xoá fork + machinery (Stage C1+C2 — CHỈ sau B-gate)

**Files:**

- Delete: `plugins/morkit-codex/` (toàn bộ)
- Delete: `plugins/morkit/codex/vocab-map.yaml`, `plugins/morkit/scripts/sync-codex-fork.sh`, `plugins/morkit/scripts/check-codex-drift.sh`

**TDD steps:**

- [ ] `git rm -r plugins/morkit-codex/`
- [ ] `git rm` vocab-map + sync + drift script
- [ ] Verify: `grep -rn morkit-codex plugins .agents .claude-plugin` rỗng; không còn gọi 3 script
- [ ] Commit

## Task 10: Retire / retarget tests (Stage C3)

**Files:**

- Delete: `plugins/morkit/tests/{test-vocab-map,test-drift-detector,test-sync-codex-fork,test-skills-codex-vocab,test-e2e-codex-fork}.sh`
- Modify: `plugins/morkit/tests/{test-install-codex,test-codex-marketplace,test-docs-codex,test-commands-codex}.sh` (retarget nguồn đơn)

**TDD steps:**

- [ ] `git rm` test chỉ kiểm cơ chế fork
- [ ] Retarget test kiểm hành vi Codex thật sang nguồn đơn
- [ ] Verify: `for t in plugins/morkit/tests/*.sh; do bash "$t"; done` toàn xanh, không lỗi missing-file
- [ ] Commit

## Task 11: CI + docs + version (Stage C4+C5)

**Files:**

- Modify: `plugins/morkit/ci/github-actions.yml`
- Modify: `plugins/morkit/.claude-plugin/plugin.json`, `CHANGELOG.md`

**TDD steps:**

- [ ] Bỏ job `drift-check` trong `github-actions.yml`; verify YAML hợp lệ + không còn ref `check-codex-drift`/`sync-codex-fork`
- [ ] (OQ2) Quyết số phận `docs-hero-orchestrator` mồ côi — xoá hoặc trỏ writing-docs
- [ ] CHANGELOG entry `[morkit@X.Y.0]`; bump `plugin.json` version
- [ ] Verify: **C-gate** — toàn bộ test xanh; `grep -rn morkit-codex` rỗng; doctor OK
- [ ] Commit
