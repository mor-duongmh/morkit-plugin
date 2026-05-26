---
title: "Docs versioning (model A) + re-sync site về main"
status: planned
created: 2026-05-26
source: change
blockedBy: []
blocks: []
---

# Docs versioning + re-sync — version selector ở góc trên (model A)

## Context

Site docs (`docs/`) sinh bởi `docs/_scaffolder/` đã **lệch pha với main**: vẫn mô tả bộ
`docs-hero` (8 skill `generate-*` + `docs-hero-orchestrator`, 6 command `setup/init/update-doc/
sync/apply-sync/doctor`) đã bị khai tử, trong khi skill mới `writing-docs` + command `docs`
chưa có trang. Đồng thời chưa có cơ chế version nào cho docs.

Mục tiêu: (1) **re-sync** site về đúng trạng thái main, (2) thêm **version selector ở `.topnav`**
theo **model A** (root = bản mới nhất, bản cũ đóng băng trong `docs/vX/`).

**Quyết định người dùng đã chốt:**
- Model A (root = latest + freeze bản cũ).
- Docs có **track version riêng**, tách khỏi plugin version (`plugin.json` đang 1.5.0).
- Bản hiện tại (stale, mô tả docs-hero) = **1.0.0** (đóng băng làm history).
- Bản re-sync về main = **1.1.0** (root, "mới nhất").

## Quyết định đã khóa

- **Mô hình lưu trữ (A):** `docs/` root LUÔN là bản mới nhất. Bản cũ là cây HTML đóng băng
  trong `docs/v<version>/`. URL "mới nhất" ổn định (`…/docs/`), link chia sẻ không gãy.
- **Nguồn version (single source):** `docs/versions.json`. Selector đọc file này, không hardcode.
- **Selector:** vanilla JS (`docs/version-selector.js`), KHÔNG thêm dependency (đúng tinh thần
  scaffolder stdlib-only). Đổi version → điều hướng sang trang chủ của version đó.
- **`DOCS_ROOT` theo độ sâu trang:** script nhận `data-docs-root` (đường relative tới `docs/`
  thật). templates.py biết độ sâu khi sinh → emit đúng giá trị. Bản đóng băng `v1.0.0/` nằm sâu
  hơn 1 cấp → patch cộng thêm 1 cấp `..` (transform tất định).
- **Track version docs ≠ plugin version.** Footer ghi chú nhẹ "ứng với plugin 1.5.0" để khỏi lẫn.
- **content.py không tự xoá orphan:** `build.py` chỉ ghi/đè, không xoá. Phải xoá 14 file HTML chết
  thủ công + sửa `GROUPS["doc-gen"]` trong content.py.

## Delta re-sync (đã đối chiếu từng file)

| | Orphan trong docs (XOÁ) | Thiếu (THÊM) |
|---|---|---|
| Skills | 8: `generate-srs`, `generate-api-docs`, `generate-db-design`, `generate-system-architecture`, `generate-code-standards`, `generate-codebase-summary`, `generate-design-guidelines`, `docs-hero-orchestrator` | `writing-docs` |
| Commands | 6: `setup`, `init`, `update-doc`, `sync`, `apply-sync`, `doctor` | `docs` |

Sau re-sync: 19 trang skill + 10 trang command (khớp `plugins/morkit/`).
Stale phụ: URL `github.com/.../claude-plugins` → `morkit-plugin` (vd `docs/docs.html:593`).

## Phases

| # | Phase | Status | Priority | Depends |
|---|-------|--------|----------|---------|
| 01 | [Đóng băng docs hiện tại → v1.0.0](phase-01-freeze-v1.0.0.md) | planned | P1 | — |
| 02 | [Re-sync root về main (thành 1.1.0)](phase-02-resync-root.md) | planned | P1 | — |
| 03 | [Version selector + versions.json](phase-03-version-selector.md) | planned | P1 | 02 |
| 04 | [Patch snapshot v1.0.0 + nghi thức release](phase-04-snapshot-patch-ritual.md) | planned | P2 | 01,03 |
| 05 | [Verify E2E](phase-05-verify.md) | planned | P2 | 02,03,04 |

Lưu ý thứ tự: 01 phải chạy TRƯỚC 02 (đóng băng trạng thái stale làm 1.0.0 trước khi sửa root).

## Key files

- `docs/_scaffolder/content.py` — `GROUPS["doc-gen"]` + các block `CURATED["skills.*"]`/`["commands.*"]`.
- `docs/_scaffolder/build.py` — sinh trang; đọc frontmatter từ `plugins/morkit/{skills,commands}`.
- `docs/_scaffolder/templates.py` — `.topnav` cho mọi trang sinh (nơi nhúng selector).
- `docs/index.html`, `docs/docs.html` — header viết tay (nhúng selector thủ công).
- (mới) `docs/versions.json`, `docs/version-selector.js`.

## Success criteria (toàn plan)

- Site root = 1.1.0, khớp main: 19 skill + 10 command, KHÔNG còn trang `generate-*`/`docs-hero`/
  `sync`/`apply-sync`/`init`/`setup`/`update-doc`/`doctor`; có trang `writing-docs` + `docs`.
- `docs/v1.0.0/` browse được độc lập, là snapshot trung thực của trạng thái cũ.
- Selector hiện 2 mục (1.1.0 mới nhất + 1.0.0); chuyển **hai chiều** đều chạy (kể cả từ trang
  con sâu và từ trong snapshot nhảy về latest).
- Không link gãy, không orphan; theme toggle + nav cũ vẫn hoạt động.
- Có tài liệu nghi thức release để lần sau snapshot đúng quy trình.
