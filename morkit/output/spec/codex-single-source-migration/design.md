# Design — codex-single-source-migration

## Architecture

**Trước:** hai plugin (`morkit` cho Claude marketplace, `morkit-codex` cho Codex marketplace) với `morkit-codex/skills` là bản vocab-swapped sinh từ `morkit/skills` qua `sync-codex-fork.sh`.

**Sau:** một plugin `morkit`, một `skills/` (Claude vocab) phục vụ cả hai nền:
- **Claude Code:** harness auto-load `skills/` (không đổi).
- **Codex:** symlink `~/.agents/skills/morkit` → `plugins/morkit/skills` + agent đọc `using-morkit/references/codex-tools.md` để dịch vocab lúc chạy + dùng native `multi_agent`/skill-discovery.

```
plugins/morkit/
  skills/            ← MỘT nguồn, Claude vocab (Claude auto-load; Codex symlink)
    using-morkit/references/codex-tools.md  ← mapping (Skill→native, Task→spawn_agent, R1 pre-flight)
  commands/          ← một bản; bridge mô tả trong AGENTS.md/CLAUDE.md
  agents/*.md        ← specialist prompts (deep-review, dùng cả 2 nền)
  hooks/hooks.json   ← gate (matcher Skill|apply_patch|Edit|Write) — GIỮ
  AGENTS.md          ← Codex entry/bridge
  CLAUDE.md          ← Claude entry
  .codex/INSTALL.md  ← Codex install
  scripts/install-codex.sh  ← symlink plugins/morkit/skills
```

## Tech Stack

- Bash 4+, `jq`, Python 3 (chỉ cho aggregator nếu giữ), Markdown, symlink/junction.
- Codex CLI native: skill-discovery (`~/.agents/skills/`), `multi_agent` (`spawn_agent`/`wait`/`close_agent`).
- **Không dependency runtime mới.** Không thêm thư viện → không cần tra Context7. Phụ thuộc DUY NHẤT là feature flag native của Codex CLI (`multi_agent`) — cần xác minh version tối thiểu (xem Open Questions).

## Decisions

- **D1 — Single-source + mapping.** Một `skills/` Claude vocab; agent dịch qua `codex-tools.md` lúc chạy. Lý do: skills là tuned-code không nên nhân bản; fork scale `O(harness×skills)`; superpowers chứng minh mô hình này trên 5 harness.
- **D2 — Staged, revert-được.** A additive (không xoá) → B repoint (revert = trỏ lại) → C delete (chỉ sau B xanh). Không big-bang.
- **D3 — Tin native `multi_agent`.** Deep-review trên Codex dùng `spawn_agent(worker, message=<agents/*.md đã fill>)` theo codex-tools.md; retire `codex-deep-review.sh` bash wrapper.
- **D4 — `${CLAUDE_PLUGIN_ROOT}` → env alias.** Export `MORKIT_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT:-<fallback>}` trong install + nêu trong codex-tools.md; KHÔNG rewrite file. Giữ phân biệt với `MORKIT_ROOT` (spec folder — nghĩa cũ).
- **D5 — R1 pre-flight vào codex-tools.md.** Khối export `MORKIT_CURRENT_CHANGE` chuyển từ SKILL.md fork-only sang mục "Codex executing-plans pre-flight" trong mapping reference. Diệt vĩnh viễn R1-wipe vì không còn bản fork để bị ghi đè.
- **D6 — Giữ gate hook + agents + writing-docs.** `hooks.json` matcher đã harness-agnostic (`Skill` cho Claude, `apply_patch|Edit|Write` cho Codex) — một file, không cần fork.
- **D7 — Một marketplace source.** `.agents/plugins/marketplace.json` trỏ `./plugins/morkit` (bỏ entry morkit-codex). Claude marketplace giữ nguyên.
- **D8 — Codex = Advisory (trực giao).** Migration KHÔNG đổi mức enforcement; gate/slash/subagent vẫn advisory trên Codex (thiếu Skill-tool/hook-autoload). Ghi rõ trong AGENTS.md/INSTALL (đã có draft từ phiên trước).

## Stage detail

### Stage A — additive (Claude path zero-impact)
- A1: audit + env-alias `${CLAUDE_PLUGIN_ROOT}` (install-codex.sh export + codex-tools.md note).
- A2: viết mục R1 pre-flight trong codex-tools.md; xoá khối R1 fork-only khỏi `morkit-codex` SKILL.md (sẽ biến mất ở C dù sao).
- A3: cập nhật skill deep-review + codex-tools.md để mô tả native multi_agent; đánh dấu bash wrapper deprecated.
- A4: hợp nhất slash-command bridge instructions vào AGENTS.md/CLAUDE.md.

### Stage B — repoint
- B1: `install-codex.sh` symlink `plugins/morkit/skills`; cập nhật `.codex/INSTALL.md`.
- B2: `.agents/plugins/marketplace.json` source → `./plugins/morkit`.
- B3: copy/di chuyển `AGENTS.md`, `hooks.json` (Codex matcher), `.codex/INSTALL.md` vào `plugins/morkit`.
- B4: verify bằng `doctor` (skill discovery, multi_agent, gate) từ nguồn đơn.

### Stage C — delete (sau B xanh)
- C1: `rm -rf plugins/morkit-codex/`.
- C2: xoá `codex/vocab-map.yaml`, `scripts/sync-codex-fork.sh`, `scripts/check-codex-drift.sh`.
- C3: retire test fork (`test-*codex*`, `test-vocab-map`, `test-drift-detector`, `test-sync*`); retarget test nào kiểm hành vi Codex thật.
- C4: bỏ CI drift-check job trong `ci/github-actions.yml`.
- C5: CHANGELOG entry + bump `plugins/morkit/.claude-plugin/plugin.json` version.

## Open Questions

- **OQ1 — Python aggregator** (`codex-deep-review-aggregate.py`): retire cùng bash wrapper, hay giữ làm CLI tất định? (nghiêng: giữ optional, vì aggregation đa-process vẫn hữu ích.)
- **OQ2 — `docs-hero-orchestrator` mồ côi** (workers `generate-*` đã mất): xoá hẳn source+fork, hay trỏ writing-docs? (ngoài scope nhưng nên giải kèm Stage C.)
- **OQ3 — Codex `multi_agent` min version** + có cần fallback bash cho bản cũ không (dù D3 đã chọn tin bản mới).
- **OQ4 — Thứ tự B2 vs B3**: đổi marketplace source trước hay sau khi file per-platform vào `plugins/morkit`? (đề xuất B3 trước B2 để source mới đã đủ file.)
