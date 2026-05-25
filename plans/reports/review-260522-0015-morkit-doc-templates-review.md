# Review: doc-templates cho morkit writing-docs skill

**Date:** 2026-05-22 · **Branch:** feature/update-docs-skill · **Type:** template review (theo nhóm)
**Mục tiêu:** chốt skeleton cho `doc-templates/`. Output report đánh giá (chưa viết file template thật).
**Reference:** `example/mail-history-admin/` (instance điền sẵn, module-scoped).

---

## Quyết định chung (áp cho mọi template)

- **Scale:** template generic; skill hỗ trợ **cả project-level và per-module**. Project nhỏ → 1 bộ taxonomy; monorepo/app lớn → gợi ý per-module.
- **DRY:** mỗi template mở đầu bằng dòng `> Doc này chứa X. Cho Y xem [doc kia]` + cross-link. Một sự thật ở 1 nơi.
- **Flow format:** `text` + mũi tên `->` (KISS, agent grep được, không cần render). Không Mermaid mặc định.
- **ID policy:** bật `FR-###`/`NFR-###` (FEATURE-LIST) + `INV-###` (INVARIANTS) để TEST-MATRIX cross-ref. Các doc khác ID optional.
- **Front-matter tối thiểu:** `updated`, `status`, `source_files` (nơi có nghĩa). Đặt nền cho mode update sau.
- **README per-folder:** 1 template chung dùng toàn taxonomy (không viết riêng mỗi nhóm).
- **Anchor chính:** MAP files + cross-link. Code Search Keywords (grep-able) trong SOURCE-MAP.

---

## Nhóm 00-overview ✓ CHỐT

### DOCUMENT-MAP (entry point — quan trọng nhất)
`Directory Roles` (table) · `Read Paths` (task→path sequence, ép ≥3) · `Canonical Source Rules` (loại sự thật→path).
→ root README phải link tới file này. Read Paths = cơ chế giúp AI nạp đúng context.

### SCOPE
`In Scope` · `Out Of Scope` · `Boundaries (Must/Must Not own)` · `Legacy/Deprecated Boundary` (opt).

### SOURCE-MAP (mỏ neo mạnh nhất)
front-matter `source_files` · `Concern→Source` (concern|files|responsibility) · `Key Symbols` (symbol|file|purpose) · `Code Search Keywords` (grep block) · `Source Boundaries`.
→ "Source Boundaries" cross-link sang SCOPE thay vì lặp.

### DEPENDENCY-MAP
`Internal` (dep|direction|purpose) · `External` (3rd-party — example THIẾU, thêm) · `Data` (chỉ liệt kê store, schema để DATA-MAP) · `Cross-Module` (+ "khi thêm X, update Y").

### GLOSSARY
`Terms` (term|meaning|source ref) · `Status/Enum Values` (opt).

---

## Nhóm 10-requirements ✓ CHỐT

