# Phase 05 — Verify E2E

**Mục tiêu:** Xác nhận toàn bộ site (latest 1.1.0 + snapshot 1.0.0 + selector) chạy đúng, không
gãy, không orphan.

## Tasks

- [ ] Phục vụ `docs/` qua `python3 -m http.server` (bắt buộc — `fetch(versions.json)` không chạy
      trên `file://`).
- [ ] **Latest (1.1.0):**
      - [ ] `index.html` load, sidebar khớp 19 skill + 10 command, không link 404.
      - [ ] Mở 1 trang skill mới (`writing-docs`) + 1 command mới (`docs`) → render đúng.
      - [ ] Không truy cập được trang `generate-*`/`docs-hero`/`sync`... (đã xoá).
      - [ ] `docs.html` (use cases) load, nội dung không còn nhắc docs-hero/sync.
- [ ] **Selector hai chiều:**
      - [ ] Latest → 1.0.0 (từ index, từ trang skill con).
      - [ ] 1.0.0 → "mới nhất" (từ `v1.0.0/index.html`, từ `v1.0.0/skills/x.html`).
      - [ ] Dropdown đánh dấu đúng version đang xem.
- [ ] **Snapshot (1.0.0):** browse được, nội dung stale nguyên vẹn (history), nav nội bộ ok.
- [ ] Theme toggle (sáng/tối) vẫn hoạt động ở mọi trang.
- [ ] Grep `claude-plugins` ngoài `docs/v1.0.0/` → 0.

## Definition of done

- [ ] Mọi success criteria trong `plan.md` đạt.
- [ ] (Nếu deploy GitHub Pages) kiểm tra lại trên URL pages thật — đường relative + selector chạy
      đúng trong môi trường project-pages (`/<repo>/docs/...`).
