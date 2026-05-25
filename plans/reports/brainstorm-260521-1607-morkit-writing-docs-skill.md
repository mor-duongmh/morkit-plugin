# Brainstorm: morkit `writing-docs` skill — bộ tài liệu AI-optimized

**Date:** 2026-05-21 · **Branch:** feature/update-docs-skill · **Type:** brainstorm summary

---

## 1. Problem statement

Cần skill cho **morkit** sinh bộ tài liệu dự án phục vụ AI agent:
- Agent đọc hiểu dễ → tài liệu cấu trúc, nhất quán
- Làm **mỏ neo** (anchor) để agent bám vào
- **Phân rã nhỏ + liên kết qua mỏ neo** → agent nạp đúng context tối thiểu cho từng task

Bối cảnh: bộ `docs-hero` cũ của morkit (8 generate-* skill + orchestrator + agent + 6 command, dùng Python venv + parser + diff engine) **vừa bị xóa** (commit `4cb3d35`) vì quá phức tạp/nặng bảo trì. Làm lại theo hướng KISS.

Khám phá quan trọng: `example/mail-history-admin/` **đã hiện thực** ý tưởng này (34 file, ~1500 LOC) nhưng **chưa codify thành skill**. Đây là reference đã chứng minh.

## 2. Approaches evaluated

| Tiêu chí | Chọn | Loại bỏ |
|---|---|---|
| **Cơ chế gen** | Agent/LLM tự viết (đọc code + template) | Python parser/diff engine (vết xe đổ docs-hero) · Template-only (thiếu nội dung thật) |
| **Phạm vi taxonomy** | Core 6, mở rộng dần | Đủ 10 folder ngay (over-engineering, vi phạm YAGNI) · User pick subset (thêm tương tác thừa) |
| **Đóng gói** | 1 skill + `references/` | Orchestrator + N sub-skill (mô hình docs-hero đã xóa) |
| **Vị trí** | morkit plugin | ck:docs (ck chỉ là kit hỗ trợ phát triển morkit) |
| **Output** | `docs/` root project đích | `morkit/output/` (agent khác khó tìm) |
| **Sync** | Hoãn (front-matter đặt nền) | Auto-sync ngay (phức tạp, chưa cần) |

## 3. Final solution

### 3.1 Vị trí & đóng gói
```
plugins/morkit/
├── skills/writing-docs/
│   ├── SKILL.md                     router: init|update|summarize (frontmatter morkit tối giản)
│   └── references/
│       ├── init-workflow.md         scout → sinh taxonomy → size check
│       ├── update-workflow.md       cập nhật thủ công theo front-matter source_files
│       ├── summarize-workflow.md    tóm tắt nhanh
│       ├── taxonomy.md       [MỚI]  vai trò từng folder + khi nào tạo folder mở rộng
│       ├── anchor-conventions.md [MỚI] 4 cơ chế mỏ neo + quy tắc + ví dụ
│       └── doc-templates/    [MỚI]  skeleton: DOCUMENT-MAP, SOURCE-MAP, *-SYS-SPEC,
│                                    *-MAP, AI-CODING-GUIDE, TEST-RUNBOOK...
└── commands/docs.md                 /morkit:docs → invoke writing-docs skill
```
- LLM-driven, **KHÔNG Python**. 1 skill duy nhất. Theo style morkit (command chỉ "Invoke skill").

### 3.2 Output taxonomy (trong `docs/` của project đích)
```
docs/
├── 00-overview/      DOCUMENT-MAP, SCOPE, SOURCE-MAP, DEPENDENCY-MAP, GLOSSARY
├── 10-requirements/  FEATURE-LIST, USER-FLOWS
├── 20-design/        DESIGN-MAP, 00-core/(ARCHITECTURE,INVARIANTS),
│                     10-features/*-SYS-SPEC, 20-data/DATA-MAP, 30-api/API-MAP, 40-ui/UI-MAP
├── 30-test/          TEST-STRATEGY, TEST-RUNBOOK, TEST-MATRIX
├── 40-ai-coding/     AI-CODING-GUIDE, CODE-SEARCH-GUIDE, COMMON-CHANGE-PLAYBOOKS,
│                     KNOWN-PITFALLS, RISK-REGISTER
└── 90-operations/    LOCAL-RUNBOOK, TROUBLESHOOTING
```
**Folder mở rộng (chỉ tạo khi có tín hiệu/yêu cầu — YAGNI):** `00-review, 50-migration, 60-security, 70-performance, 80-release`. Skill *biết* nhưng không scaffold mặc định.

