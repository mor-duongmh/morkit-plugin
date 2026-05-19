"""Step 2 of API sync — convert checked proposal items into a Delta JSON.

Reads `api-sync-proposal.md` produced by `api_sync_propose.py`, extracts items
whose checkbox is ticked (`[x]` or `[X]`), and writes a Delta JSON the standard
update flow consumes.

CLI:
    api_sync_apply.py --proposal .tmp/api-sync-proposal.md \
        --output .tmp/api-delta.json
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))

from lib.normalized_schema import Change, Delta, save_delta  # noqa: E402

# Match: ### [x] ADD ENDPOINT-GET-users-by-id   (also accepts [X])
_CHECKED_LINE = re.compile(
    r"^###\s+\[(?P<box>[ xX])\]\s+(?P<op>ADD|UPDATE|DEPRECATE)\s+(?P<id>[A-Z][A-Za-z0-9_-]+)\s*$",
    re.MULTILINE,
)

# Optional follow-up bullet "- `METHOD /path`" giving us the URL path payload
_PATH_BULLET = re.compile(
    r"^-\s*`(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(?P<path>[^`]+)`",
    re.MULTILINE,
)


def parse_proposal(text: str) -> list[Change]:
    """Extract checked items as Change records."""
    changes: list[Change] = []
    matches = list(_CHECKED_LINE.finditer(text))

    for i, m in enumerate(matches):
        if m.group("box") not in {"x", "X"}:
            continue

        op_text = m.group("op")
        op = "DEPRECATE" if op_text == "DEPRECATE" else op_text  # ADD/UPDATE/DEPRECATE
        entity_id = m.group("id")

        # Slice the block until the next ### header
        block_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[m.end():block_end]

        payload: dict = {}
        path_m = _PATH_BULLET.search(block)
        if path_m:
            payload["method"] = path_m.group("method").upper()
            payload["path"] = path_m.group("path").strip()

        # Auth bullet
        if re.search(r"^-\s*Auth:\s*required", block, re.MULTILINE | re.IGNORECASE):
            payload["auth_required"] = True
        elif re.search(r"^-\s*Auth:\s*public", block, re.MULTILINE | re.IGNORECASE):
            payload["auth_required"] = False

        entity_type = _entity_type_from_id(entity_id)
        changes.append(
            Change(
                op=op,  # type: ignore[arg-type]
                entity_type=entity_type,  # type: ignore[arg-type]
                entity_id=entity_id,
                payload=payload or None,
                reason="codebase-sync",
            )
        )
    return changes


def _entity_type_from_id(entity_id: str) -> str:
    if entity_id.startswith("ENDPOINT-"):
        return "ENDPOINT"
    if entity_id.startswith("ERR-"):
        return "ERROR_CODE"
    if entity_id.startswith("WEBHOOK-"):
        return "WEBHOOK"
    return "ENDPOINT"  # safe default for API scope


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--proposal", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    proposal_path = Path(args.proposal)
    text = proposal_path.read_text(encoding="utf-8")

    changes = parse_proposal(text)
    if not changes:
        print("No checked items found — nothing to apply.", file=sys.stderr)

    delta = Delta(
        source_type="codebase-sync",
        source_path=str(proposal_path),
        changes=changes,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    save_delta(delta, out_path)

    counts = {"ADD": 0, "UPDATE": 0, "DEPRECATE": 0}
    for c in changes:
        counts[c.op] = counts.get(c.op, 0) + 1
    print(
        f"Applied {len(changes)} changes "
        f"(ADD={counts['ADD']}, UPDATE={counts['UPDATE']}, DEPRECATE={counts['DEPRECATE']}) "
        f"-> {args.output}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
