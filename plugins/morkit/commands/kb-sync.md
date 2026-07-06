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

1. **Propose (read-only)** — collect PENDING tasks (in `knowledge/changes/`, not yet
   in the ledger), derive scope from each task's `tasks.md` **Files:**, scan in-scope
   repos from source (proto / Gin / GORM / Makefile), diff vs `catalog.json`, and write
   `.tmp/kb-sync-proposal.md` with `[ ]` checkboxes grouped by task. **KB untouched.**

2. **Human gate** — open the proposal, tick `[x]` the facts to accept.

3. **Apply** — `/morkit:kb-sync` with `--proposal .tmp/kb-sync-proposal.md`: update
   `catalog.json` + fact-sheet numbers/provenance + `api.md` rollup, append a weekly
   `sync_run` to `_sync-ledger.json`, re-render `SYNC-LOG.md`.

Cadence: run as a **weekly batch by a PM / team lead**, not per task. Only
numeric/structural facts sync — prose stays for fan-out.
