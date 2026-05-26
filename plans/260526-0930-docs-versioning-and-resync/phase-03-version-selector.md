# Phase 03 — Version selector + versions.json

**Mục tiêu:** Thêm dropdown chọn version ở `.topnav` mọi trang root (1.1.0), đọc từ
`docs/versions.json`. Vanilla JS, không dependency.

## Tasks — versions.json

- [ ] Tạo `docs/versions.json`:
      ```json
      {
        "latest": "1.1.0",
        "versions": [
          { "version": "1.1.0", "label": "mới nhất", "path": "." },
          { "version": "1.0.0", "label": "",         "path": "v1.0.0" }
        ]
      }
      ```
      `path` là đường relative tính từ `docs/` thật. Latest = `"."`.

## Tasks — version-selector.js

- [ ] Tạo `docs/version-selector.js` (vanilla, ~40-60 dòng):
      - Đọc `data-docs-root` từ chính thẻ `<script>` của nó (= đường relative tới `docs/` thật).
      - `fetch(`${root}/versions.json`)` → render `<select>` vào `.nav-actions` (trước nút theme).
      - Xác định version hiện tại: nếu `location.pathname` chứa `/v<x>/` → match `path`, ngược lại = latest.
      - On change → điều hướng `${root}/${path}/index.html` (path `"."` → `${root}/index.html`).
      - Giữ sub-page khi đổi version = TÙY CHỌN nâng cao (bản đầu chỉ về index của version → chống gãy).

## Tasks — nhúng vào 3 nơi

- [ ] `docs/_scaffolder/templates.py`: thêm mount + `<script>` vào `.topnav`. templates.py biết độ
      sâu trang khi sinh → emit `data-docs-root`:
      - trang depth-0 (nếu có) → `"."`
      - trang `skills/*.html`, `commands/*.html` (depth-1) → `".."`
- [ ] `docs/index.html` (viết tay, depth-0): nhúng `<script src="version-selector.js"
      data-docs-root=".">` + mount point trong `.nav-actions`.
- [ ] `docs/docs.html` (viết tay, depth-0): nhúng tương tự.
- [ ] Chạy lại `build.py` để trang skill/command nhận selector.

## Verify

- [ ] Phục vụ local: `python3 -m http.server` trong `docs/` (fetch `versions.json` KHÔNG chạy trên
      `file://` ở vài browser — phải dùng http server).
- [ ] Trang root (index, docs, 1 trang skill, 1 trang command) đều hiện dropdown ở góc trên với 2 mục.
- [ ] Đứng ở latest chọn 1.0.0 → tới `docs/v1.0.0/index.html`.