### FEATURE-LIST (template mới — giàu hơn example)
front-matter · `Legend` (Status enum: Active/Hidden/Planned/Legacy/Deprecated; Priority opt) · `Actors/Roles` (table) · `Functional Features` (ID|Feature|Module/Area|Status|Actor|User Value|Spec-link|Sources) · `Non-Functional Requirements` (NFR-###|Category|Requirement|Verify→TEST-MATRIX) · `Feature Notes` (opt, cho feature nhỏ chưa có SYS-SPEC).
→ Vai trò = **catalog**, không nuốt SYS-SPEC. Thêm Module/Area (scale), Actor, Priority, Spec-link, NFR-bảng.

### USER-FLOWS (tách theo feature)
`USER-FLOWS.md` = index (Feature→link). Mỗi feature 1 file `flows/FR-00X-<feature>.md`.
→ Chỉ chứa **luồng user-facing + touchpoint/endpoint chính**. Sequence kỹ thuật (controller→service→repo→DB) thuộc SYS-SPEC. Tách bạch WHAT vs HOW.

### README (chung)
`# <Folder Title>` · 1 dòng mô tả · `Docs:` list (file — 1 dòng) · `Liên quan:` cross-link.

---

## Nhóm 20-design ✓ CHỐT (deep-review theo sub-folder)

**Sub-taxonomy 20-design** (core/conditional/optional):
- `00-core/` CORE (ARCHITECTURE, INVARIANTS) · `10-features/` CORE (`*-SYS-SPEC`/feature)
- `20-data/` `30-api/` `40-ui/` conditional (chỉ tạo khi có DB/API/UI — tránh folder rỗng)
- `90-reference/` optional (deep-dive)
- Cross-cutting (batch/webhook/integration) → **gộp vào 10-features** (1 SYS-SPEC, dùng status/tag), KHÔNG sub-folder riêng.

**DESIGN-MAP:** Design Layers (Layer|Canonical Doc|Purpose) · System Overview (text) · Key Design Decisions Found In Source.

**`*-SYS-SPEC` (template đinh — CORE + OPTIONAL sections):**
- front-matter: `feature: FR-###`, `status: active|legacy|planned`, `updated`, `source_files`.
- CORE: Purpose · Source Anchors (Layer|Source→file) · Behavior/Flow (text technical seq) · Business Rules (`BR-###` cục bộ) · **Change Impact** (chuẩn hóa tên, bỏ "Change Guidance").
- OPTIONAL: Filters/Inputs · Data Shapes (json) · Response/Output Contract · **Known Issues/Source Mismatch** (cross-link `40-ai-coding/KNOWN-PITFALLS`) · Status+Deprecation (feature legacy).

**INVARIANTS:** nhóm theo concern, `INV-###` + why/source. TEST-MATRIX verify từng INV. Anchor mạnh cho AI-coding.

**ARCHITECTURE (generic-hóa):** Purpose · Runtime Structure (text) · Components/Layers · Patterns&Conventions · Cross-cutting (auth/access/error) · Routing FE/BE (optional web-only).

**DATA-MAP / API-MAP / UI-MAP:** table-anchor concern→file. API-MAP thêm cột Auth. UI-MAP optional (backend-only bỏ). DATA-MAP cross-link DEPENDENCY-MAP (không trùng).

**`*-REFERENCE` (90-reference, pointer pattern — chống stale):** KHÔNG lặp nội dung; chỉ trỏ source path + chuỗi anchor grep. Vd DB-SPEC-REFERENCE trỏ `.sql` + `CREATE TABLE x`. Bản tóm tắt ở MAP.

## Nhóm 30-test ✓ CHỐT

**TEST-STRATEGY:** Existing Coverage (+gaps) · Priority Test Areas (Area|Risk|Coverage — risk-based) · Test Levels · Manual Test Focus.
**TEST-RUNBOOK:** How To Run per-stack (```bash```, skill detect runner) · Manual Verification (URLs/steps) · **Minimal Verification By Change Type** (Change Type|Required Checks) · Current Gaps.
**TEST-MATRIX:** `| Ref (FR/NFR/INV) | Feature | Case | Expected | Status(pass/todo) |`. Khép vòng: NFR/INV → verify ở đây. (Status có thể stale — chấp nhận.)

**Ranh giới overlap "khi đổi X" (3 góc độ + cross-link):**
- SYS-SPEC/Change Impact = **code** nào đổi
- TEST-RUNBOOK/Minimal Verification = **test** nào chạy
- 40-ai-coding/COMMON-CHANGE-PLAYBOOKS = **quy trình e2e**
Mỗi doc 1 góc, link nhau.

## Nhóm 40-ai-coding ✓ CHỐT (nhóm overlap nặng nhất → đã giải quyết DRY)

**AI-CODING-GUIDE = meta-index lai** (KHÔNG lặp): giữ `Safe Change Workflow` (generic) + `Notes For Agents` (đặc thù). Bảng "Common Source Entry Points" → **link** SOURCE-MAP; "Do Not Break" → **link** INVARIANTS; "Before Editing" → link DOCUMENT-MAP read paths.
**CODE-SEARCH-GUIDE = giữ riêng:** `rg` recipes chạy được theo task (bổ sung SOURCE-MAP keywords, không thay thế).
**COMMON-CHANGE-PLAYBOOKS:** quy trình e2e/loại thay đổi; mỗi playbook KẾT bằng "update doc nào". (= góc "quy trình" trong bộ ba overlap.)
**KNOWN-PITFALLS** (`Pitfall|Why|How-avoid` — lỗi CODE hay mắc) vs **RISK-REGISTER** (`Risk|Impact|Mitigation` — rủi ro HỆ THỐNG/nghiệp vụ): giữ cả 2, phân tầng rõ. SYS-SPEC/Known-Issues cross-link KNOWN-PITFALLS.

## Nhóm 90-operations ✓ CHỐT

**LOCAL-RUNBOOK:** Start (backend/frontend/services ```bash```) · Access/URLs · Useful DB/Data Checks (```sql```) · Verify Key Operations. Giữ RIÊNG TEST-RUNBOOK (app vs test), cross-link phần setup chung.
**TROUBLESHOOTING:** `## <Triệu chứng>` → `Check:` list. Khác KNOWN-PITFALLS: chẩn đoán **runtime** vs phòng tránh **code-time**.

## README — 2 loại (phân biệt rõ)
- **README root `docs/`** = landing **mỏng**: intro ngắn + link canonical (DOCUMENT-MAP giữ read paths/source rules). Agent: README → DOCUMENT-MAP.
- **README per-folder** = mini-map mỗi nhóm (đã chốt nhóm 10-req): title · 1 dòng · list file · cross-link.

---

## Bảng index tất cả template (chốt)

| # | Template | Nhóm | Mức | Anchor chính |
|---|---|---|---|---|
| 1 | README (root) | docs/ | core | link DOCUMENT-MAP |
| 2 | README (per-folder) | mọi nhóm | core | mini-map |
| 3 | DOCUMENT-MAP | 00 | core | **read paths + canonical source rules** |
| 4 | SCOPE | 00 | core | boundaries |
| 5 | SOURCE-MAP | 00 | core | **concern→file→symbol→keyword** |
| 6 | DEPENDENCY-MAP | 00 | core | deps (+external) |
| 7 | GLOSSARY | 00 | core | term→source |
| 8 | FEATURE-LIST | 10 | core | FR-### + Main Sources |
| 9 | USER-FLOWS (index) + flows/`FR-*` | 10 | core | user-facing flow |
| 10 | DESIGN-MAP | 20 | core | design layers index |
| 11 | ARCHITECTURE | 20/00-core | core | runtime structure (generic) |
| 12 | INVARIANTS | 20/00-core | core | **INV-### (→TEST-MATRIX)** |
| 13 | `*-SYS-SPEC` | 20/10-features | core | Source Anchors · BR-### · Change Impact · Known-Issues |
| 14 | DATA-MAP | 20/20-data | conditional | schema (cross-link DEPENDENCY) |
| 15 | API-MAP | 20/30-api | conditional | endpoint→handler +Auth |
| 16 | UI-MAP | 20/40-ui | conditional | route→component |
| 17 | `*-REFERENCE` | 20/90-reference | optional | **pointer (trỏ source, không lặp)** |
| 18 | TEST-STRATEGY | 30 | core | risk-based areas |
| 19 | TEST-RUNBOOK | 30 | core | Minimal Verification by change |
| 20 | TEST-MATRIX | 30 | core | **Ref(FR/NFR/INV)+Status** |
| 21 | AI-CODING-GUIDE | 40 | core | **meta-index (link, không lặp)** |
| 22 | CODE-SEARCH-GUIDE | 40 | core | `rg` recipes |
| 23 | COMMON-CHANGE-PLAYBOOKS | 40 | core | quy trình e2e |
| 24 | KNOWN-PITFALLS | 40 | core | lỗi code-time |
| 25 | RISK-REGISTER | 40 | core | rủi ro hệ thống |
| 26 | LOCAL-RUNBOOK | 90 | core | chạy app + DB checks |
| 27 | TROUBLESHOOTING | 90 | core | symptom→checklist runtime |

## Traceability khép vòng (ID + cross-link)
`FR-###` (FEATURE-LIST) → `*-SYS-SPEC` (feature) → `BR-###` (rules per spec)
`NFR-###` (FEATURE-LIST) + `INV-###` (INVARIANTS) → **TEST-MATRIX.Ref** (verify)
`*-SYS-SPEC`/Known-Issues ↔ `KNOWN-PITFALLS` · DATA-MAP ↔ DEPENDENCY-MAP · AI-CODING-GUIDE → SOURCE-MAP/INVARIANTS/DOCUMENT-MAP

## Nguyên tắc template (áp mọi file)
1. Front-matter tối thiểu (`updated`/`status`/`source_files` nơi có nghĩa).
2. Dòng ranh giới đầu file: `> Doc này chứa X. Cho Y xem [doc kia]`.
3. Flow = `text` + mũi tên (không Mermaid mặc định).
4. MAP/REFERENCE = anchor/pointer, không lặp nội dung doc khác.
5. Core/conditional/optional: skill chỉ tạo file khi project có thành phần tương ứng.
6. File nhắm ~100 LOC (như example), trần 800.

## 5 template phẳng cũ (`example/*-template.md`) — mapping & GAP resolution ✓ CHỐT

| Template cũ | LOC | Xử lý |
|---|---|---|
| system-architecture (arc42 8-sec) | 151 | → **ARCHITECTURE nâng lên arc42-lite** (Goals/Constraints/Context/Strategy/BuildingBlock/Runtime/Crosscutting). Deployment View → 90-operations. Tái dùng template này làm base. |
| database-design (ERD/TBL/IDX/REL) | 234 | → **DATA-MAP 2 chế độ**: map-mode (tóm tắt+pointer, mặc định, chống stale) · full-mode (dùng template này khi design-first/không có schema source). |
| codebase-summary (stack/layout/build) | 116 | → **phân rã**: Tech Stack/Packages/Entry/LOC → **00-overview/STACK.md (mới, project-level)**; "What is" → README root; Layout → SOURCE-MAP; Build&Run → LOCAL-RUNBOOK. |
| code-standards (FMT/NAM/LNT/CMT) | 128 | → **40-ai-coding/CODE-STANDARDS.md (mới)**, conditional. Tái dùng template cũ (giữ IDs). |
| design-guidelines (principles/patterns/ADR/anti) | 89 | → principles/patterns → ARCHITECTURE; anti-patterns → KNOWN-PITFALLS; **ADR → 20-design/ADR/NNN-slug.md (mới, MADR-style)**, DESIGN-MAP link tới. |

**3 doc MỚI thêm vào taxonomy (từ GAP):** `00-overview/STACK.md` · `40-ai-coding/CODE-STANDARDS.md` · `20-design/ADR/NNN-slug.md`.
→ Tổng template: **30** (27 + 3 mới). Tất cả conditional/optional theo project.

**Quyết định triết lý quan trọng:** DATA-MAP map-mode (pointer) là mặc định để chống-stale; full-mode chỉ khi không có schema source. Giữ nguyên nguyên tắc "MAP/REFERENCE không lặp".

## Open questions
1. `*-SYS-SPEC` + ADR: theo structure đã review (nghiêng) hay chuẩn ngoài (BrSE)? — chốt khi plan.
2. Skill có cần lệnh "verify docs" (cross-link gãy / ID mồ côi / front-matter thiếu)? — đề xuất để plan cân nhắc (low-priority).
3. Front-matter giữ tối thiểu 3 field (`updated`/`status`/`source_files`) hay thêm `owner`/`related`? — nghiêng tối thiểu.
4. CODE-STANDARDS đặt 40-ai-coding — có cần map ID (NAM/LNT) vào INVARIANTS/test không, hay độc lập?
