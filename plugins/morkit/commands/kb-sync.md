---
description: Sync task changes (RPC/route/table/commands) into a convention-driven knowledge pack + weekly ledger. Batch cadence, run by PM/team lead. Read-only propose → human ticks checkboxes → apply. Needs knowledge/.kb-sync.json.
argument-hint: "[--tasks a,b]  (then apply: --proposal .tmp/kb-sync-proposal.md)"
---

Pre-flight:

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /morkit:setup first." >&2
  exit 1
}
test -f "${PWD}/knowledge/.kb-sync.json" || {
  echo "ERROR: knowledge/.kb-sync.json missing. Create it (see kb-sync SKILL.md convention)." >&2
  exit 1
}
```

Invoke the **kb-sync** skill. It runs the two-step, human-gated flow:

1. **Propose (read-only)** — scan repos from source (proto / router / Makefile), diff vs
   `catalog.json`, write `.tmp/kb-sync-proposal.md` with `[ ]` checkboxes. **KB untouched.** Hai chế độ:
   - mặc định (**task-driven**): scope từ `**Files:**` của task PENDING trong `knowledge/changes/`.
   - `--all` (**full-scan**): quét mọi repo vs catalog (hợp pack repo-riêng như 1stop-knowledge, `repos_root: ".."`).

2. **Human gate** (mặc định) — open the proposal, tick `[x]` the facts to accept.
   **Hoặc bỏ gate**: apply với `--yes` (ghi mọi mục drift, không cần tick) — an toàn nhờ số tất định; review bằng `git diff` trước push.

3. **Apply** — update `catalog.json` + fact-sheet numbers/provenance + `api.md` rollup,
   append `sync_run` to `_sync-ledger.json`, re-render `SYNC-LOG.md`.

Cadence: run as a **weekly batch by a PM / team lead**, not per task. Only
numeric/structural facts sync — prose stays for fan-out.
