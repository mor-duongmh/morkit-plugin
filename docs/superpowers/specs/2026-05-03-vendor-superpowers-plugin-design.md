# Design: Vendor Superpowers as a Sibling Plugin

**Date:** 2026-05-03
**Author:** Mor (Hai Duong)
**Status:** Draft — pending implementation
**Related:** PR #1 (slim README + skill fixes) must merge first

## 1. Problem & Goals

Marketplace `mor-duongmh/claude-plugins` hiện chỉ có 1 plugin `spec` (workflow OpenSpec spec-driven của Mor). Plugin `spec` có nhiều tham chiếu chéo tới `superpowers:*` skills (qua tasks.md template, skill output, README workflow), nhưng những skills đó thuộc plugin upstream `obra/superpowers` — **không nằm trong marketplace của Mor**.

User muốn:
1. Marketplace của Mor "đóng gói" được Superpowers — user cài Superpowers từ chính marketplace này thay vì phải cài hai marketplace riêng.
2. Tách bạch hai plugin (`spec` + `superpowers`), không gộp một plugin.
3. Vendored Superpowers giữ nguyên xi (as-is), customization tương lai qua overlay.
4. Sync upstream qua manual snapshot script (không submodule, không subtree).

### Non-goals

- Auto-install policy (`installation: "AUTO"`) — chấp nhận user gõ 3 lệnh cài.
- Plugin name khác `superpowers` cho fork — name phải là `superpowers` để giữ 34 cross-references nội tại không vỡ.
- Append-mode overlay — chỉ replace toàn file ở v1.
- Auto drift detection khi sync upstream — manual diff khi cần.
- CI tự động sync nightly — defer.

## 2. Architecture

Marketplace chứa **2 plugin tách biệt**, cài độc lập:

```
mor-duongmh/claude-plugins
├── spec@mor-duongmh         (existing — Mor's OpenSpec workflow)
└── superpowers@mor-duongmh  (new — vendored fork of obra/superpowers)
```

User flow (3 lệnh global, 1 lần mỗi máy):

```
/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install spec@mor-duongmh
/plugin install superpowers@mor-duongmh
```

Sau đó các slash commands `/spec:*` (Mor) và `/superpowers:*` (vendored) cùng tồn tại không xung đột.

**Plugin name = `superpowers`** (không phải `mor-superpowers`) là quyết định cốt lõi. Lý do: source upstream có 34 hardcoded references dạng `superpowers:executing-plans`, `superpowers:subagent-driven-development`, etc. trong nội dung skills. Plugin name phải khớp để các references này resolve đúng. Đổi tên = phải rewrite 34 chỗ = phá nguyên tắc "vendor as-is" + tăng maintenance khi sync upstream.

Trade-off: user nào đang cài upstream `superpowers@obra` sẽ phải uninstall trước khi cài `superpowers@mor-duongmh` (cùng plugin name → collision). Mor's plugin được thiết kế là **drop-in replacement** chứ không coexist.

## 3. Folder structure

```
claude-plugins/
├── .claude-plugin/
│   └── marketplace.json                    [UPDATED — thêm entry superpowers]
├── README.md                                [UPDATED — mention 2 plugins]
├── LICENSE
└── plugins/
    ├── spec/                                [unchanged sau PR #1]
    │   └── ...
    │
    └── superpowers/                         [NEW]
        ├── .claude-plugin/plugin.json       [name: "superpowers"]
        ├── README.md                        [plugin-level, ngắn]
        ├── ATTRIBUTION.md                   [credit obra + MIT notice]
        ├── LICENSE                          [copy MIT của upstream]
        ├── .vendor-manifest.json            [version, sha256, fetched_at, paths]
        │
        ├── scripts/
        │   ├── sync-superpowers.sh          [refresh vendored layer]
        │   ├── verify-vendor.sh             [check sha256 still matches]
        │   └── start-overlay.sh             [helper: copy live skill → overlay/]
        │
        ├── overlay/                         [Mor customization — RỖNG ngày hôm nay]
        │   ├── README.md
        │   └── .gitkeep
        │
        ├── skills/                          [VENDORED 100% — 14 dirs]
        ├── commands/                        [VENDORED 100% — 3 files]
        └── agents/                          [VENDORED 100%]
```

Nguyên tắc:
- `skills/`, `commands/`, `agents/` ở `superpowers/` là **flat folder** (Claude Code yêu cầu) và **100% vendored**.
- File Mor-owned chỉ ở `.claude-plugin/`, `README.md`, `ATTRIBUTION.md`, `LICENSE`, `.vendor-manifest.json`, `scripts/`, `overlay/`.
- `overlay/` rỗng ngày hôm nay; sync script đọc từ đây nhưng không có gì để apply.

## 4. Sync script

**File:** `plugins/superpowers/scripts/sync-superpowers.sh`

### Inputs

```bash
./scripts/sync-superpowers.sh           # đọc version từ .vendor-manifest.json
./scripts/sync-superpowers.sh 5.1.0     # bump tới version cụ thể
./scripts/sync-superpowers.sh --dry-run 5.1.0
```

