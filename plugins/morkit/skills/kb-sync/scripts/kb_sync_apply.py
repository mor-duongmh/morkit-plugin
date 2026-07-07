"""kb-sync step 2 — APPLY (writes to KB, only checked items).

Parses `[x]` items from a proposal, updates catalog.json (authoritative numbers),
refreshes fact-sheet provenance + conservative number tokens, optionally rolls up
api.md totals. All writes go through safe_io.resolve_within. Idempotent.

CLI:
    kb_sync_apply.py --config knowledge/.kb-sync.json --proposal .tmp/kb-sync-proposal.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))
from safe_io import resolve_within  # noqa: E402
from parse_proto import scan_protos, total_rpc  # noqa: E402
from ledger import (  # noqa: E402
    append_run, load_ledger, pending_tasks, save_ledger, write_sync_log,
)

_CHECKED = re.compile(
    r"^\s*-\s*\[x\]\s*\*\*(?P<repo>[^*]+)\*\*\s+(?P<type>\w+):\s*(?P<old>\S+)\s*→\s*(?P<new>\d+)",
    re.MULTILINE,
)
# accept-all: khớp mọi mục ứng viên, cả [ ] lẫn [x] (bỏ human-gate)
_CANDIDATE = re.compile(
    r"^\s*-\s*\[[ xX]\]\s*\*\*(?P<repo>[^*]+)\*\*\s+(?P<type>\w+):\s*(?P<old>\S+)\s*→\s*(?P<new>\d+)",
    re.MULTILINE,
)
_TASK_HDR = re.compile(r"^##\s*Task:\s*(\S+)", re.MULTILINE)
_PROV = re.compile(r"(provenance:\s*extracted\s+)(\d{4}-\d{2}-\d{2})")


def parse_tasks(text: str) -> list[str]:
    """Task ids present in the proposal (## Task: <id>)."""
    return _TASK_HDR.findall(text)


def _iso_run_id(today: str) -> str:
    import datetime
    y, w, _ = datetime.date.fromisoformat(today).isocalendar()
    return f"{y}-W{w:02d}"


def parse_checked(text: str, accept_all: bool = False) -> list[dict]:
    out = []
    rx = _CANDIDATE if accept_all else _CHECKED
    for m in rx.finditer(text):
        old = m.group("old")
        out.append({"repo": m.group("repo").strip(), "type": m.group("type"),
                    "old": None if old == "∅" else int(old) if old.isdigit() else old,
                    "new": int(m.group("new"))})
    return out


def apply_catalog(catalog_path: Path, checked: list[dict]) -> int:
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    by_name = {r["name"]: r for r in data.get("repos", [])}
    n = 0
    for c in checked:
        r = by_name.get(c["repo"])
        if r is not None and r.get(c["type"]) != c["new"]:
            r[c["type"]] = c["new"]
            n += 1
    catalog_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return n


_UNIT = {"grpc_rpc": "RPC", "rest_routes": "route"}


def refresh_fact_sheet(fact_dir: Path, repo: str, checked: list[dict], today: str) -> bool:
    fs = fact_dir / f"{repo}.md"
    if not fs.exists():
        return False
    text = fs.read_text(encoding="utf-8")
    for c in checked:
        unit = _UNIT.get(c["type"])
        if unit and c["old"] is not None:
            text = re.sub(rf"\b{c['old']}\s+{unit}\b", f"{c['new']} {unit}", text)
    text = _PROV.sub(rf"\g<1>{today}", text)
    fs.write_text(text, encoding="utf-8")
    return True


def update_api_rollup(api_path: Path, grpc_total: int) -> bool:
    """Conservatively replace the gRPC grand-total number ('<n> RPC') in api.md."""
    if not api_path.exists():
        return False
    text = api_path.read_text(encoding="utf-8")
    updated = re.sub(r"\b\d+ RPC\b", f"{grpc_total} RPC", text)
    api_path.write_text(updated, encoding="utf-8")
    return updated != text


def apply(config_path: str | Path, proposal_path: str | Path, today: str,
          synced_by: str = "lead", sha_range: str = "", accept_all: bool = False) -> dict:
    cfg_path = Path(config_path).resolve()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    workspace = cfg_path.parent.parent
    proposal_text = Path(proposal_path).read_text(encoding="utf-8")
    checked = parse_checked(proposal_text, accept_all=accept_all)
    tasks = parse_tasks(proposal_text)

    catalog_path = resolve_within(workspace, cfg["catalog"])
    applied = apply_catalog(catalog_path, checked)

    fact_dir = resolve_within(workspace, cfg["fact_sheets"])
    touched_repos = sorted({c["repo"] for c in checked})
    for repo in touched_repos:
        refresh_fact_sheet(fact_dir, repo, [c for c in checked if c["repo"] == repo], today)

    if cfg.get("update_api_md") and cfg.get("api_doc"):
        api_path = resolve_within(workspace, cfg["api_doc"])
        grpc_total = total_rpc(scan_protos([str(workspace)]))
        update_api_rollup(api_path, grpc_total)

    # Ledger: record this weekly run + re-render SYNC-LOG
    ledger_path = resolve_within(workspace, cfg["ledger"])
    ledger = load_ledger(ledger_path)
    run_id = _iso_run_id(today)
    append_run(ledger, run_id, today, synced_by, sha_range, tasks, checked)
    save_ledger(ledger_path, ledger)
    changes_dir = resolve_within(workspace, cfg["changes"])
    pending = pending_tasks(changes_dir, ledger)
    write_sync_log((fact_dir.parent / "SYNC-LOG.md"), ledger, pending, [])

    return {"applied": applied, "repos": touched_repos, "changes": checked,
            "run_id": run_id, "tasks": tasks, "pending": pending}


def main(argv: list[str] | None = None) -> int:
    import datetime
    ap = argparse.ArgumentParser(description="kb-sync: apply checked proposal items to the KB")
    ap.add_argument("--config", required=True)
    ap.add_argument("--proposal", required=True)
    ap.add_argument("--today", default=datetime.date.today().isoformat())
    ap.add_argument("--by", default="lead", help="who ran this sync (recorded in ledger)")
    ap.add_argument("--sha-range", default="", help="optional git sha range, e.g. a..b")
    ap.add_argument("--accept-all", "--yes", action="store_true", dest="accept_all",
                    help="BỎ human-gate: ghi MỌI mục drift (cả [ ]), không cần tick. "
                         "An toàn nhờ số tất định + idempotent; review bằng git diff trước push.")
    args = ap.parse_args(argv)
    res = apply(args.config, args.proposal, args.today, synced_by=args.by,
                sha_range=args.sha_range, accept_all=args.accept_all)
    print(f"[{res['run_id']}] applied {res['applied']} change(s) across {len(res['repos'])} repo(s): "
          f"{', '.join(res['repos'])} · {len(res['pending'])} task(s) still pending")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
