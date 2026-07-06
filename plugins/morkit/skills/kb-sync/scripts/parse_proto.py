"""gRPC .proto scanner — count services and RPCs per proto file.

Ground-truth source for a knowledge pack's gRPC surface. Reused by kb-sync and
usable by morkit's api-docs sync. Pure stdlib, conservative regex + brace matching.

CLI:
    parse_proto.py --paths "1stop-proto/proto" --output proto.json
    # stdout/file JSON: [{"proto_file": "...", "service": "...", "rpc_count": N}]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

_SERVICE_OPEN = re.compile(r"\bservice\s+(\w+)\s*\{")
_RPC = re.compile(r"^\s*rpc\s+\w+\s*\(", re.MULTILINE)


@dataclass
class ProtoService:
    proto_file: str
    service: str
    rpc_count: int


def _service_body(text: str, open_brace_idx: int) -> str:
    """Return the body text between the service's `{` and its matching `}`."""
    depth = 0
    for i in range(open_brace_idx, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_idx + 1 : i]
    return text[open_brace_idx + 1 :]  # unbalanced — take rest


def count_services(text: str, proto_file: str = "") -> list[ProtoService]:
    """Parse one .proto's text → per-service RPC counts (brace-matched)."""
    out: list[ProtoService] = []
    for m in _SERVICE_OPEN.finditer(text):
        name = m.group(1)
        brace_idx = m.end() - 1  # index of the `{`
        body = _service_body(text, brace_idx)
        out.append(ProtoService(proto_file, name, len(_RPC.findall(body))))
    return out


def scan_protos(paths: list[str | Path]) -> list[ProtoService]:
    """Scan .proto files under given paths → sorted list of ProtoService."""
    results: list[ProtoService] = []
    for p in paths:
        base = Path(p)
        files = [base] if base.is_file() else sorted(base.rglob("*.proto"))
        for f in files:
            if f.suffix != ".proto":
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            results.extend(count_services(text, f.name))
    return sorted(results, key=lambda s: (s.proto_file, s.service))


def total_rpc(services: list[ProtoService]) -> int:
    return sum(s.rpc_count for s in services)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Count gRPC services/RPCs from .proto files")
    ap.add_argument("--paths", required=True, help="comma-separated dirs/files")
    ap.add_argument("--output", help="write JSON here; default stdout")
    args = ap.parse_args(argv)

    paths = [p.strip() for p in args.paths.split(",") if p.strip()]
    services = scan_protos(paths)
    payload = json.dumps([asdict(s) for s in services], ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
