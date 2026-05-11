# Tasks — morkit-docs-site

- [ ] **T1.** Cut branch `docs/morkit-overview-and-detail-pages` off `docs/morkit-landing-html` (PR #21 head).
- [ ] **T2.** Tạo OpenSpec artifacts (proposal.md, design.md, tasks.md) trong `openspec/changes/morkit-docs-site/`.
- [ ] **T3.** Tách CSS tokens từ `docs/docs.html` thành block CSS dùng chung trong scaffolder (sau đó inline lại vào mỗi file output).
- [ ] **T4.** Viết `docs/_scaffolder/templates.py` — string templates cho overview / command / skill.
- [ ] **T5.** Viết `docs/_scaffolder/content.py` — group map + per-item curated `when_to_use` + `example` (fallback nếu thiếu).
- [ ] **T6.** Viết `docs/_scaffolder/build.py` — đọc SKILL.md + command md, parse frontmatter, render, ghi file. Stdlib only (no pip deps).
- [ ] **T7.** Chạy scaffolder → sinh 15 trang `docs/commands/*.html` + 26 trang `docs/skills/*.html`.
- [ ] **T8.** Viết tay `docs/index.html` — overview 5 mục (Cài đặt / Morkit có gì / Slash commands / Plan review gate / Companion tools), mỗi tên skill/command là link đến trang chi tiết tương ứng.
- [ ] **T9.** Sanity check: dùng preview tool mở `docs/index.html`, click thử 2-3 link sang command/skill page, verify theme toggle hoạt động, không có lỗi console.
- [ ] **T10.** Commit theo conventional: `docs: add morkit overview + command/skill detail pages`.
- [ ] **T11.** Push branch lên origin và mở **draft PR** với title `docs: morkit overview + command/skill detail pages`, body link sang PR #21 + screenshot overview + 1 sample skill page.
- [ ] **T12.** Report bản review-ready cho user — list các điểm cần user check (nội dung Vietnamese, "Khi nào dùng" bullets có đúng không, link wiring).
