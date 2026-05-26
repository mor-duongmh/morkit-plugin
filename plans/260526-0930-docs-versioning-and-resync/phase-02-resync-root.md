# Phase 02 — Re-sync root docs về main (nội dung thành 1.1.0)

**Mục tiêu:** Đưa site ở `docs/` root khớp đúng `plugins/morkit/` trên main: bỏ docs-hero, thêm
`writing-docs` + `docs`, sửa URL stale, regenerate.

## Tasks — content.py

- [ ] Sửa `GROUPS["doc-gen"]` trong `docs/_scaffolder/content.py`:
      - `skills`: `["writing-docs"]`
      - `commands`: `["docs"]`
- [ ] Xoá các block `CURATED` cũ: `skills.docs-hero-orchestrator`, `skills.generate-srs`,
      `skills.generate-api-docs`, `skills.generate-db-design`, `skills.generate-system-architecture`,
      `skills.generate-code-standards`, `skills.generate-codebase-summary`,
      `skills.generate-design-guidelines`, và các block command `setup/init/update-doc/sync/
      apply-sync/doctor`.
- [ ] Thêm block `CURATED["skills.writing-docs"]` + `CURATED["commands.docs"]`
      (lede / when_to_use / example_args / example_note tiếng Việt). Nếu thiếu, build.py dùng
      fallback frontmatter — nhưng nên viết curated cho chất lượng.

## Tasks — xoá orphan + sửa URL

- [ ] Xoá 14 file HTML chết (build.py KHÔNG tự xoá):
      - `docs/skills/`: `generate-srs.html`, `generate-api-docs.html`, `generate-db-design.html`,
        `generate-system-architecture.html`, `generate-code-standards.html`,
        `generate-codebase-summary.html`, `generate-design-guidelines.html`,
        `docs-hero-orchestrator.html`
      - `docs/commands/`: `setup.html`, `init.html`, `update-doc.html`, `sync.html`,
        `apply-sync.html`, `doctor.html`
- [ ] Grep + thay `mor-duongmh/claude-plugins` → `mor-duongmh/morkit-plugin` trong `docs/docs.html`
      (vd dòng 593), `docs/index.html`, `docs/_scaffolder/templates.py` (nếu có).
- [ ] Kiểm tra `docs.html`/`index.html` có còn nhắc tên skill/command docs-hero (sync, generate-*,
      docs-hero) trong nội dung viết tay → cập nhật cho khớp `writing-docs`/`docs`.

## Tasks — regenerate

- [ ] Chạy `python3 docs/_scaffolder/build.py` từ repo root.
- [ ] Đối chiếu kết quả: `docs/skills/` = 19 file, `docs/commands/` = 10 file (khớp
      `plugins/morkit/skills` 19 + `commands` 10). Có `writing-docs.html` + `docs.html`.

## Verify

- [ ] `ls docs/skills | wc -l` = 19, `ls docs/commands | wc -l` = 10.
- [ ] Không còn file `generate-*` / `docs-hero-orchestrator` / `sync` / `apply-sync` / `init` /
      `setup` / `update-doc` / `doctor` trong `docs/skills|commands`.
- [ ] Grep `claude-plugins` trong `docs/` (trừ `docs/v1.0.0/`) → 0 kết quả.
- [ ] Nav sidebar trong `index.html` không trỏ tới trang đã xoá (404).
