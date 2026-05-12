## 1. Branch & preparation

- [x] 1.1 Tạo branch `feat/deploy-docs-v2-pages` off `main` (rebase nếu đang ở branch khác)
- [x] 1.2 `git pull --rebase origin main` để chắc base mới nhất
- [x] 1.3 Xác nhận `docs/index-v2.html` + `docs/docs-v2.html` tồn tại và không có local mod chưa commit

## 2. Promote v2 → entry mặc định (filesystem)

- [x] 2.1 `git rm docs/index.html` (xoá v1 README-mirror)
- [x] 2.2 `git rm docs/docs.html` (xoá v1 use cases / PR #21 landing)
- [x] 2.3 `git mv docs/index-v2.html docs/index.html`
- [x] 2.4 `git mv docs/docs-v2.html docs/docs.html`
- [x] 2.5 Sửa internal link trong `docs/index.html`: tìm/thay `docs-v2.html` → `docs.html` (2 occurrences ở dòng 289 và 322, dùng Edit hoặc `sed`)
- [x] 2.6 Verify: `grep -rE 'docs-v2\.html|index-v2\.html' docs/` không có kết quả

## 3. Jekyll guard & static assets

- [x] 3.1 Tạo `docs/.nojekyll` (empty file) để disable Jekyll
- [x] 3.2 `git add docs/.nojekyll`
- [x] 3.3 Xác nhận `docs/_scaffolder/`, `docs/commands/`, `docs/skills/` vẫn nguyên (không xoá nhầm)

## 4. README live link

- [x] 4.1 Thêm dòng `**Live**: https://mor-duongmh.github.io/claude-plugins/` ngay dưới tagline (sau dòng 3) trong `README.md`
- [x] 4.2 (Optional) Thêm shield.io badge cạnh badge License: `[![Live](https://img.shields.io/badge/live-mor--duongmh.github.io-blue)](https://mor-duongmh.github.io/claude-plugins/)`
- [x] 4.3 Verify 20 dòng đầu README chứa chuỗi `https://mor-duongmh.github.io/claude-plugins/`

## 5. Commit & push

- [x] 5.1 `git status` review: chỉ 2 rename + 2 delete + `.nojekyll` add + 1 edit `index.html` + 1 edit `README.md`
- [ ] 5.2 `git commit -m "feat(docs): promote v2 landing và enable GitHub Pages"`
- [ ] 5.3 `git push -u origin feat/deploy-docs-v2-pages`
- [ ] 5.4 Mở PR qua `gh pr create` (title ngắn, body summary + test plan)

## 6. Enable GitHub Pages (post-merge hoặc trên PR branch để test)

- [ ] 6.1 Đợi PR merge vào `main` (hoặc tạm thời test bằng cách enable Pages trỏ vào branch PR trước)
- [ ] 6.2 Enable Pages: `gh api -X POST /repos/mor-duongmh/claude-plugins/pages -f source[branch]=main -f source[path]=/docs` (cần admin token)
- [ ] 6.3 Hoặc qua UI: Settings → Pages → Source: `Deploy from a branch` → Branch: `main`, folder: `/docs` → Save
- [ ] 6.4 Đợi 1-2 phút cho Pages build lần đầu

## 7. Verify live site

- [ ] 7.1 `curl -sI https://mor-duongmh.github.io/claude-plugins/` → HTTP 200
- [ ] 7.2 `curl -s https://mor-duongmh.github.io/claude-plugins/ | grep -E 'claudekit-style docs hub|data-sec="install"'` → match (xác nhận content v2)
- [ ] 7.3 `curl -sI https://mor-duongmh.github.io/claude-plugins/docs.html` → HTTP 200
- [ ] 7.4 `curl -sI https://mor-duongmh.github.io/claude-plugins/commands/propose.html` → HTTP 200
- [ ] 7.5 `curl -sI https://mor-duongmh.github.io/claude-plugins/skills/brainstorming.html` → HTTP 200
- [ ] 7.6 Mở browser thật, kiểm tra dark mode toggle + sidebar nav + responsive trên màn nhỏ
- [ ] 7.7 Click vài link nội bộ trên live site, đảm bảo không có 404

## 8. Documentation & cleanup

- [ ] 8.1 Update PR body với screenshot live site + verification output
- [ ] 8.2 Nếu Pages build fail: đọc `gh api /repos/mor-duongmh/claude-plugins/pages/builds/latest`, fix, push lại
- [ ] 8.3 Sau khi merge và verify OK: archive change bằng `/opsx:archive deploy-docs-v2-pages`
