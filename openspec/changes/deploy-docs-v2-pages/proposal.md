## Why

`docs/index-v2.html` + `docs/docs-v2.html` (cùng folder `docs/commands/`, `docs/skills/`) đã sẵn sàng làm landing page chính cho marketplace, nhưng repo chưa enable GitHub Pages — README hiện chỉ liệt kê command/skill bằng text, không có link tới trang demo live. Người dùng mới phải clone repo mới xem được v2.

## What Changes

- **BREAKING**: Xoá `docs/index.html` (v1) và `docs/docs.html` (v1 PR #21 landing) khỏi folder docs; promote v2 thành entry mặc định bằng cách rename `docs/index-v2.html` → `docs/index.html` và `docs/docs-v2.html` → `docs/docs.html`.
- Sửa các internal link trong `docs/index.html` (mới) từ `docs-v2.html` → `docs.html` để khớp tên file sau rename.
- Enable GitHub Pages cho repo `mor-duongmh/claude-plugins`: source = `main` branch, folder `/docs`.
- Thêm section "Live site" (hoặc badge) trong `README.md` ở root, link tới `https://mor-duongmh.github.io/claude-plugins/`.
- Verify các trang con (`docs/commands/*.html`, `docs/skills/*.html`) load đúng qua URL live.

## Capabilities

### New Capabilities
- `docs-site-hosting`: Public GitHub Pages site phục vụ documentation site từ folder `docs/` trên main, bao gồm policy về entry file, internal link conventions, và link discoverability từ README.

### Modified Capabilities
<!-- Không có spec hiện có để sửa — repo chưa có openspec/specs/ folder. -->

## Impact

- **Affected paths**:
  - Xoá: `docs/index.html` (v1), `docs/docs.html` (v1)
  - Rename: `docs/index-v2.html` → `docs/index.html`, `docs/docs-v2.html` → `docs/docs.html`
  - Sửa internal link trong `docs/index.html` (file mới sau rename)
  - Update: `README.md` ở root repo
- **Affected code**: Không có runtime code — chỉ HTML tĩnh + README markdown.
- **External dependencies**: GitHub Pages (Settings → Pages → Source: main /docs). Cần quyền admin repo để enable.
- **Hosting URL**: `https://mor-duongmh.github.io/claude-plugins/` (path mặc định cho user-repo Pages).
- **Compatibility**:
  - PR #21 (`morkit-docs-site`) đã merge `docs/docs.html` v1 — change này thay thế bằng v2.
  - Bookmark `/docs.html` cũ vẫn hoạt động (URL không đổi, content là v2 mới).
  - Bookmark `/index-v2.html` cũ sẽ vỡ — chấp nhận vì chưa publish.
