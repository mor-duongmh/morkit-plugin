# mor-stack — Mor's full Claude Code stack (meta-plugin)

> Cài 1 lệnh, được full bộ tools của Mor.

```
/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install mor-stack@mor-duongmh
```

Lệnh trên auto-install 4 plugin:

| Plugin | Để làm gì |
|---|---|
| **mor-kit** | Tạo proposal/design/tasks + review-checklist gate |
| **superpowers** | Brainstorm, viết plan, thực thi plan, debug, TDD (vendored fork) |
| **deep-review** | Code review tự động bằng 5 specialist subagent |
| **docs-hero** | Sinh tài liệu BrSE: SRS + API + DB |

## Khi nào dùng `mor-stack` vs cài riêng?

- ✅ **Dùng `mor-stack`** nếu ngươi muốn full Mor experience: brainstorm → plan → review → code → review code → doc.
- ⚙️ **Cài riêng từng plugin** nếu chỉ cần một số plugin cụ thể. Ví dụ: dự án không cần BrSE doc → bỏ `docs-hero`; dự án không TDD → bỏ `superpowers`.

## Uninstall toàn bộ

```
/plugin uninstall mor-stack@mor-duongmh
claude plugin prune                          # dọn deps mồ côi
```

## Yêu cầu

- Claude Code ≥ v2.1.110 (cho dependencies feature)
- Node.js ≥ 18

Nếu Claude Code phiên bản cũ hơn, fall back về cài thủ công 4 plugin riêng — xem `README.md` của marketplace.

## License

[MIT](../../LICENSE) © Mor.