### Flow

1. **Resolve target version** — arg > manifest current version > error.
2. **Confirm with user** — print current vs target; abort nếu user từ chối.
3. **Check git clean state** — abort nếu `skills/` `commands/` `agents/` có uncommitted changes (tránh nuốt mất work).
4. **Download tarball** từ `https://github.com/obra/superpowers/archive/refs/tags/v<version>.tar.gz`.
5. **Compute SHA256** của tarball:
   - Nếu manifest đã có `tarball_sha256` cho version đang sync → **verify khớp**, fail-loud nếu mismatch (catch tampering hoặc upstream re-tag).
   - Nếu manifest chưa có (lần đầu sync version này) → **compute & store** vào manifest. Không có external trust anchor ở v1.
6. **Extract vào `mktemp -d`** — atomic-ish.
7. **Wipe vendored dirs** — `rm -rf plugins/superpowers/{skills,commands,agents}` + `LICENSE`.
8. **Copy từ tempdir** — chỉ `skills/`, `commands/`, `agents/`, `LICENSE`.
9. **Apply overlay** (nếu `overlay/` có content) — copy `overlay/skills/*` đè lên `skills/*` (replace mode).
10. **Update `.vendor-manifest.json`** — version, tarball_url, tarball_sha256, fetched_at, fetched_by.
11. **Print git diff stat + suggest commit message** — không tự commit.

### `.vendor-manifest.json` schema

```json
{
  "name": "obra/superpowers",
  "source": "https://github.com/obra/superpowers",
  "version": "5.0.7",
  "tarball_url": "https://github.com/obra/superpowers/archive/refs/tags/v5.0.7.tar.gz",
  "tarball_sha256": "<computed>",
  "fetched_at": "2026-05-03T08:30:00Z",
  "fetched_by": "scripts/sync-superpowers.sh",
  "vendored_paths": ["skills/", "commands/", "agents/", "LICENSE"]
}
```

### Safety rules

- Bash strict mode (`set -euo pipefail`).
- Confirm prompt trước khi wipe.
- Verify SHA256 trước khi extract.
- Extract vào `mktemp -d`, copy sau khi verify.
- Idempotent — chạy lại cùng version = no-op (skip nếu manifest version khớp & overlay không đổi).

### Dependencies

`curl`, `tar`, `shasum` (fallback `sha256sum`), `jq`, `git`. Script kiểm tra availability ở đầu, abort with friendly message nếu thiếu.

## 5. Overlay infrastructure

### Quy tắc

```
For each path in overlay/<dir>/:
    target = <dir>/<same-relative-path>
    if target exists:
        REPLACE target with overlay file        # full replacement
    else:
        ADD overlay file to live folder          # Mor-only new skill
```

### 3 use cases

| Use case | File trong overlay | Hiệu ứng |
|----------|-------------------|----------|
| Override skill upstream | `overlay/skills/test-driven-development/SKILL.md` | Replace bản vendored sau sync |
| Thêm skill Mor-only | `overlay/skills/mor-code-style/SKILL.md` | Skill mới, không trùng upstream |
| Override agent | `overlay/agents/code-reviewer.md` | Replace agent vendored |

### Workflow bắt đầu overlay

```bash
./scripts/start-overlay.sh skills/test-driven-development
# → copy skills/test-driven-development → overlay/skills/test-driven-development
# → tạo overlay/.../.overlay-meta.json (track base version)
```

`.overlay-meta.json`:
```json
{
  "overlay_path": "skills/test-driven-development",
  "based_on_upstream_version": "5.0.7",
  "created_at": "2026-...",
  "note": "free-form lý do customize"
}
```

### Drift detection (defer)

Khi sync upstream lên version mới hơn `based_on_upstream_version`, script có thể warn rằng overlay có thể đã outdated. Implement ở v2 — v1 chỉ apply overlay không warn.

### Trạng thái ngày hôm nay

`overlay/` chỉ chứa `README.md` + `.gitkeep`. Không overlay nào tồn tại; plugin hoạt động như "vendor as-is" thuần túy.

## 6. Marketplace.json + plugin.json updates

### `claude-plugins/.claude-plugin/marketplace.json`

Thêm entry thứ hai:

```json
{
  "name": "superpowers",
  "description": "Mor's vendored fork of obra/superpowers — same skills as upstream, pinned and synced via script. Replaces upstream superpowers@obra in this marketplace.",
  "source": "./plugins/superpowers",
  "category": "development",
  "author": {
    "name": "Jesse Vincent (upstream) / Mor (vendoring)",
    "email": "duongmh@mor.com.vn"
  },
  "homepage": "https://github.com/mor-duongmh/claude-plugins/tree/main/plugins/superpowers"
}
```

### `plugins/superpowers/.claude-plugin/plugin.json`

