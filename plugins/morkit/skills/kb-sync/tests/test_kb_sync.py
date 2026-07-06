"""Tests for the kb-sync skill scripts."""
from __future__ import annotations

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
