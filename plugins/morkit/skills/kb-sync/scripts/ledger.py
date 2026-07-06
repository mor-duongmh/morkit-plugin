"""kb-sync ledger — weekly sync_runs, synced_tasks map, pending detection, SYNC-LOG.

Ledger records each weekly batch (run by PM/lead) as one `sync_run` covering many
tasks, plus a `synced_tasks` map (task_id → run_id). Renders a human SYNC-LOG.md
with a per-week table, a pending backlog, and a per-repo freshness/drift section.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_PROV = re.compile(r"provenance:\s*extracted\s+(\d{4}-\d{2}-\d{2})")


def load_ledger(path: str | Path) -> dict:
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"last_sync": None, "last_sync_sha": None, "sync_runs": [], "synced_tasks": {}}


def save_ledger(path: str | Path, ledger: dict) -> None:
    Path(path).write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_run(ledger: dict, run_id: str, date: str, synced_by: str,
               sha_range: str, tasks: list[str], changes: list[dict]) -> dict:
    """Append a weekly sync_run and mark its tasks synced."""
    ledger.setdefault("sync_runs", []).append({
        "run_id": run_id, "date": date, "synced_by": synced_by,
        "sha_range": sha_range, "tasks": list(tasks), "changes": changes,
    })
    synced = ledger.setdefault("synced_tasks", {})
    for t in tasks:
        synced[t] = run_id
    ledger["last_sync"] = date
    if sha_range and ".." in sha_range:
        ledger["last_sync_sha"] = sha_range.split("..")[-1]
    return ledger


def pending_tasks(changes_dir: str | Path, ledger: dict) -> list[str]:
    d = Path(changes_dir)
    if not d.exists():
        return []
    synced = set((ledger or {}).get("synced_tasks", {}))
    return [c.name for c in sorted(d.iterdir())
            if c.is_dir() and not c.name.startswith("_") and c.name not in synced]


def read_provenance(fact_sheet: str | Path) -> str | None:
    p = Path(fact_sheet)
    if not p.exists():
        return None
    m = _PROV.search(p.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def compute_drift(provenance_by_repo: dict[str, str | None],
                  last_commit_by_repo: dict[str, str | None]) -> list[str]:
    """Repos whose latest commit date is newer than the fact-sheet provenance."""
    drift = []
    for repo, prov in provenance_by_repo.items():
        commit = last_commit_by_repo.get(repo)
        if prov and commit and commit > prov:
            drift.append(repo)
    return sorted(drift)


def render_sync_log(ledger: dict, pending: list[str], drift: list[str]) -> str:
    runs = ledger.get("sync_runs", [])
    total_tasks = len(ledger.get("synced_tasks", {}))
    lines = ["# Nhật ký sync KB", "",
             f"Tổng: {total_tasks} task đã sync qua {len(runs)} đợt · gần nhất: {ledger.get('last_sync') or '—'}", "",
             "## Đợt sync (theo tuần)", "",
             "| Run | Ngày | Người chạy | #task | #fact |",
             "|-----|------|-----------|-------|-------|"]
    for r in runs:
        lines.append(f"| {r['run_id']} | {r['date']} | {r.get('synced_by','?')} | "
                     f"{len(r.get('tasks',[]))} | {len(r.get('changes',[]))} |")
    lines += ["", "## Pending backlog (đã propose, chưa sync)", ""]
    lines.append("- " + ("\n- ".join(pending) if pending else "(trống — KB đã tươi)"))
    lines += ["", "## Trạng thái tươi theo repo", ""]
    if drift:
        for repo in drift:
            lines.append(f"- ⚠️ **{repo}** — có commit mới hơn provenance (nghi drift, cần sync)")
    else:
        lines.append("- ✅ Không phát hiện drift")
    return "\n".join(lines) + "\n"


def write_sync_log(path: str | Path, ledger: dict, pending: list[str], drift: list[str]) -> None:
    Path(path).write_text(render_sync_log(ledger, pending, drift), encoding="utf-8")
