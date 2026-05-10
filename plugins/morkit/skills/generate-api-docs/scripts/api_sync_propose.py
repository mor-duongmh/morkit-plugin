"""Step 1 of API sync — generate human-readable proposal from codebase scan.

Compares routes detected via `parse_codebase_routes.scan_routes()` with endpoints
already documented in `docs/api-docs.md` (parsed by header IDs) and emits a markdown
proposal with `[ ]` checkboxes per candidate. **Does NOT modify the existing doc.**

The user reviews, ticks boxes, then runs `api_sync_apply.py` to convert checked
items into a Delta JSON for the standard update flow.

CLI:
    api_sync_propose.py --codebase-paths "src/api,src/routes" \
        --existing-doc docs/api-docs.md \
        --output .tmp/api-sync-proposal.md
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))
sys.path.insert(0, str(_THIS_DIR))

from parse_codebase_routes import EndpointDef, scan_routes  # noqa: E402
from render_api_docs import _path_slug  # noqa: E402

# Match H3 endpoint anchor: ### ENDPOINT-GET-users-by-id
_ENDPOINT_HEADER = re.compile(
    r"^###\s+(ENDPOINT-(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)-[A-Za-z0-9_-]+)\b",
    re.MULTILINE,
)


def parse_existing_endpoints(doc_path: Path) -> set[tuple[str, str]]:
    """Parse api-docs.md for documented endpoints, return set of (METHOD, slug)."""
    if not doc_path.exists():
        return set()
    text = doc_path.read_text(encoding="utf-8")
    found: set[tuple[str, str]] = set()
    for m in _ENDPOINT_HEADER.finditer(text):
        full = m.group(1)  # ENDPOINT-METHOD-slug
        method = m.group(2)
        slug = full[len(f"ENDPOINT-{method}-"):]
        found.add((method.upper(), slug))
    return found


def code_endpoint_key(ep: EndpointDef) -> tuple[str, str]:
    return (ep.method.upper(), _path_slug(ep.path))


def diff_endpoints(
    code_eps: list[EndpointDef], doc_keys: set[tuple[str, str]]
) -> tuple[list[EndpointDef], list[tuple[str, str]]]:
    """Return (to_add, to_deprecate)."""
    code_keys = {code_endpoint_key(ep) for ep in code_eps}
    by_key = {code_endpoint_key(ep): ep for ep in code_eps}

    add_keys = code_keys - doc_keys
    deprecate_keys = doc_keys - code_keys

    to_add = [by_key[k] for k in sorted(add_keys)]
    to_deprecate = sorted(deprecate_keys)
    return to_add, to_deprecate


def _render_add_block(ep: EndpointDef) -> str:
    sec_id = f"ENDPOINT-{ep.method.upper()}-{_path_slug(ep.path)}"
    risk = ""
    notes = (ep.notes or "").lower()
    if "@internal" in notes or "internal" in notes:
        risk = "- Risk: ⚠️ tag `@internal` detected — may be internal-only\n"
    return (
        f"### [ ] ADD {sec_id}\n"
        f"- `{ep.method.upper()} {ep.path}`\n"
        f"- Source: `{ep.file}:{ep.line}` ({ep.framework})\n"
        f"- Auth: {'required' if ep.auth_required else 'public'}\n"
        f"{risk}\n"
    )


def _render_deprecate_block(method: str, slug: str) -> str:
    sec_id = f"ENDPOINT-{method}-{slug}"
    return (
        f"### [ ] DEPRECATE {sec_id}\n"
        f"- Documented but no matching handler found in scanned paths\n"
        f"- Risk: ⚠️ verify before deprecating — may have been moved/renamed\n\n"
    )


def render_proposal(
    code_paths: list[str],
    existing_doc: Path,
    code_eps: list[EndpointDef],
    to_add: list[EndpointDef],
    to_deprecate: list[tuple[str, str]],
) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = []
    lines.append(f"# API Sync Proposal — {ts}\n\n")
    lines.append(f"**Codebase scanned:** {', '.join(code_paths)}\n")
    lines.append(f"**Existing doc:** `{existing_doc}`\n")
    lines.append(f"**Detected endpoints in code:** {len(code_eps)}\n")
    lines.append("**Status:** REVIEW REQUIRED — no doc changes yet\n\n")
    lines.append("---\n\n")

    lines.append(f"## ADD candidates ({len(to_add)})\n\n")
    if not to_add:
        lines.append("_None._\n\n")
    else:
        for ep in to_add:
            lines.append(_render_add_block(ep))
    lines.append("---\n\n")

    lines.append(f"## DEPRECATE candidates ({len(to_deprecate)})\n\n")
    if not to_deprecate:
        lines.append("_None._\n\n")
    else:
        for method, slug in to_deprecate:
            lines.append(_render_deprecate_block(method, slug))
    lines.append("---\n\n")

    lines.append(
        "## How to apply\n\n"
        "1. Edit checkboxes above (`[x]` = apply, `[ ]` = skip)\n"
        "2. Save this file\n"
        "3. Run: `python api_sync_apply.py --proposal {this-file} --output .tmp/api-delta.json`\n"
        "4. Standard update flow consumes the Delta\n"
    )
    return "".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--codebase-paths", required=True, help="Comma-separated")
    p.add_argument("--existing-doc", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    paths = [s.strip() for s in args.codebase_paths.split(",") if s.strip()]
    code_eps = scan_routes(paths)
    doc_keys = parse_existing_endpoints(Path(args.existing_doc))

    to_add, to_deprecate = diff_endpoints(code_eps, doc_keys)

    text = render_proposal(paths, Path(args.existing_doc), code_eps, to_add, to_deprecate)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")

    print(
        f"Proposal: {len(to_add)} ADD / {len(to_deprecate)} DEPRECATE -> {args.output}",
        file=sys.stderr,
    )
    print("Edit checkboxes, then run api_sync_apply.py", file=sys.stderr)

    # Also dump the raw scan for debugging
    if to_add:
        debug_dump = out_path.parent / "api-sync-scan.json"
        import json as _json

        debug_dump.write_text(
            _json.dumps([asdict(ep) for ep in code_eps], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
