---
description: Scan codebase and propose ADD/UPDATE/DEPRECATE changes to the 5 code-derived docs (api-docs, database-design, codebase-summary, system-architecture, code-standards). Read-only — no doc changes. User ticks checkboxes, then runs /morkit:apply-sync.
argument-hint: "--codebase-paths <comma-separated>"
---

Pre-flight check:

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /morkit:setup first." >&2
  exit 1
}
```

Invoke the orchestrator skill with mode `sync`. It proposes ADD/UPDATE/DEPRECATE
for the **5 code-derived docs** — each `*_sync_propose.py` scans for its own signals:

| Doc | Scanned signals |
|---|---|
| `api-docs.md` | REST routes (Express/Nest/FastAPI/Django/Gin…) |
| `database-design.md` | ORM models (Prisma/TypeORM/Sequelize/Django/SQLAlchemy/GORM/raw SQL) |
| `codebase-summary.md` | file tree + manifests + LOC by language |
| `system-architecture.md` | services / packages / Dockerfile / k8s / import graph |
| `code-standards.md` | lint / format / commit configs |

The skill will:

1. Run each doc's `*_sync_propose.py` over `--codebase-paths`
2. Diff against the current doc in `docs/`
3. Write proposals (with `[ ]` checkboxes) to `${PWD}/.tmp/`:
   - `api-sync-proposal.md`, `db-sync-proposal.md`, `codebase-summary-sync-proposal.md`,
     `system-architecture-sync-proposal.md`, `code-standards-sync-proposal.md`
4. **DOES NOT touch docs.** User reviews proposals, ticks `[x]` for what to apply.

Not supported (cannot be safely inferred from code): **SRS** (requirements) and
**design-guidelines** (ADRs are manual).

Next step:
```
# After ticking checkboxes in the proposals you care about (repeat per edited proposal):
/morkit:apply-sync --proposal .tmp/codebase-summary-sync-proposal.md
```
