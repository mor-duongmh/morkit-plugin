---
phase: 1
title: "Greenfield detect + seed sub-mode"
status: completed
priority: P1
effort: "3-4h"
dependencies: []
---

# Phase 1: Greenfield detect + seed sub-mode

## Overview
Thêm nhánh greenfield vào `/morkit:init`: phát hiện repo code-rỗng ở Stage 0, rồi seed CHỈ spine đúng format (không scout-content, không bịa). Biến copy "brownfield or greenfield" thành sự thật.

## Requirements
- Functional:
  - Init Stage 0 phát hiện greenfield và rẽ sang seed sub-mode thay vì chạy scout pipeline.
  - Seed tạo đúng 4 file core; tuỳ chọn thêm STACK/ARCHITECTURE (intended) qua 1 gate.
  - Không sinh bất kỳ file derive-từ-code nào (SOURCE-MAP, SYS-SPEC, TEST-*, CODE-STANDARDS, INVARIANTS…).
- Non-functional: LLM-driven, no Python. Giữ giọng + cấu trúc các reference hiện có. Mỗi file vẫn ~100 LOC.

## Architecture

**Detector (quyết định đã chốt):** greenfield khi — KHÔNG có manifest nhận dạng (`package.json`, `pyproject.toml`/`setup.py`, `go.mod`, `Cargo.toml`, `pom.xml`/`build.gradle`, `composer.json`, `Gemfile`, `*.csproj`…) **VÀ** số source-file LOC ≈ 0 (bỏ qua `.git`, `README*`, `LICENSE*`, dotfiles/config, `docs/`).
- Manifest có nhưng không có src (scaffold) → **brownfield** (STACK derive được).
- Mơ hồ (vài file lẻ) → **AskUserQuestion**: "Brownfield (scout & document) hay Greenfield (seed spine)?".
- Per-module scope: chạy detector cho TỪNG module root; chỉ module rỗng mới seed.

**Seed sub-mode — file tạo (quyết định đã chốt):**
```
docs/00-overview/SCOPE.md          ← từ template; điền mục tiêu dự án (hỏi user 1-2 câu hoặc để placeholder rõ ràng)
docs/00-overview/DOCUMENT-MAP.md   ← từ template; note "populated as code grows"; chỉ list folder đang có
docs/10-requirements/FEATURE-LIST.md ← từ template; RỖNG, sẵn cột FR-###/NFR-###
CLAUDE.md (root)                    ← pointer marker-block + approve gate (agent-instructions.md)
```
- **Opt-in (1 gate):** hỏi "Seed thêm STACK + ARCHITECTURE dự định?" — default KHÔNG; `--yes` → KHÔNG (vì là intent forward, dễ stale). Nếu chọn có: thêm `00-overview/STACK.md` (stack dự định) + `20-design/00-core/ARCHITECTURE.md` (kiến trúc dự định, đánh dấu `status: planned`).
- `00-overview/` tồn tại ⇒ thoả precondition của `docs update` (update-workflow.md dòng 26).

**Luồng greenfield trong Stage 0/Stage seed:**
```
Stage 0: docs/ trống? → CÓ → chạy detector code
   greenfield → SEED sub-mode:  hỏi scale (project/module) → [gate STACK/ARCH?] →
                ghi 4 file core (+opt) → CLAUDE.md pointer (approve gate) → report "seeded, 0 fiction"
   brownfield → pipeline cũ (Stage 1 Scout → … không đổi)
```

## Related Code Files
- Modify: `plugins/morkit/skills/writing-docs/references/init-workflow.md`
  - Stage 0: thêm bước "kiểm tra code → greenfield?" (sau bước check `docs/`, trước Scale).
  - Thêm mục **"Greenfield Seed Sub-Mode"** (đặt giữa Stage 0 và Stage 1, hoặc nhánh rẽ rõ ràng): liệt kê file seed, gate STACK/ARCH, KHÔNG chạy Stage 1-4 scout-content; vẫn chạy Stage 4b (agent-instructions/CLAUDE.md) + Stage 5 (validate, rút gọn).
- Modify: `plugins/morkit/skills/writing-docs/SKILL.md`
  - Mục Routing/Constraints: ghi rõ init có 2 nhánh (brownfield scout / greenfield seed); nhắc "no fiction — chỉ seed khi code rỗng".
  - Cập nhật dòng generation order note nếu cần (seed: Content(seed) → MAP(seed) → agent-instructions, vẫn đúng thứ tự).

## Implementation Steps
1. Đọc `init-workflow.md` + `SKILL.md` + template `SCOPE.md`/`DOCUMENT-MAP.md`/`FEATURE-LIST.md` + `references/agent-instructions.md` để khớp giọng & marker-block.
2. Soạn đoạn **detector** cho Stage 0 (heuristic manifest + LOC; rule scaffold; rule mơ hồ→Ask; rule per-module).
3. Soạn mục **Greenfield Seed Sub-Mode**: danh sách 4 file core + gate opt-in STACK/ARCH + "skip mọi file code-derived" + chạy agent-instructions + validate rút gọn. Nêu rõ với mỗi seed file dùng template nào và để placeholder/hỏi gì.
4. Cập nhật `SKILL.md` (routing 2 nhánh + constraint no-fiction).
5. Đảm bảo `--scope`, `--yes`, `--agents` vẫn hợp lệ ở nhánh seed (–-yes bỏ gate STACK/ARCH = off; bỏ post-scout gate vốn không có ở seed).
6. Kiểm tra cross-link trong đoạn mới trỏ tới template/`agent-instructions.md` có thật.

## Success Criteria
- [ ] `init-workflow.md` mô tả rõ detector + seed sub-mode; brownfield path không đổi hành vi.
- [ ] Seed tạo đúng 4 file core (+ STACK/ARCH chỉ khi opt-in); liệt kê tên file + template nguồn.
- [ ] Ghi rõ: KHÔNG sinh SOURCE-MAP/SYS-SPEC/TEST-*/CODE-STANDARDS/INVARIANTS khi greenfield.
- [ ] `--yes`/`--scope`/`--agents` xử lý nhất quán ở nhánh seed.
- [ ] `SKILL.md` phản ánh 2 nhánh + constraint no-fiction.
- [ ] Mọi cross-link mới giải đúng file tồn tại.

## Risk Assessment
- **LLM vẫn bịa dù có chỉ thị seed** → mitigation: câu lệnh tuyệt đối "KHÔNG suy diễn nội dung; chỉ ghi placeholder/điều user nhập"; validate liệt kê file tạo để người soi.
- **Detector nhầm scaffold thành greenfield** → mitigation: tách rõ "manifest có = brownfield"; mơ hồ → Ask.
- **Seed quá mỏng vô dụng (YAGNI)** → mitigation: giữ 4 file + opt-in; `DOCUMENT-MAP` + `CLAUDE.md` pointer đủ để agent định hướng ngày 1.
