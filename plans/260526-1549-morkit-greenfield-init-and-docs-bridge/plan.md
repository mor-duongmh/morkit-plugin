---
title: "morkit greenfield init + change-spec→docs bridge"
status: completed
created: 2026-05-26
source: skill
blockedBy: []
blocks: []
---

# morkit greenfield `/morkit:init` + change-spec → docs bridge

## Context

Hai tính năng đã CHỐT qua brainstorm — phase dưới chỉ thực thi, KHÔNG brainstorm lại.

**Report nguồn (đọc trước khi làm):** `plans/reports/brainstorm-260526-1542-morkit-greenfield-init-docs-bridge.md`

Đây là việc sửa **nội dung instruction của skill** (markdown), KHÔNG phải code ứng dụng, KHÔNG Python. Skill `writing-docs` LLM-driven, morkit-native dispatch — giữ nguyên bản chất.

**Vấn đề:** `/morkit:init` không có nhánh greenfield (Stage 0 chỉ check `docs/`, không check code) → repo trống ra docs rỗng + nguy cơ bịa. `docs update` thuần code-driven → mất WHAT (spec.md scenarios) + WHY (design.md decisions) của mỗi change.

## Quyết định đã khóa

- **Greenfield = Option B (seed).** Detector code-rỗng ở init Stage 0 → seed sub-mode: chỉ tạo spine đúng format, skip file derive-từ-code, không bịa.
- **B+bridge.** `docs update` đọc thêm change-spec **active/chưa archive, tasks tick hết**, **đủ 4 file** (proposal+design+tasks+spec), fold vào docs theo **canonical-source rule**.
- **Thứ tự:** `docs update` (bridge) chạy TRƯỚC `archive` (nguồn bridge = change active).
- 5 câu hỏi mở đã chốt thành quyết định — xem từng phase.

### Canonical-source rule (cơ chế lõi của bridge)

```
CODE canonical        → SYS-SPEC, SOURCE-MAP, DATA/API/UI-MAP           (spec chỉ là hint)
design.md canonical   → 20-design/ADR, 40-ai-coding/RISK-REGISTER+KNOWN-PITFALLS, STACK, SCOPE(non-goals)
spec.md canonical     → 10-requirements/FEATURE-LIST(FR-###), flows/, 30-test/TEST-MATRIX (1 scenario=1 row)
proposal.md           → SCOPE, mô tả FR
tasks.md Files block   → SYS-SPEC Source Anchors + SOURCE-MAP (hint, verify được)
spec ⟂ code           → ghi nhưng đánh dấu status: drift + liệt kê ở report; KHÔNG tin spec mù; code thắng
```

## Phases

| # | Phase | Status | Priority | Phụ thuộc |
|---|-------|--------|----------|-----------|
| 1 | [Greenfield detect + seed sub-mode](phase-01-greenfield-detect-seed.md) | completed | P1 | — |
| 2 | [Docs-update spec bridge](phase-02-docs-update-spec-bridge.md) | completed | P1 | — |
| 3 | [Templates, anchors + versioning](phase-03-templates-anchors-versioning.md) | completed | P2 | 1, 2 |
| 4 | [Verify + consistency](phase-04-verify-consistency.md) | completed | P2 | 1, 2, 3 |

Phase 1 và 2 độc lập (file khác nhau) → có thể song song. Phase 3 hợp nhất + bump version. Phase 4 kiểm tra.

## Files chạm (toàn bộ dưới `plugins/morkit/`)

- `skills/writing-docs/references/init-workflow.md` — Stage 0 detector + seed sub-mode (Phase 1)
- `skills/writing-docs/SKILL.md` — routing/constraints cho greenfield seed (Phase 1)
- `skills/writing-docs/references/update-workflow.md` — bước bridge + canonical rule + drift (Phase 2)
- `skills/writing-docs/references/doc-templates/00-overview/DOCUMENT-MAP.md` — ghi canonical-source rule meta (Phase 3)
- `commands/init.md` — copy "brownfield or greenfield" giờ có thật + flag (Phase 3)
- `skills/using-morkit/` + sequencing note "docs update trước archive" (Phase 3)
- `.claude-plugin/plugin.json` + `.codex-plugin/plugin.json` — bump 1.6.0 → 1.7.0 (Phase 3)

## Quan hệ kế hoạch khác

- `260522-1005-morkit-writing-docs-skill` (completed) — đã build skill này; plan hiện tại mở rộng.
- `260526-0930-docs-versioning-and-resync` (planned) — re-sync site docs. **Soft link:** sau khi plan này merge, lần re-sync site nên phản ánh hành vi init mới. Không hard-block (khác tầng: skill content vs generated site).

## Success Criteria (tổng)

- [x] `/morkit:init` trên repo trống → chỉ seed spine + pointer, ZERO nội dung bịa.
- [x] `docs update` trên 1 change active: decisions→ADR, scenarios→TEST-MATRIX/flows, requirements→FEATURE-LIST(FR-###), Files→Source Anchors. *(+ fallback proposal/tasks khi không có spec.md — fix C1 từ code-review)*
- [x] Xung đột spec⟂code hiện ra dạng drift (`status: drift` đã đăng ký ở anchor-conventions), không ghi ngầm thành sự thật.
- [x] Một format taxonomy nhất quán giữa init + update.
- [x] Cross-link trong các reference workflow giải đúng (template đã verify tồn tại).

## Implementation note (260526)
Triển khai qua `/ck:cook` cùng phiên. 8 file đổi dưới `plugins/morkit/`. Code-review (code-reviewer agent) tìm 1 Critical (C1: bridge phụ thuộc `spec.md` mà native `propose` không sinh) + 3 fix nhất quán → đã xử lý hết: thêm fallback proposal/tasks; đăng ký `planned`/`drift` vào anchor-conventions; STACK seed bỏ `source_files`; note partial-archive; xử lý oldest-first. Test suite: 13/15 file pass; 2 fail (`test-doctor-codex`, `test-install-codex`) do thiếu `codex` CLI trong env — không liên quan thay đổi.
