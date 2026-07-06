"""kb-sync step 1 — PROPOSE (read-only).

Batch/weekly flow (run by PM/lead): collect PENDING tasks (proposed but not yet in
the ledger), derive scope from each task's tasks.md `**Files:**`, scan those repos
from SOURCE, diff vs catalog.json, and emit a checkbox proposal grouped by task.

**Never touches the knowledge base** — only writes the proposal to `.tmp/`.

CLI:
    kb_sync_propose.py --config knowledge/.kb-sync.json [--tasks a,b] --output .tmp/kb-sync-proposal.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))

from safe_io import resolve_within, validate_config  # noqa: E402
from parse_proto import scan_protos  # noqa: E402
from scan_makefile import scan_makefile  # noqa: E402

_FILE_LINE = re.compile(r"^\s*-\s*(?:Create|Modify|Delete)\s*:\s*`([^`]+)`", re.MULTILINE)
# REST route: đếm theo pattern đơn giản, phạm vi router/ — khớp cách catalog được dựng
# (parser Gin đầy đủ của morkit đếm KHÁC → gây false drift, nên KHÔNG dùng ở đây).
_ROUTE = re.compile(r"\.(?:GET|POST|PUT|PATCH|DELETE)\(")


def count_rest_routes(repo_dir: Path) -> int:
    """Đếm route trong repo_dir/router/**/*.go bằng pattern đơn giản (tất định)."""
    router = repo_dir / "router"
    base = router if router.is_dir() else repo_dir
    return sum(len(_ROUTE.findall(f.read_text(encoding="utf-8", errors="replace")))
               for f in base.rglob("*.go"))


# ---------- config / ledger ----------

def load_config(config_path: str | Path) -> tuple[dict, Path]:
    cfg_path = Path(config_path).resolve()
    cfg = validate_config(json.loads(cfg_path.read_text(encoding="utf-8")))
    workspace = cfg_path.parent.parent  # .../<workspace>/knowledge/.kb-sync.json
    return cfg, workspace


def load_ledger(workspace: Path, cfg: dict) -> dict:
    lp = resolve_within(workspace, cfg["ledger"])
    if lp.exists():
        return json.loads(lp.read_text(encoding="utf-8"))
    return {"synced_tasks": {}, "sync_runs": []}


# ---------- pending detection ----------

def list_pending(workspace: Path, cfg: dict, ledger: dict) -> list[str]:
    """Task folders under `changes/` (excl. `_archive`, `_*`) not in synced_tasks."""
    changes = resolve_within(workspace, cfg["changes"])
    synced = set((ledger or {}).get("synced_tasks", {}))
    if not changes.exists():
        return []
    out = []
    for d in sorted(changes.iterdir()):
        if d.is_dir() and not d.name.startswith("_") and d.name not in synced:
            out.append(d.name)
    return out


# ---------- scope ----------

def files_in_task(task_dir: Path) -> list[str]:
    tasks_md = task_dir / "tasks.md"
    if not tasks_md.exists():
        return []
    return _FILE_LINE.findall(tasks_md.read_text(encoding="utf-8"))


def files_to_repos(files: list[str], repo_names: list[str]) -> set[str]:
    """Map file paths → repo names by first matching path segment."""
    repos: set[str] = set()
    for f in files:
        parts = Path(f).parts
        for name in repo_names:
            if name in parts:
                repos.add(name)
                break
    return repos


def repo_dirs(repos_root: Path, cfg: dict) -> dict[str, Path]:
    return {p.name: p for p in sorted(repos_root.glob(cfg["repos_glob"])) if p.is_dir()}


# ---------- scan ----------

def scan_repo_facts(repo_dir: Path, proto_services: dict[str, int], catalog_repo: dict) -> dict:
    """Scan one repo → {rest_routes, grpc_rpc, commands}. grpc via declared services."""
    facts: dict = {}
    # Only diff metrics the repo actually tracks (avoid noise for grpc-only / bff-only repos).
    if "rest_routes" in catalog_repo:
        facts["rest_routes"] = count_rest_routes(repo_dir)
    declared = catalog_repo.get("grpc_services") or []
    if isinstance(declared, list) and declared and proto_services:
        facts["grpc_rpc"] = sum(proto_services.get(s, 0) for s in declared)
    facts["commands"] = scan_makefile(repo_dir)["commands"]
    return facts


# ---------- diff ----------

def build_change_list(repo: str, scanned: dict, catalog_repo: dict) -> list[dict]:
    """Compare scanned numeric facts vs catalog → list of changes."""
    changes: list[dict] = []
    for metric in ("grpc_rpc", "rest_routes"):
        new = scanned.get(metric)
        if new is None:
            continue
        old = catalog_repo.get(metric)
        if old is None:
            changes.append({"repo": repo, "type": metric, "op": "ADD", "old": None, "new": new})
        elif old != new:
            changes.append({"repo": repo, "type": metric, "op": "UPDATE", "old": old, "new": new})
    return changes


# ---------- render ----------

def render_proposal(task_changes: dict[str, list[dict]], pending: list[str]) -> str:
    lines = ["# kb-sync proposal (weekly batch)", "",
             "> Tick `[x]` các mục muốn ghi vào KB, rồi chạy `/morkit:kb-sync-apply`.",
             f"> Pending tasks: {len(pending)} — {', '.join(pending) or '(none)'}", ""]
    total = 0
    for task in pending:
        changes = task_changes.get(task, [])
        lines.append(f"## Task: {task}")
        if not changes:
            lines.append("- (không phát hiện thay đổi số liệu)")
        for c in changes:
            total += 1
            old = "∅" if c["old"] is None else c["old"]
            lines.append(f"- [ ] **{c['repo']}** {c['type']}: {old} → {c['new']}  ({c['op']})")
        lines.append("")
    lines.append(f"_Total candidate changes: {total}_")
    return "\n".join(lines) + "\n"


# ---------- orchestration ----------

def propose(config_path: str | Path, only_tasks: list[str] | None = None,
            all_repos: bool = False) -> tuple[str, list[str]]:
    cfg, workspace = load_config(config_path)
    # repos_root: nơi chứa 17 repo source. Mặc định = workspace (pack sống cùng code);
    # đặt ".." khi pack là repo RIÊNG, sibling với các repo source (vd 1stop-knowledge).
    repos_root = (workspace / cfg.get("repos_root", ".")).resolve()
    rdirs = repo_dirs(repos_root, cfg)  # dir_name → path (e.g. "1stop-order-service")
    prefix = cfg.get("repo_name_prefix", "")

    def canon(dirname: str) -> str:  # dir name → catalog/fact-sheet name (e.g. "order-service")
        return dirname[len(prefix):] if prefix and dirname.startswith(prefix) else dirname

    catalog = json.loads(resolve_within(workspace, cfg["catalog"]).read_text(encoding="utf-8"))
    cat_by_name = {r["name"]: r for r in catalog.get("repos", [])}
    proto_services = {s.service: s.rpc_count for s in scan_protos([str(repos_root)])} if "proto" in cfg["scanners"] else {}

    def changes_for(dirname: str) -> list[dict]:
        cname = canon(dirname)
        scanned = scan_repo_facts(rdirs[dirname], proto_services, cat_by_name.get(cname, {}))
        return build_change_list(cname, scanned, cat_by_name.get(cname, {}))

    # FULL-SCAN: quét mọi repo vs catalog (không phụ thuộc task) — hợp pack repo-riêng.
    if all_repos:
        acc: list[dict] = []
        for dirname in sorted(rdirs):
            acc.extend(changes_for(dirname))
        return render_proposal({"full-scan": acc}, ["full-scan"]), ["full-scan"]

    # TASK-DRIVEN: scope = union Files: của các task pending (pack sống cùng code).
    ledger = load_ledger(workspace, cfg)
    pending = list_pending(workspace, cfg, ledger)
    if only_tasks:
        pending = [t for t in pending if t in set(only_tasks)]
    task_changes: dict[str, list[dict]] = {}
    for task in pending:
        repos = files_to_repos(files_in_task(resolve_within(workspace, cfg["changes"]) / task), list(rdirs))
        task_changes[task] = [c for repo in sorted(repos) if repo in rdirs for c in changes_for(repo)]
    return render_proposal(task_changes, pending), pending


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="kb-sync: propose KB updates from pending tasks (read-only)")
    ap.add_argument("--config", required=True)
    ap.add_argument("--tasks", help="comma-separated task_ids to limit scope")
    ap.add_argument("--all", action="store_true", dest="all_repos",
                    help="full-scan: quét MỌI repo vs catalog (pack repo-riêng), bỏ qua task")
    ap.add_argument("--output", default=".tmp/kb-sync-proposal.md")
    args = ap.parse_args(argv)
    only = [t.strip() for t in args.tasks.split(",")] if args.tasks else None
    md, pending = propose(args.config, only, all_repos=args.all_repos)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    label = "full-scan" if args.all_repos else f"{len(pending)} pending task(s)"
    print(f"proposal → {out}  ({label})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
