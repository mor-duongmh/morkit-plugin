---
name: kb-sync
description: Sync task changes into a convention-driven knowledge pack (catalog.json + repos/*.md) and keep a weekly ledger of synced tasks. Manual, batch cadence — run by PM/team lead. Scans gRPC (.proto), REST (Gin), models (GORM), Makefile from source; human-gated via checkbox proposal. No prose auto-edits.
license: MIT
---

# kb-sync

Keep a source-extracted knowledge pack in sync with code after tasks land — **only
numeric/structural facts** (RPC / route / table counts, commands), never prose.
Runs as a **weekly batch by a PM/team lead**, not per task.

## Convention

The project declares `knowledge/.kb-sync.json`:
```json
{ "repos_glob": "1stop-*", "repo_name_prefix": "1stop-",
  "repos_root": "..",
  "catalog": "knowledge/catalog.json", "fact_sheets": "knowledge/repos",
  "ledger": "knowledge/_sync-ledger.json", "changes": "knowledge/changes",
  "tickets": "knowledge/tickets",
  "task_summary_template": "knowledge/tickets/_TASK_SUMMARY_TEMPLATE.md",
  "api_doc": "api.md", "update_api_md": true,
  "scanners": ["proto","gin_routes","gorm_models","makefile"] }
```
Nếu khai `tickets`, apply ghi **task-summary theo template** vào `tickets/<task>/summary.md`
(frontmatter + bảng "KB đã cập nhật" máy điền; phần người để `<...>`). Bỏ `tickets` → không ghi.

Any project with this file + a pack (catalog.json + repos/*.md) can use the skill.

**`repos_root`** — nơi chứa các repo source, tương đối với workspace (thư mục cha của `knowledge/`). Hai topology:
- **Pack sống CÙNG code** (repo source là sibling của `knowledge/`): bỏ qua / `"."` (mặc định).
- **Pack là repo RIÊNG** (vd `1stop-knowledge` sibling với 17 repo source): đặt `"repos_root": ".."`.

**REST count**: đếm theo pattern `.METHOD(` trong `repo/router/**/*.go` — khớp cách catalog được dựng (KHÔNG dùng parser Gin đầy đủ của morkit vì đếm khác → false drift).

## Pre-flight

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || { echo "ERROR: run /morkit:setup first"; exit 1; }
```

## Flow (two steps, human gate between)

**Step 1 — PROPOSE (read-only):**
```bash
PY="${HOME}/.claude/plugins/data/docs-hero/.venv/bin/python"
S="${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/skills/kb-sync/scripts"
$PY "$S/kb_sync_propose.py" --config knowledge/.kb-sync.json --output .tmp/kb-sync-proposal.md
```
Hai chế độ scope:
- **Task-driven** (mặc định): scope = union `**Files:**` của các task PENDING trong `knowledge/changes/` (chưa có trong ledger). Hợp pack sống cùng code.
- **Full-scan** (`--all`): quét MỌI repo trong `repos_glob` vs catalog, bỏ qua task. Hợp **pack repo-riêng** (vd 1stop-knowledge) — đây là chế độ drift-gate định kỳ.
  ```bash
  $PY "$S/kb_sync_propose.py" --config knowledge/.kb-sync.json --all --output .tmp/kb-sync-proposal.md
  ```
- Cả hai: scan từ SOURCE; diff vs `catalog.json`; ghi proposal checkbox `.tmp/`. **KHÔNG chạm KB.**

**Human gate (mặc định):** open `.tmp/kb-sync-proposal.md`, tick `[x]` the facts to accept.

**Step 2 — APPLY (writes only checked items):**
```bash
$PY "$S/kb_sync_apply.py" --config knowledge/.kb-sync.json --proposal .tmp/kb-sync-proposal.md
```

**Chế độ AUTO — bỏ human-gate (`--yes` / `--accept-all`):** ghi MỌI mục drift mà không cần tick.
```bash
$PY "$S/kb_sync_apply.py" --config knowledge/.kb-sync.json --proposal .tmp/kb-sync-proposal.md --yes
```
An toàn vì chỉ ghi số tất định (parse_proto/router) + idempotent. **Lưới an toàn = `git diff` trước khi push** (thay cho checkbox). Dùng cho sync hands-free định kỳ.
- Updates `catalog.json` numbers, refreshes fact-sheet provenance + number tokens,
  rolls up `api.md` totals (if `update_api_md`).
- Appends a weekly `sync_run` to `_sync-ledger.json`, marks tasks synced,
  re-renders `SYNC-LOG.md` (with a Pending backlog + drift flags).

## Guardrails

- **Mặc định human-gate**: apply chỉ ghi mục `[x]`. Chế độ `--yes`/`--accept-all` ghi tất cả — chỉ dùng khi user chủ động chọn; lưới an toàn chuyển sang `git diff` trước push.
- **PROPOSE never writes to the KB** — only `.tmp/`.
- **Only numeric/structural facts** sync; prose (role, gotchas) stays for fan-out.
- All KB writes go through `safe_io.resolve_within` — no path escaping the declared dirs.
- git is called with an arg-list (never a shell string).
- Role: skill does not enforce "lead only" (no CLI RBAC) — convention + `synced_by` in the ledger.
