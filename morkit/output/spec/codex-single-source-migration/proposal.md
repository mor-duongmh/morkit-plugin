# Proposal — codex-single-source-migration

## Why

morkit hiện hỗ trợ Codex bằng **fork**: `plugins/morkit-codex/` là bản sao vocab-swapped của `plugins/morkit/skills/`, sinh ra qua `sync-codex-fork.sh` + `codex/vocab-map.yaml`, canh bằng `check-codex-drift.sh`, kèm AGENTS.md bridge viết tay và `codex-deep-review.sh` (bash mô phỏng subagent).

Mô hình fork là nguồn của một lớp lỗi lặp lại:
- **Manual-edit wipe** — khối Codex-only (R1 pre-flight `MORKIT_CURRENT_CHANGE`) bị `sync` xoá mỗi lần chạy lại.
- **Bridge stale** — AGENTS.md + `plugin.json` + `commands/` không được sync nên trỏ tới skill đã xoá (vừa xảy ra với `generate-*` / `writing-docs`).
- **Duplication & drift** — 2 bản skill phải đồng bộ tay; fork scale `O(harness × skills)`.
- **Redundant & mâu thuẫn** — morkit **đã thừa hưởng** mapping reference của superpowers (`using-morkit/references/codex-tools.md`, nằm trong `vocab-map` preserve list) mô tả con đường runtime-translate chính xác hơn (native `spawn_agent`/`multi_agent`), nhưng fork lại phủ lên bằng vocab-swap thô hơn và bash wrapper trùng lặp với native feature.

superpowers (5 harness: Claude/Codex/Gemini/Cursor/opencode) chứng minh mô hình **single-source + mapping** scale `O(skills + harness)`, zero-drift, tận dụng native Codex (skill-discovery + `multi_agent`).

`morkit-codex` **chưa có user thật** → tự do migrate không cần deprecation.

## What Changes

Chuyển morkit sang **single-source + mapping** (kiểu superpowers), gỡ toàn bộ cỗ máy fork — staged 3 bước revert-được:

- **Stage A (additive):** đưa logic platform-specific về mô hình mapping *trong khi fork vẫn còn*.
  - Giải `${CLAUDE_PLUGIN_ROOT}` bằng **env alias**, bỏ nhu cầu rewrite file.
  - Chuyển **R1 pre-flight** vào `codex-tools.md` (diệt vĩnh viễn R1-wipe).
  - Thay hướng dẫn deep-review bash bằng **native `multi_agent`/`spawn_agent`**.
  - Gom slash-command bridge vào AGENTS.md/CLAUDE.md (một bản).
- **Stage B (repoint):** trỏ phân phối Codex sang nguồn đơn `plugins/morkit`.
  - `install-codex.sh` symlink `plugins/morkit/skills`.
  - `.agents/plugins/marketplace.json` source → `./plugins/morkit`.
  - Đưa AGENTS.md + hooks.json (Codex matcher) + `.codex/INSTALL.md` vào `plugins/morkit`.
- **Stage C (delete, sau khi B xanh):** xoá `plugins/morkit-codex/`, `vocab-map.yaml`, `sync-codex-fork.sh`, `check-codex-drift.sh`, test fork, CI drift-check job; cập nhật CHANGELOG + bump version.

**Giữ nguyên (giá trị riêng morkit, superpowers không có):** checklist gate hook (`hooks.json` + `pre-tool-checklist-gate.sh`), specialists `agents/*.md`, writing-docs taxonomy.

## Impact

- **Affected:** `plugins/morkit/` (skills/commands/hooks/scripts/AGENTS.md), `plugins/morkit-codex/` (xoá ở Stage C), `.agents/plugins/marketplace.json`, `plugins/morkit/ci/github-actions.yml`, CHANGELOG, `plugin.json` version.
- **Không ảnh hưởng Claude Code path:** Stage A additive, Claude vẫn auto-load `skills/` như cũ; behavior không đổi.
- **Codex path:** sau migration cài qua symlink `plugins/morkit/skills` + mapping; cần Codex CLI bản có `multi_agent` (xác minh ở tasks).
- **Bỏ ~193 file + 2 script + ~10 test + 1 CI job**; bảo trì cross-platform từ 2x về ~1x.
- **Rủi ro chính:** install path Codex đổi (chấp nhận được — chưa có user thật); phụ thuộc native `multi_agent` (mitigation: verify version, cân nhắc fallback ở open question).

## Capabilities

- `codex-single-source` — morkit chạy trên Codex từ **cùng một** `plugins/morkit/skills/` qua mapping reference + native Codex features, không fork/sync/drift.
