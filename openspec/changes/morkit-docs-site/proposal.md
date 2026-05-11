# Proposal — morkit-docs-site

## Why

`docs/docs.html` (PR #21) là landing page kể 4 use case. Người mới mở repo vẫn phải tự đọc `README.md` để biết:

- morkit gồm những gì (4 nhóm chức năng)
- 15 slash command làm gì, gọi như thế nào
- 26 skill làm gì, khi nào dùng

README chỉ liệt kê 1-dòng/item — không đủ cho người dùng lần đầu. Cần một mini docs site giải thích từng command, từng skill với format đơn giản đủ-dùng.

## What changes

Thêm 42 trang HTML thuần (no JS runtime deps) cạnh `docs/docs.html`:

- `docs/index.html` — overview lặp lại nội dung README (bỏ section "Workflow điển hình" và "License"); mỗi tên command/skill trong bảng là link đến trang chi tiết.
- `docs/commands/<name>.html` × 15 — chi tiết từng command theo template "claudekit-slim" (5 mục).
- `docs/skills/<name>.html` × 26 — chi tiết từng skill theo template "claudekit-slim" (4 mục).

Thêm một scaffolder Python (`docs/_scaffolder/build.py`) đọc `plugins/morkit/skills/*/SKILL.md` + `plugins/morkit/commands/*.md`, render qua template chung, ghi ra HTML. Chạy bằng tay khi nội dung đổi; output check vào git → người dùng cuối không cần Node/Python.

**Không động vào** `docs/docs.html` (giữ nguyên PR #21).

## Impact

- Affected paths: `docs/index.html` (mới), `docs/commands/` (mới, 15 file), `docs/skills/` (mới, 26 file), `docs/_scaffolder/` (mới, 1 script + templates), `docs/_assets/` (mới, fonts/icons nếu cần).
- Affected code: không có code runtime — chỉ docs.
- Hosting: GitHub Pages serve trực tiếp `docs/index.html` được.
- Tương thích với PR #21: branch base off `docs/morkit-landing-html` để không conflict; sau khi PR #21 merge → branch này rebase lên main.
