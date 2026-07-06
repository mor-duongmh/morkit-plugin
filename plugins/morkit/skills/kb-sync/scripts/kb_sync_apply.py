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

_CHECKED = re.compile(
    r"^\s*-\s*\[x\]\s*\*\*(?P<repo>[^*]+)\*\*\s+(?P<type>\w+):\s*(?P<old>\S+)\s*→\s*(?P<new>\d+)",
    re.MULTILINE,
)
_PROV = re.compile(r"(provenance:\s*extracted\s+)(\d{4}-\d{2}-\d{2})")


def parse_checked(text: str) -> list[dict]:
    out = []
    for m in _CHECKED.finditer(text):
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


def apply(config_path: str | Path, proposal_path: str | Path, today: str) -> dict:
    cfg_path = Path(config_path).resolve()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    workspace = cfg_path.parent.parent
    checked = parse_checked(Path(proposal_path).read_text(encoding="utf-8"))

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

    return {"applied": applied, "repos": touched_repos, "changes": checked}


def main(argv: list[str] | None = None) -> int:
    import datetime
    ap = argparse.ArgumentParser(description="kb-sync: apply checked proposal items to the KB")
    ap.add_argument("--config", required=True)
    ap.add_argument("--proposal", required=True)
    ap.add_argument("--today", default=datetime.date.today().isoformat())
    args = ap.parse_args(argv)
    res = apply(args.config, args.proposal, args.today)
    print(f"applied {res['applied']} change(s) across {len(res['repos'])} repo(s): {', '.join(res['repos'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
