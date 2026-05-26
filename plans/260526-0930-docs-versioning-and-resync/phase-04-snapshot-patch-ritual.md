# Phase 04 — Patch snapshot v1.0.0 + nghi thức release

**Mục tiêu:** Cho phép người đang xem bản cũ `v1.0.0` nhảy về latest (snapshot build trước khi có
selector nên chưa có dropdown). Và ghi nghi thức release để lần sau snapshot đúng quy trình.

## Tasks — nhúng selector vào snapshot

- [ ] Copy `docs/version-selector.js` vào `docs/v1.0.0/version-selector.js` (hoặc trỏ chung — nhưng
      copy an toàn hơn cho tính độc lập của snapshot).
- [ ] Vào mọi trang trong `docs/v1.0.0/`, nhúng `<script src="…/version-selector.js"
      data-docs-root="…">` + mount point như phase 03.
- [ ] **Cộng 1 cấp `..` cho `data-docs-root`** (vì snapshot nằm sâu hơn 1 thư mục so với `docs/`):
      - `docs/v1.0.0/index.html` (depth-0 trong snapshot) → `data-docs-root=".."`
      - `docs/v1.0.0/skills/*.html`, `commands/*.html` (depth-1 trong snapshot) → `"../.."`
      Transform tất định — có thể làm bằng script sed/python một lần.
- [ ] `docs/v1.0.0/versions.json`: KHÔNG cần (selector dùng `versions.json` ở docs root thật qua
      `data-docs-root`). Bỏ qua.

## Tasks — footer ghi chú plugin version

- [ ] Thêm dòng nhỏ ở footer (templates.py + index/docs.html) kiểu "Tài liệu 1.1.0 · ứng với plugin
      morkit 1.5.0" để tránh nhầm 2 track version. (Tùy chọn nhưng người dùng đã đồng ý.)

## Tasks — nghi thức release (tài liệu hoá)

- [ ] Ghi quy trình vào `docs/_scaffolder/RELEASING.md` (hoặc cuối `build.py` docstring):
      ```
      Phát hành docs X.Y.Z mới (vd 1.1.0 → 1.2.0):
        1. cp -R docs/(root: index.html, docs.html, skills/, commands/, .nojekyll, version-selector.js) → docs/v1.1.0/
        2. Patch data-docs-root trong docs/v1.1.0/ (cộng 1 cấp '..')
        3. Thêm {"version":"1.1.0", "path":"v1.1.0"} vào docs/versions.json; đổi "latest" + nhãn "mới nhất" sang 1.2.0
        4. Cập nhật plugin/content.py → python3 docs/_scaffolder/build.py (root thành 1.2.0)
      ```

## Verify

- [ ] Trong `docs/v1.0.0/` (qua http server) dropdown hiện 2 mục; đứng ở 1.0.0 chọn "mới nhất" →
      về `docs/index.html` (latest). Chọn từ trang con sâu `v1.0.0/skills/x.html` cũng về đúng.
