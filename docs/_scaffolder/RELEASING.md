# Phát hành phiên bản tài liệu (versioning — model A)

Site docs theo **model A**: `docs/` root LUÔN là bản mới nhất; mỗi bản cũ được
đóng băng nguyên cây HTML trong `docs/v<version>/`. Selector ở góc trên đọc
`docs/versions.json` để chuyển giữa các bản.

> **Lưu ý:** version của *tài liệu* (1.0.0, 1.1.0, …) chạy track riêng, KHÔNG
> trùng version của *plugin* (`plugins/morkit/.claude-plugin/plugin.json`).

## Thành phần

| File | Vai trò |
|------|---------|
| `docs/versions.json` | Nguồn sự thật danh sách version. `latest` + mảng `versions[{version,label,path}]`. `path:"."` = bản root mới nhất. |
| `docs/version-selector.js` | Vanilla JS. Đọc `data-docs-root` trên thẻ `<script>` → fetch `versions.json` → render `<select>` vào `.version-mount` (hoặc `.nav-actions`/`.crumbs`). |
| `docs/v<version>/` | Snapshot đóng băng của một bản cũ. |

`data-docs-root` = đường relative từ trang hiện tại tới `docs/` thật:
trang root depth-0 → `"."`; trang `skills/`,`commands/` → `".."`;
trong snapshot cộng thêm 1 cấp (`v1.0.0/index.html` → `".."`, `v1.0.0/skills/x.html` → `"../.."`).

## Nghi thức phát hành bản mới (ví dụ 1.1.0 → 1.2.0)

```bash
# 1. Đóng băng bản root hiện tại (1.1.0) thành snapshot
cd docs
mkdir -p v1.1.0
cp index.html docs.html .nojekyll version-selector.js v1.1.0/
cp -R skills v1.1.0/skills
cp -R commands v1.1.0/commands

# 2. Patch selector cho snapshot vừa tạo (cộng 1 cấp '..' cho data-docs-root)
#    Dùng lại scaffolder/patch-snapshot logic, đổi base sang docs/v1.1.0
#    (xem /tmp/patch_snapshot.py hoặc viết tay: data-docs-root '.' → '..', '..' → '../..').

# 3. Thêm bản cũ vào versions.json + nâng "latest"
#    versions.json:
#      "latest": "1.2.0"
#      versions: [ {1.2.0,"mới nhất","."}, {1.1.0,"","v1.1.0"}, {1.0.0,"","v1.0.0"} ]

# 4. Cập nhật nội dung plugin/content.py rồi regenerate root (thành 1.2.0)
python3 docs/_scaffolder/build.py
```

## Kiểm tra

Luôn phục vụ qua HTTP (fetch `versions.json` không chạy trên `file://`):

```bash
cd docs && python3 -m http.server 8000
# mở http://localhost:8000 — selector hiện đủ version, chuyển hai chiều OK.
```

build.py KHÔNG ghi `index.html` (đó là landing v2 viết tay) và tự dọn trang
skill/command orphan khi slug nguồn biến mất.
