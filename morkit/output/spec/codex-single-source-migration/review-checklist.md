# Plan Review Checklist — `codex-single-source-migration`

> **Human gate.** Tick the items below honestly. Set **Overall Decision: OK** at the
> bottom only when you're satisfied with the plan. Until that happens, the plugin
> blocks `/morkit:executing-plans` and `/morkit:subagent-driven-development` for this change.

## Meta

- **Change:** `codex-single-source-migration`
- **Variant:** BE - Refactor *(auto-detected; override via `--variant` if wrong)*
- **Generated:** 2026-05-25T08:00:00Z
- **Source:** [Mor Developer Review Checklist](https://docs.google.com/document/d/184wY2N2WOUExmZrClvHCfcRCnSQsJYvav6gc6JwL6xc)
- **Files reviewed:**
  - [`proposal.md`](./proposal.md)
  - [`design.md`](./design.md)
  - [`tasks.md`](./tasks.md)

---

## BE - Refactor

### Mục đích & giới hạn

- [x] Có Motivation cụ thể (tech debt nào, pain point nào, metric nào muốn cải thiện)
- [x] Có metric thành công đo được (số file/test/script gỡ được, bảo trì 2x→1x)
- [x] Scope nêu rõ: refactor này KHÔNG đổi behavior Claude path / không đổi mức enforcement (Advisory trực giao)

### Đảm bảo không làm hỏng chức năng đang chạy

- [x] Plan đánh giá test coverage hiện tại (mốc A0 ghi pass count trước khi đổi)
- [x] Coverage thấp → bổ sung/giữ test TRƯỚC khi gỡ fork
- [x] Plan chạy full test suite sau mỗi stage (A-gate / B-gate / C-gate)
- [x] Claude Code path KHÔNG breaking (Stage A additive, smoke-test load skill)

### Security

Mục tiêu: đảm bảo các biện pháp bảo mật hiện có **KHÔNG bị bỏ hoặc yếu đi** sau refactor.

#### Authentication / Authorization

- [x] **Checklist gate hook KHÔNG bị mất khi gỡ fork** — `hooks.json` + `pre-tool-checklist-gate.sh` được giữ; matcher `Skill|apply_patch|Edit|Write` còn nguyên sau migration.
- [x] **R1 pre-flight chuyển đúng chỗ** — logic `MORKIT_CURRENT_CHANGE` vào codex-tools.md không làm fail-open thêm so với hiện tại (vẫn fail-open an toàn, không fail-closed sai).
- [x] **Path traversal guard trong gate KHÔNG bị bỏ** — validation `MORKIT_CURRENT_CHANGE` (chặn `../`, `archive`) còn nguyên.

#### Common Attacks

- [x] **Env-alias `${CLAUDE_PLUGIN_ROOT}` KHÔNG tạo injection** — fallback resolve không cho phép path tùy ý/command substitution ngoài ý muốn.
- [x] **Symlink install KHÔNG ghi ra ngoài vùng cho phép** — `install-codex.sh` chỉ tạo symlink trong `~/.agents/skills` / `~/.codex`, idempotent, uninstall chỉ gỡ symlink trỏ vào checkout.

#### Data Protection

- [x] **Không hardcode secret/token khi dọn config** trong install/scripts sửa đổi.
- [x] **Không leak path nhạy cảm** trong log/echo của script mới.

#### Infrastructure

- [x] **Không dependency runtime mới** — chỉ dựa native Codex feature; nếu cần bật `multi_agent` đã ghi rõ version.
- [x] **CI thay đổi an toàn** — bỏ drift-check job không làm hổng gate test khác; YAML hợp lệ.

### Tác động

- [x] Liệt kê consumer: `morkit-codex` chưa có user thật (xác nhận) → migration không phá install hiện hữu
- [x] Có staged rollout (A→B→C) + mỗi stage revert-được
- [x] Có rollback plan (A additive; B revert=trỏ lại; C chỉ sau B xanh)

### Chi tiết việc plan thực thi

- [x] Mọi task có Steps đánh số rõ ràng
- [x] Mọi Step có code snippet / command cụ thể
- [x] Mọi task có verify step + gate per stage

### Review Summary

- Section có Fail:
- Critical Issues:
- Major Issues:
- Minor Issues: (OQ1 aggregator, OQ2 docs-hero-orchestrator, OQ3 multi_agent min-version, OQ4 thứ tự B2/B3 — accept để resolve trong stage tương ứng?)
- Câu hỏi muốn bàn lại với agent:
- Quyết định:

---

Reviewed by:  Duong

---

## Overall Decision

Overall Decision: OK

### Notes / questions for the agent
