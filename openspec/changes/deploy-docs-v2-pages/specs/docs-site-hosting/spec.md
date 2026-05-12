## ADDED Requirements

### Requirement: Public live site phục vụ docs/ qua GitHub Pages

Repo `mor-duongmh/claude-plugins` SHALL có GitHub Pages enabled, source là `main` branch và folder `/docs`. URL public MUST là `https://mor-duongmh.github.io/claude-plugins/` và MUST trả HTTP 200 cho path root.

#### Scenario: Site root trả về trang v2

- **WHEN** một người dùng truy cập `https://mor-duongmh.github.io/claude-plugins/`
- **THEN** server trả HTTP 200
- **AND** body chứa marker đặc trưng của v2 (ví dụ chuỗi `claudekit-style docs hub` hoặc `data-sec="install"`)

#### Scenario: Trang con `docs.html` (use cases) accessible

- **WHEN** người dùng truy cập `https://mor-duongmh.github.io/claude-plugins/docs.html`
- **THEN** server trả HTTP 200
- **AND** body chứa marker của trang use cases v2 (ví dụ `MORtion · AI Workflow Use Cases`)

#### Scenario: Trang con commands/skills accessible

- **WHEN** người dùng truy cập `https://mor-duongmh.github.io/claude-plugins/commands/propose.html`
- **THEN** server trả HTTP 200
- **AND** không có 404 đối với `commands/*.html` và `skills/*.html` được link từ `index.html`

### Requirement: v2 là entry mặc định, v1 file phải bị remove

Folder `docs/` trên `main` MUST chứa entry mặc định là layout v2. Các file v1 (`docs/index.html` cũ và `docs/docs.html` cũ) MUST bị xoá hoặc thay thế. Sau change này, `docs/index-v2.html` và `docs/docs-v2.html` MUST không tồn tại nữa.

#### Scenario: Không còn file v1 hoặc suffix -v2

- **WHEN** kiểm tra `git ls-files docs/`
- **THEN** không có file `docs/index-v2.html` hoặc `docs/docs-v2.html`
- **AND** `docs/index.html` và `docs/docs.html` tồn tại với content v2 (chứa marker v2, không chứa marker v1)

### Requirement: Internal link giữa các trang v2 phải đúng sau rename

Mọi `<a href>` hoặc reference trong `docs/index.html` và `docs/docs.html` MUST trỏ tới file tồn tại trong cùng folder `docs/`. Không được còn reference tới `docs-v2.html` hay `index-v2.html`.

#### Scenario: Grep không tìm thấy reference đã đổi

- **WHEN** chạy `grep -rE 'docs-v2\.html|index-v2\.html' docs/`
- **THEN** không có kết quả nào

#### Scenario: Mọi link nội bộ resolve được

- **WHEN** parse tất cả `href` relative trong `docs/index.html` và `docs/docs.html`
- **THEN** mỗi target file tồn tại trong filesystem (hoặc là anchor `#` trong cùng trang)

### Requirement: README root chứa link tới live site

File `README.md` ở root repo MUST chứa link rõ ràng tới `https://mor-duongmh.github.io/claude-plugins/`. Link MUST xuất hiện trước section "Cài đặt" (phần đầu README) để người mới mở repo thấy ngay.

#### Scenario: README có live link visible từ top

- **WHEN** đọc 20 dòng đầu của `README.md`
- **THEN** tìm thấy chuỗi `https://mor-duongmh.github.io/claude-plugins/`

#### Scenario: Live link hoạt động

- **WHEN** click vào link trong README qua viewer GitHub
- **THEN** browser navigate tới live site và nhận HTTP 200

### Requirement: Jekyll processing phải bị disable

Folder `docs/` MUST chứa file `.nojekyll` (empty) để GitHub Pages serve HTML tĩnh nguyên bản, không xử lý qua Jekyll (tránh việc bỏ qua các path bắt đầu bằng `_` như `docs/_scaffolder/`).

#### Scenario: File .nojekyll tồn tại

- **WHEN** kiểm tra `ls docs/.nojekyll`
- **THEN** file tồn tại (kích thước có thể là 0 byte)
