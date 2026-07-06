"""Tests for the kb-sync skill scripts."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from parse_proto import count_services, scan_protos, total_rpc  # noqa: E402


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
