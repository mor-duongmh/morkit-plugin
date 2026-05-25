# Design Log — Codex single-source migration

- date: 2026-05-25
- topic: Gỡ fork-based Codex support của morkit, chuyển sang single-source + mapping (kiểu superpowers)
- mode: explore (morkit:brainstorming)
- inputs:
  - `plugins/morkit-codex/` (fork hiện tại) + `.codex-plugin/plugin.json`, `AGENTS.md`, `.codex/INSTALL.md`, `hooks/hooks.json`
  - `plugins/morkit/codex/vocab-map.yaml`, `plugins/morkit/scripts/sync-codex-fork.sh`, `check-codex-drift.sh`
  - `plugins/morkit/skills/using-morkit/references/codex-tools.md` (mapping — bản gần như copy superpowers)
  - `plugins/morkit/hooks/pre-tool-checklist-gate.sh` (gate)
  - superpowers 5.0.7: `skills/using-superpowers/references/codex-tools.md`, `docs/README.codex.md`, `AGENTS.md`, `.codex/INSTALL.md`, layout đa-harness (.cursor-plugin/.opencode/gemini-extension)
  - `.claude-plugin/marketplace.json` (publish morkit) + `.agents/plugins/marketplace.json` (publish morkit-codex)

## 1. Problem framing

morkit đang gánh **hai chiến lược cross-platform cạnh tranh**:
- **Fork** (vocab-map → `morkit-codex/skills/` qua `sync-codex-fork.sh`, drift detector, AGENTS.md bridge viết tay, `codex-deep-review.sh` bash wrapper).
- **Mapping** (`using-morkit/references/codex-tools.md`, thừa hưởng nguyên từ superpowers, nằm trong `preserve` list).

Hai cái dư thừa và **mâu thuẫn**: vocab-swap (`Agent tool`→"delegate to specialist") thô hơn mapping (`spawn_agent(worker,…)`); bash deep-review trùng với native `multi_agent`. Fork là nguồn của mọi lỗi gặp trong phiên: **R1-wipe, AGENTS.md stale, commands drift**. Fork scale `O(harness × skills)`, không bền khi thêm nền.

## 2. Approaches considered

1. **Hybrid** — giữ fork, tự sinh AGENTS.md + commands trong sync để hết stale. Loại: chỉ vá triệu chứng, vẫn duplication/drift.
2. **Single-source + mapping (superpowers)** — một `skills/` Claude vocab + `codex-tools.md` + symlink `~/.agents/skills/` + native Codex `multi_agent`/skill-discovery. Chọn.
3. **Big-bang vs staged collapse** — chọn staged (revert-được).

Triết lý superpowers xác nhận: skills là *tuned code* không nên nhân bản; phép dịch vocab tầm thường giao cho agent lúc chạy; target 5 harness nên fork bất khả thi.

## 3. Decisions

- **Chốt mô hình single-source + mapping.** (đã confirm)
- **Migration staged 3 bước, revert-được.**
- **Tin native Codex `multi_agent`/`spawn_agent`** (bản mới) → bỏ được bash wrapper `codex-deep-review.sh`.
- **`morkit-codex` chưa có user thật** → tự do làm mạnh tay, không cần deprecation story.
- **Giữ giá trị riêng morkit** (superpowers không có): checklist gate hook, specialists `agents/*.md`, writing-docs taxonomy.
- **R1 pre-flight chuyển vào `codex-tools.md`** → diệt vĩnh viễn lỗi R1-wipe.
- **`${CLAUDE_PLUGIN_ROOT}` giải bằng env alias**, không rewrite file.

### Stage plan
- **A (additive):** A1 env-alias plugin-root · A2 R1→codex-tools.md · A3 deep-review→native multi_agent (retire bash) · A4 slash-bridge gom vào AGENTS/CLAUDE.
- **B (repoint):** B1 install-codex.sh symlink `plugins/morkit/skills` · B2 `.agents/marketplace.json`→`./plugins/morkit` · B3 đưa AGENTS.md+hooks.json+.codex/INSTALL vào `plugins/morkit` · B4 verify doctor.
- **C (delete sau khi B xanh):** C1 xoá `morkit-codex/` · C2 xoá vocab-map+sync+drift · C3 retire test fork · C4 bỏ CI drift-check · C5 CHANGELOG+bump.

## 4. Open questions

- **Python aggregator** (`codex-deep-review-aggregate.py`): retire cùng bash wrapper, hay giữ làm CLI option tất định cho team thích shell?
- **`docs-hero-orchestrator` mồ côi** (workers `generate-*` đã mất ở source): xoá hẳn ở cả source lẫn fork, hay trỏ về writing-docs? (ngoài scope migration nhưng nên giải kèm.)
- **Phạm vi audit `${CLAUDE_PLUGIN_ROOT}`**: bao nhiêu skill/command hardcode thật sự?
- **Codex `multi_agent` minimum version**: native có sẵn từ Codex bản nào? Có cần fallback cho bản cũ không (dù đã chọn tin bản mới)?

## 5. Next step

`/morkit:propose codex-single-source-migration` — biến design log này thành change chính thức (proposal + design + TDD-ready tasks + review-checklist gate).