```json
{
  "name": "superpowers",
  "version": "5.0.7-mor.1",
  "description": "Vendored fork of obra/superpowers. Skills, commands, and agents are mirrored as-is from upstream; sync via scripts/sync-superpowers.sh. Mor customizations live in overlay/.",
  "author": { "name": "Mor (Hai Duong)", "email": "duongmh@mor.com.vn" },
  "homepage": "https://github.com/mor-duongmh/claude-plugins/tree/main/plugins/superpowers",
  "repository": "https://github.com/mor-duongmh/claude-plugins",
  "license": "MIT",
  "keywords": ["superpowers", "tdd", "skills", "vendored-fork"]
}
```

**Convention version:** `<upstream-version>-mor.<vendor-revision>`. Ví dụ `5.0.7-mor.1` → vendored upstream 5.0.7, Mor revision 1.

### `ATTRIBUTION.md`

Credit upstream rõ ràng, MIT notice, giải thích tại sao vendor và tại sao tên plugin là `superpowers`. Nội dung chi tiết đã thống nhất ở Section 5 brainstorming.

### `LICENSE`

Copy nguyên xi LICENSE MIT của upstream (yêu cầu của MIT khi redistribute). Không thêm copyright Mor riêng vào file này; nếu tương lai overlay/ cần copyright riêng, sẽ tạo `overlay/LICENSE` độc lập.

## 7. Testing strategy

| # | Test | Cách chạy | Pass criterion |
|---|------|-----------|---------------|
| 1 | Sync dry-run | `./scripts/sync-superpowers.sh --dry-run 5.0.7` | Print expected changes, không ghi gì |
| 2 | Sync smoke | `./scripts/sync-superpowers.sh 5.0.7` lần đầu | `skills/` có 14 dirs, `commands/` 3 files, `agents/` ≥1, manifest đúng |
| 3 | Idempotency | Chạy sync lần 2 cùng version | No-op, log "already at 5.0.7" |
| 4 | Vendor verify | `./scripts/verify-vendor.sh` | SHA256 hiện tại khớp manifest |
| 5 | Plugin install smoke (manual) | `/plugin add marketplace ...` rồi `/plugin install superpowers@mor-duongmh` | Skills `superpowers:*` xuất hiện |
| 6 | Cross-reference (manual) | Trong session, invoke `superpowers:executing-plans` skill | 34 internal refs resolve đúng |
| 7 | E2E với spec plugin (manual) | Cài cả `spec@mor-duongmh` + `superpowers@mor-duongmh`, chạy `/spec:propose` | Output gợi ý 3 paths Superpowers; chọn `subagent-driven-development` resolve được |
| 8 | Overlay flow (manual) | Tạo overlay file thủ công, chạy sync, verify live folder dùng overlay version | Replace mode hoạt động |

Plugin là content-only nên không có unit test runtime. Sync script có thể test bằng bash test framework (bats) ở tương lai.

## 8. Migration plan

Phụ thuộc PR #1 (slim README + skill fixes) merge trước.

```
1. Merge PR #1
2. Branch: feat/add-superpowers-plugin
3. Add scaffolding plugins/superpowers/ (plugin.json, README, ATTRIBUTION, LICENSE placeholder, manifest stub, scripts/, overlay/)
4. Write & test sync-superpowers.sh (test 1-3)
5. Run sync 5.0.7 → populate skills/ commands/ agents/ + LICENSE thật
6. Manual smoke (test 5-7)
7. Update marketplace.json (thêm entry superpowers)
8. Update top-level README.md (mention 2 plugins, 3-command install flow)
9. Commit + PR + review
10. Merge → tag v0.4.0
```

## 9. Rollout

- **Branch:** `feat/add-superpowers-plugin` (sau khi PR #1 merge).
- **PR title:** *Add vendored superpowers plugin alongside spec*.
- **PR body:** link tới design doc này, list 9 sections, screenshots smoke test outputs.
- **Tag:** `v0.4.0` sau merge — đánh dấu milestone marketplace có 2 plugin.
- **README announce:** subsection "What's new in v0.4.0" trong top-level README.

## 10. Open questions / future work

- Add CI workflow chạy `verify-vendor.sh` mỗi PR (catch broken syncs).
- Append-mode overlay (concatenate thay vì replace).
- Auto drift detection khi sync upstream version mới.
- Plugin signing / supply chain hardening.
- Auto-install policy — verify Claude Code có hỗ trợ `installation: "AUTO"` rồi reconsider số lệnh cài.

---

**Decisions log (từ brainstorming):**

| # | Quyết định | Rationale |
|---|-----------|-----------|
| 1 | 2 plugin tách biệt (spec + superpowers) | User pivot từ "1 plugin gộp" sang "2 plugin tách" để tránh đụng nội tại Superpowers |
| 2 | 3 lệnh install (β) | Đơn giản, chắc chắn hoạt động, không phụ thuộc tính năng chưa verify |
| 3 | Vendor as-is, customize sau qua overlay (C) | Ship nhanh, tránh fork dead-on-arrival |
| 4 | Manual snapshot via script (B) | Pin version chính xác, contributors mới không phải biết submodule |
| 5 | Plugin name = `superpowers` (A) | Giữ 34 cross-references nguyên vẹn |
| 6 | Drop-in replacement upstream | User trade-off chấp nhận: không coexist với `superpowers@obra` |
