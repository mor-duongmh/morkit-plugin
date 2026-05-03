# Mor Claude Plugins

> Marketplace plugin Claude Code của Mor — spec-driven, TDD-first, plug thẳng vào Superpowers.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Cài đặt

Yêu cầu: [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) + Node.js ≥ 18.

```
/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install spec@mor-duongmh
```

Không cần `npm install -g` — CLI chạy qua `npx`.

## Plugin `spec`

Spec-driven workflow trên OpenSpec, tùy chỉnh để `tasks.md` plug thẳng vào `/superpowers:executing-plans` và `/superpowers:subagent-driven-development` mà không cần viết lại.

### Slash commands

| Command | Tham số | Mục đích |
|---------|---------|----------|
| `/spec:setup` | `[path]` | Cài schema vào project (luôn confirm trước khi ghi) |
| `/spec:explore` | — | Suy nghĩ trước khi implement |
| `/spec:propose` | `[description]` | Sinh `proposal.md` + `design.md` + `tasks.md` (TDD-ready) |
| `/spec:apply` | `[change-name]` | Thực thi tasks pending |
| `/spec:archive` | `[change-name]` | Đóng change sau khi merge |

### Workflow

```
/spec:propose  →  /spec:apply  hoặc  /superpowers:executing-plans  →  /spec:archive
```

`tasks.md` sinh ra đã có sẵn Superpowers header (Goal/Architecture/Tech Stack), Files block (Create/Modify/Test paths), và TDD steps — đưa thẳng cho Superpowers, không cần viết lại.

### Schema `superpowers-driven` khác default ở 3 chỗ

1. `design.md` bắt buộc section **`## Tech Stack`** — để `tasks.md` reference, không phải đoán.
2. `tasks.md` mở đầu bằng **Superpowers header** + chú thích `REQUIRED SUB-SKILL`.
3. Mỗi task group có **Files block** + **5 bước TDD bắt buộc** (write test → fail → implement → pass → commit).

## Auto-suggestion

Mở project có `openspec/` nhưng chưa cài schema → plugin gợi ý `/spec:setup` ở đầu session. Tắt vĩnh viễn cho project này:

```bash
touch openspec/.spec-setup-skip
```

`/spec:setup` không bao giờ ghi file mà không confirm path.

## Troubleshooting

- **Commands hiện `/mor-openspec:*` thay vì `/spec:*`** — đang dùng cache cũ → `/plugin update spec@mor-duongmh`.
- **`schema validate` báo lỗi** → xóa `openspec/schemas/superpowers-driven/` và chạy lại `/spec:setup`.

## License

[MIT](LICENSE) © Mor