### 3.3 Mỏ neo (4 cơ chế, right-sized)
| Cơ chế | Vai trò | Mức |
|---|---|---|
| **MAP files** | SOURCE-MAP (concern→file→symbol→keyword) · DOCUMENT-MAP (read paths) · DATA/API/UI/DESIGN-MAP. Agent nạp MAP trước → biết file nào cần đọc | **Chính** |
| **Cross-link** | Read paths + link tương đối giữa doc | **Chính** |
| **Front-matter** | YAML tối thiểu: `source_files`, `updated`, `status` — đặt nền sync sau | **Nhẹ** (mọi file) |
| **ID grep** | `FR-###` (FEATURE-LIST), `INV-###` (INVARIANTS) — chỉ nơi cần cross-ref | **Tùy chọn** |

> Lưu ý: reference `mail-history-admin` dùng **0 front-matter, 0 ID** — chỉ MAP + cross-link + code-search-keywords là đã đủ sạch. Front-matter/ID thêm vào phải giữ tối giản, tránh nhồi sinh độ phức tạp docs-hero.

### 3.4 init workflow (LLM-driven)
1. **Scout** codebase — bỏ qua `.git`, `node_modules`, `__pycache__`, secrets...
2. **Morkit-native dispatch** (Task tool + hướng dẫn inline, hoặc skill `dispatching-parallel-agents` của morkit — KHÔNG phụ thuộc ck:docs-manager) sinh theo thứ tự: **nội dung trước** (10-requirements, 20-design feature specs) → **MAP/anchor files sinh SAU** (MAP là index, phải phản ánh nội dung thật).
3. Mỗi file nhắm **~100 LOC** (như example), trần cứng 800 LOC.
4. **Phát hiện `docs/` phẳng cũ** (project-overview-pdr.md...) → hỏi user: migrate sang taxonomy mới hay giữ song song.

## 4. Implementation considerations & risks

- **MAP files dễ stale** (sinh từ LLM, không auto-sync). Giảm thiểu: front-matter `source_files` + mode `update` thủ công.
- **`docs/` repo này theo convention phẳng** (ghi trong CLAUDE.md documentation-management). Đổi output skill → cân nhắc có migrate docs repo này + cập nhật CLAUDE.md không (xem open question).
- **Rác cần dọn:** `plugins/docs-hero/.pytest_cache/` — untracked leftover sau khi xóa docs-hero, nên xóa.
- **DRY templates:** doc-templates/ tái dùng từ `example/*-template.md` + structure của `example/mail-history-admin/` (không viết lại từ đầu).

## 5. Success metrics

- Chạy `/morkit:docs init` trên 1 codebase thật → sinh đủ core-6 taxonomy, mỗi file <200 LOC, có DOCUMENT-MAP + SOURCE-MAP chính xác.
- Agent dùng DOCUMENT-MAP read path → tìm đúng file cho 1 task mẫu mà không cần đọc toàn bộ docs.
- SOURCE-MAP map đúng concern→file→symbol (spot-check vài entry với codebase thật).
- Không phụ thuộc Python/venv.

## 6. Next steps & dependencies

1. `/ck:plan` chi tiết hóa: viết SKILL.md, 3 workflow references, taxonomy.md, anchor-conventions.md, doc-templates/, command docs.md.
2. Tái dùng: `example/*-template.md` + `example/mail-history-admin/` structure; pattern docs-manager agent từ ck:docs init-workflow.
3. Đăng ký command trong morkit (README + plugin nếu cần).
4. Test init trên 1 codebase mẫu.

## 7. Open questions

1. Có migrate `docs/` của chính repo này sang taxonomy mới + cập nhật `CLAUDE.md documentation-management` không, hay chỉ build skill (skill dùng cho project đích khác)?
2. `*-SYS-SPEC` theo chuẩn cụ thể nào (BrSE/arc42-lite) hay theo structure example là đủ?
3. Mode `update` (sync thủ công) làm ngay trong phase đầu, hay chỉ làm `init` trước rồi bổ sung `update` sau?

## 8. Resolved decisions

- **Agent:** Morkit-native dispatch (Task tool + inline instructions / `dispatching-parallel-agents`). KHÔNG dùng lại ck:docs-manager — giữ morkit self-contained.
- **Next step:** Kết thúc brainstorm tại report. Chưa tạo plan (user tự quyết sau).
