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
