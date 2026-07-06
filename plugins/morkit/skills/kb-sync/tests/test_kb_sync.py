"""Tests for the kb-sync skill scripts."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from parse_proto import count_services, scan_protos, total_rpc  # noqa: E402
from scan_makefile import canonical_commands, parse_targets, scan_makefile  # noqa: E402


# --- Task 1: parse_proto ---

SINGLE = """
syntax = "proto3";
service AuthService {
  rpc Login(LoginReq) returns (LoginResp);
  rpc Logout(LogoutReq) returns (LogoutResp);
  rpc Introspect(IntrospectReq) returns (IntrospectResp) {
    option (google.api.http) = { post: "/introspect" };
  }
}
"""

MULTI = """
service VendorService {
  rpc GetVendor(Req) returns (Resp);
  rpc UpdateVendor(Req) returns (Resp);
}
service PayoutService {
  rpc CreatePayout(Req) returns (Resp);
}
"""


def test_count_single_service():
    svcs = count_services(SINGLE, "auth.proto")
    assert len(svcs) == 1
    assert svcs[0].service == "AuthService"
    assert svcs[0].rpc_count == 3  # incl. the one with an options block


def test_count_multi_service_file():
    svcs = count_services(MULTI, "vendor.proto")
    counts = {s.service: s.rpc_count for s in svcs}
    assert counts == {"VendorService": 2, "PayoutService": 1}
    assert total_rpc(svcs) == 3


def test_scan_protos_dir_and_total():
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "auth.proto").write_text(SINGLE)
        (Path(td) / "vendor.proto").write_text(MULTI)
        (Path(td) / "notes.txt").write_text("service Fake { rpc X() returns (Y); }")
        svcs = scan_protos([td])
    assert total_rpc(svcs) == 6  # 3 + 3, .txt ignored
    assert {s.proto_file for s in svcs} == {"auth.proto", "vendor.proto"}


# --- Task 2: scan_makefile ---

MAKEFILE = "\n".join([
    ".PHONY: dev test migrate",
    "dev:",
    "\tgo run main.go",
    "test:",
    "\tgo test -v ./... -coverprofile coverage.out",
    "migrate:",
    "\tmigrate -path db -database postgres://u:p@localhost:5432/x up",
    "image:",
    "\tdocker build -t product-service .",
])


def test_parse_targets_and_recipes():
    t = parse_targets(MAKEFILE)
    assert set(t) >= {"dev", "test", "migrate", "image"}
    assert ".PHONY" not in t
    assert t["dev"] == ["go run main.go"]


def test_canonical_commands_maps_dev_to_run():
    cmds = canonical_commands(parse_targets(MAKEFILE))
    assert cmds["run"] == "go run main.go"
    assert "go test" in cmds["test"]


def test_scan_makefile_flags_postgres_leftover():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "Makefile").write_text(MAKEFILE)
        res = scan_makefile(td)
    assert res["commands"]["run"] == "go run main.go"
    assert any("leftover" in w for w in res["warnings"])


# --- Task 7: safe_io (implemented early — Task 3/4 depend on it) ---

import pytest  # noqa: E402
from safe_io import UnsafePathError, resolve_within, run_git, validate_config  # noqa: E402

_GOOD_CFG = {
    "repos_glob": "1stop-*", "catalog": "knowledge/catalog.json",
    "fact_sheets": "knowledge/repos", "ledger": "knowledge/_sync-ledger.json",
    "changes": "knowledge/changes", "scanners": ["proto", "gin_routes"],
}


def test_resolve_within_ok():
    with tempfile.TemporaryDirectory() as td:
        assert resolve_within(td, "knowledge/catalog.json") == (Path(td) / "knowledge/catalog.json").resolve()


def test_resolve_within_blocks_traversal():
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(UnsafePathError):
            resolve_within(td, "../../etc/passwd")
        with pytest.raises(UnsafePathError):
            resolve_within(td, "/etc/passwd")


def test_validate_config_ok():
    assert validate_config(dict(_GOOD_CFG)) == _GOOD_CFG


def test_validate_config_missing_and_wrongtype():
    bad = dict(_GOOD_CFG); del bad["catalog"]
    with pytest.raises(ValueError, match="missing required keys"):
        validate_config(bad)
    bad2 = dict(_GOOD_CFG); bad2["scanners"] = "proto"
    with pytest.raises(ValueError, match="must be list"):
        validate_config(bad2)


def test_run_git_uses_arg_list_no_shell():
    with tempfile.TemporaryDirectory() as td:
        # a malicious "ref" is passed as ONE literal arg → git errors, no shell exec
        cp = run_git(["rev-parse", "; touch pwned"], cwd=td)
        assert cp.returncode != 0
        assert not (Path(td) / "pwned").exists()


# --- Task 3: kb_sync_propose ---

from kb_sync_propose import (  # noqa: E402
    build_change_list, files_in_task, files_to_repos, list_pending, render_proposal,
)


def _mk_pack(td: Path):
    (td / "knowledge/changes/task-a").mkdir(parents=True)
    (td / "knowledge/changes/task-b").mkdir(parents=True)
    (td / "knowledge/changes/_archive").mkdir(parents=True)
    (td / "knowledge/changes/task-a/tasks.md").write_text(
        "## Task 1\n**Files:**\n- Modify: `1stop-order-service/handler/x.go`\n")
    cfg = {"repos_glob": "1stop-*", "catalog": "knowledge/catalog.json",
           "fact_sheets": "knowledge/repos", "ledger": "knowledge/_sync-ledger.json",
           "changes": "knowledge/changes", "scanners": ["proto", "gin_routes"]}
    return cfg


def test_list_pending_excludes_synced_and_archive():
    with tempfile.TemporaryDirectory() as t:
        td = Path(t)
        cfg = _mk_pack(td)
        ledger = {"synced_tasks": {"task-b": "2026-W27"}}
        assert list_pending(td, cfg, ledger) == ["task-a"]  # task-b synced, _archive skipped


def test_files_to_repos_mapping():
    files = ["1stop-order-service/handler/x.go", "docs/readme.md", "1stop-customer-bff/r.go"]
    assert files_to_repos(files, ["1stop-order-service", "1stop-customer-bff"]) == {
        "1stop-order-service", "1stop-customer-bff"}


def test_build_change_list_update_and_add():
    ch = build_change_list("order-service", {"grpc_rpc": 75, "rest_routes": 10},
                           {"grpc_rpc": 73})  # rest_routes missing in catalog → ADD
    kinds = {(c["type"], c["op"], c["old"], c["new"]) for c in ch}
    assert ("grpc_rpc", "UPDATE", 73, 75) in kinds
    assert ("rest_routes", "ADD", None, 10) in kinds


def test_render_proposal_has_checkboxes_no_kb_write():
    md = render_proposal({"task-a": [{"repo": "order-service", "type": "grpc_rpc",
                          "op": "UPDATE", "old": 73, "new": 75}]}, ["task-a"])
    assert "- [ ]" in md and "73 → 75" in md and "task-a" in md


def test_files_in_task_parses_backticked_paths():
    with tempfile.TemporaryDirectory() as t:
        td = Path(t); _mk_pack(td)
        files = files_in_task(td / "knowledge/changes/task-a")
        assert files == ["1stop-order-service/handler/x.go"]


# --- Task 4: kb_sync_apply ---

from kb_sync_apply import (  # noqa: E402
    apply_catalog, parse_checked, refresh_fact_sheet, update_api_rollup,
)

_PROPOSAL = """# proposal
## Task: task-a
- [x] **order-service** grpc_rpc: 73 → 75  (UPDATE)
- [ ] **customer-bff** rest_routes: 100 → 109  (UPDATE)
"""


def test_parse_checked_only_ticked():
    ch = parse_checked(_PROPOSAL)
    assert len(ch) == 1
    assert ch[0] == {"repo": "order-service", "type": "grpc_rpc", "old": 73, "new": 75}


def test_apply_catalog_updates_number_keeps_prose():
    with tempfile.TemporaryDirectory() as t:
        cat = Path(t) / "catalog.json"
        cat.write_text(json.dumps({"repos": [
            {"name": "order-service", "grpc_rpc": 73, "role": "orders"}]}))
        n = apply_catalog(cat, [{"repo": "order-service", "type": "grpc_rpc", "old": 73, "new": 75}])
        data = json.loads(cat.read_text())
        assert n == 1
        assert data["repos"][0]["grpc_rpc"] == 75
        assert data["repos"][0]["role"] == "orders"  # prose untouched


def test_apply_catalog_idempotent():
    with tempfile.TemporaryDirectory() as t:
        cat = Path(t) / "catalog.json"
        cat.write_text(json.dumps({"repos": [{"name": "o", "grpc_rpc": 75}]}))
        ch = [{"repo": "o", "type": "grpc_rpc", "old": 73, "new": 75}]
        assert apply_catalog(cat, ch) == 0  # already 75 → no change


def test_refresh_fact_sheet_number_and_provenance():
    with tempfile.TemporaryDirectory() as t:
        fd = Path(t); (fd / "order-service.md").write_text(
            "---\nprovenance: extracted 2026-06-29 từ proto\n---\n# order — 73 RPC total\n")
        ok = refresh_fact_sheet(fd, "order-service",
                                [{"repo": "order-service", "type": "grpc_rpc", "old": 73, "new": 75}], "2026-07-06")
        txt = (fd / "order-service.md").read_text()
        assert ok and "75 RPC" in txt and "2026-07-06" in txt and "2026-06-29" not in txt


def test_update_api_rollup():
    with tempfile.TemporaryDirectory() as t:
        api = Path(t) / "api.md"; api.write_text("gRPC = 370 RPC total\n")
        update_api_rollup(api, 372)
        assert "372 RPC" in api.read_text()


# --- Task 5: ledger ---

from ledger import (  # noqa: E402
    append_run, compute_drift, load_ledger, pending_tasks, render_sync_log,
)


def test_append_run_maps_tasks_and_sha():
    led = {"sync_runs": [], "synced_tasks": {}}
    append_run(led, "2026-W27", "2026-07-06", "lead:duong", "a1b2c3..d4e5f6",
               ["task-a", "task-b"], [{"repo": "order-service", "type": "grpc_rpc"}])
    assert len(led["sync_runs"]) == 1
    assert led["synced_tasks"] == {"task-a": "2026-W27", "task-b": "2026-W27"}
    assert led["last_sync_sha"] == "d4e5f6"
    assert led["last_sync"] == "2026-07-06"


def test_pending_tasks_after_run():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        for name in ("task-a", "task-b", "_archive"):
            (d / name).mkdir()
        led = {"synced_tasks": {"task-a": "2026-W27"}}
        assert pending_tasks(d, led) == ["task-b"]


def test_compute_drift():
    prov = {"order-service": "2026-06-29", "auth-service": "2026-06-29"}
    commits = {"order-service": "2026-07-05", "auth-service": "2026-06-20"}
    assert compute_drift(prov, commits) == ["order-service"]


def test_render_sync_log_sections():
    led = {"last_sync": "2026-07-06", "synced_tasks": {"task-a": "2026-W27"},
           "sync_runs": [{"run_id": "2026-W27", "date": "2026-07-06",
                          "synced_by": "lead:duong", "tasks": ["task-a"], "changes": [{}]}]}
    md = render_sync_log(led, ["task-c"], ["vendor-service"])
    assert "Đợt sync (theo tuần)" in md and "2026-W27" in md
    assert "Pending backlog" in md and "task-c" in md
    assert "⚠️ **vendor-service**" in md


# --- Task 6: smoke E2E (propose → apply on a mini pack) ---

from kb_sync_propose import propose as _propose  # noqa: E402
from kb_sync_apply import apply as _apply  # noqa: E402


def _mini_pack(root: Path):
    (root / "knowledge/repos").mkdir(parents=True)
    (root / "knowledge/changes/add-x").mkdir(parents=True)
    (root / "1stop-order-service").mkdir(parents=True)
    (root / "1stop-proto/proto").mkdir(parents=True)
    (root / "1stop-proto/proto/order.proto").write_text(
        "service OrderService {\n  rpc A(R) returns (S);\n  rpc B(R) returns (S);\n}\n")
    (root / "knowledge/catalog.json").write_text(json.dumps({"repos": [
        {"name": "1stop-order-service", "grpc_rpc": 1, "grpc_services": ["OrderService"], "role": "orders"}]}))
    (root / "knowledge/repos/1stop-order-service.md").write_text(
        "---\nprovenance: extracted 2026-06-29 từ proto\n---\n# order — 1 RPC\n")
    (root / "knowledge/changes/add-x/tasks.md").write_text(
        "**Files:**\n- Modify: `1stop-order-service/handler/order.go`\n")
    cfg = {"repos_glob": "1stop-*", "catalog": "knowledge/catalog.json",
           "fact_sheets": "knowledge/repos", "ledger": "knowledge/_sync-ledger.json",
           "changes": "knowledge/changes", "scanners": ["proto", "gin_routes"]}
    cfgp = root / "knowledge/.kb-sync.json"
    cfgp.write_text(json.dumps(cfg))
    return cfgp


def test_smoke_propose_then_apply():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        cfgp = _mini_pack(root)

        # PROPOSE — read-only, must NOT touch catalog
        md, pending = _propose(cfgp)
        assert pending == ["add-x"]
        assert "grpc_rpc: 1 → 2" in md
        assert json.loads((root / "knowledge/catalog.json").read_text())["repos"][0]["grpc_rpc"] == 1

        # user ticks the box
        md_ticked = md.replace("- [ ]", "- [x]")
        prop = root / ".tmp/kb-sync-proposal.md"
        prop.parent.mkdir(parents=True, exist_ok=True)
        prop.write_text(md_ticked)

        # APPLY
        res = _apply(cfgp, prop, "2026-07-06", synced_by="lead:test")
        cat = json.loads((root / "knowledge/catalog.json").read_text())
        assert cat["repos"][0]["grpc_rpc"] == 2  # updated
        assert cat["repos"][0]["role"] == "orders"  # prose kept
        fs = (root / "knowledge/repos/1stop-order-service.md").read_text()
        assert "2 RPC" in fs and "2026-07-06" in fs
        assert res["applied"] == 1

        # ledger + SYNC-LOG written; task now marked synced (no longer pending)
        led = json.loads((root / "knowledge/_sync-ledger.json").read_text())
        assert led["synced_tasks"] == {"add-x": res["run_id"]}
        assert len(led["sync_runs"]) == 1 and led["sync_runs"][0]["synced_by"] == "lead:test"
        assert res["pending"] == []
        assert (root / "knowledge/SYNC-LOG.md").exists()

        # idempotent: re-proposing finds nothing pending
        _, pending2 = _propose(cfgp)
        assert pending2 == []


def test_smoke_with_repo_name_prefix():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        (root / "knowledge/repos").mkdir(parents=True)
        (root / "knowledge/changes/add-y").mkdir(parents=True)
        (root / "1stop-order-service").mkdir(parents=True)
        (root / "1stop-proto/proto").mkdir(parents=True)
        (root / "1stop-proto/proto/order.proto").write_text(
            "service OrderService {\n  rpc A(R) returns (S);\n  rpc B(R) returns (S);\n  rpc C(R) returns (S);\n}\n")
        # catalog uses SHORT name; repo dir has 1stop- prefix
        (root / "knowledge/catalog.json").write_text(json.dumps({"repos": [
            {"name": "order-service", "grpc_rpc": 1, "grpc_services": ["OrderService"]}]}))
        (root / "knowledge/changes/add-y/tasks.md").write_text(
            "**Files:**\n- Modify: `1stop-order-service/handler/x.go`\n")
        cfg = {"repos_glob": "1stop-*", "catalog": "knowledge/catalog.json",
               "fact_sheets": "knowledge/repos", "ledger": "knowledge/_sync-ledger.json",
               "changes": "knowledge/changes", "scanners": ["proto"],
               "repo_name_prefix": "1stop-"}
        cfgp = root / "knowledge/.kb-sync.json"; cfgp.write_text(json.dumps(cfg))
        md, pending = _propose(cfgp)
        assert pending == ["add-y"]
        assert "**order-service** grpc_rpc: 1 → 3" in md  # short name, resolved via prefix


# --- Full-scan mode + repos_root + router-scoped REST ---

from kb_sync_propose import count_rest_routes  # noqa: E402


def test_count_rest_routes_scoped_to_router():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "bff"; (d / "router").mkdir(parents=True)
        (d / "router" / "r.go").write_text('r.GET("/a",h)\nr.POST("/b",h)\nx.PUT("/c",h)\n')
        (d / "outside.go").write_text('r.GET("/z",h)\n')  # NGOÀI router/ → không đếm
        assert count_rest_routes(d) == 3


def test_full_scan_all_repos_detects_drift():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        (root / "knowledge/repos").mkdir(parents=True)
        (root / "1stop-proto/proto").mkdir(parents=True)
        (root / "1stop-proto/proto/order.proto").write_text(
            "service OrderService {\n rpc A(R) returns (S);\n rpc B(R) returns (S);\n}\n")
        (root / "1stop-order-service").mkdir()
        (root / "knowledge/catalog.json").write_text(json.dumps({"repos": [
            {"name": "order-service", "grpc_services": ["OrderService"], "grpc_rpc": 1}]}))
        cfg = {"repos_glob": "1stop-*", "repo_name_prefix": "1stop-", "catalog": "knowledge/catalog.json",
               "fact_sheets": "knowledge/repos", "ledger": "knowledge/_sync-ledger.json",
               "changes": "knowledge/changes", "scanners": ["proto"]}
        cfgp = root / "knowledge/.kb-sync.json"; cfgp.write_text(json.dumps(cfg))
        md, groups = _propose(cfgp, all_repos=True)
        assert groups == ["full-scan"]
        assert "**order-service** grpc_rpc: 1 → 2" in md  # full-scan, không cần task


def test_full_scan_repos_root_parent():
    """Pack là repo RIÊNG (sibling các repo source) → repos_root='..'."""
    with tempfile.TemporaryDirectory() as t:
        parent = Path(t)
        pack = parent / "1stop-knowledge"; (pack / "knowledge/repos").mkdir(parents=True)
        (parent / "1stop-proto/proto").mkdir(parents=True)
        (parent / "1stop-proto/proto/o.proto").write_text(
            "service OrderService {\n rpc A(R) returns (S);\n}\n")
        (parent / "1stop-order-service").mkdir()
        (pack / "knowledge/catalog.json").write_text(json.dumps({"repos": [
            {"name": "order-service", "grpc_services": ["OrderService"], "grpc_rpc": 5}]}))
        cfg = {"repos_glob": "1stop-*", "repo_name_prefix": "1stop-", "repos_root": "..",
               "catalog": "knowledge/catalog.json", "fact_sheets": "knowledge/repos",
               "ledger": "knowledge/_sync-ledger.json", "changes": "knowledge/tickets", "scanners": ["proto"]}
        cfgp = pack / "knowledge/.kb-sync.json"; cfgp.write_text(json.dumps(cfg))
        md, _ = _propose(cfgp, all_repos=True)
        assert "**order-service** grpc_rpc: 5 → 1" in md  # source=1 (parent), catalog=5
