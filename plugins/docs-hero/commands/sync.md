---
description: Scan codebase (ORM models + REST routes) and propose ADD/UPDATE/DEPRECATE changes to api-docs.md and database-design.md. Read-only — no doc changes. User ticks checkboxes, then runs /docs-hero:apply-sync.
argument-hint: "--codebase-paths <comma-separated>"
---

Pre-flight check:

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /docs-hero:setup first." >&2
  exit 1
}
```

Invoke the orchestrator skill with mode `sync`. The skill will:

1. Scan paths via `parse_codebase_models.py` (Prisma/TypeORM/Sequelize/Django/SQLAlchemy/GORM/raw SQL) and `parse_codebase_routes.py` (REST patterns)
2. Diff with current `docs/api-docs.md` and `docs/database-design.md`
3. Write proposals (with `[ ]` checkboxes) to:
   - `${PWD}/.tmp/api-sync-proposal.md`
   - `${PWD}/.tmp/db-sync-proposal.md`
4. **DOES NOT touch docs.** User reviews proposals, ticks `[x]` for what to apply.

Note: SRS sync is intentionally not supported — requirements cannot be safely inferred from code.

Next step:
```
# After ticking checkboxes in proposals:
/docs-hero:apply-sync --proposal .tmp/api-sync-proposal.md
```
