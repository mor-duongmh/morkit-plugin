"""Step 2 of codebase-summary sync — convert checked proposal items to Delta JSON.

CLI:
    codebase_summary_sync_apply.py --proposal .tmp/codebase-summary-sync-proposal.md \
        --output .tmp/codebase-summary-delta.json
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))

from lib.normalized_schema import Change, Delta, save_delta  # noqa: E402

_CHECKED_LINE = re.compile(
    r"^###\s+\[(?P<box>[ xX])\]\s+(?P<op>ADD|UPDATE|DEPRECATE)\s+"
    r"(?P<id>(?:PKG|TCH|MOD)-[A-Za-z0-9_-]+)\s*$",
    re.MULTILINE,
)
_NAME_BULLET = re.compile(r"^-\s*Name:\s*`([^`]+)`", re.MULTILINE)
_PATH_BULLET = re.compile(r"^-\s*Path:\s*`([^`]+)`", re.MULTILINE)
_LANG_BULLET = re.compile(r"^-\s*Language:\s*([A-Za-z0-9+#.\- ]+)", re.MULTILINE)


def parse_proposal(text: str) -> list[Change]:
    changes: list[Change] = []
    matches = list(_CHECKED_LINE.finditer(text))

    for i, m in enumerate(matches):
        if m.group("box") not in {"x", "X"}:
            continue
        op = m.group("op")
        entity_id = m.group("id")
        entity_type = entity_id.split("-", 1)[0]  # PKG / TCH / MOD

        block_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[m.end():block_end]

        payload: dict = {}
        nm = _NAME_BULLET.search(block)
        if nm:
            payload["name"] = nm.group(1)
        pm = _PATH_BULLET.search(block)
        if pm:
            payload["path"] = pm.group(1)
        lm = _LANG_BULLET.search(block)
        if lm:
            payload["language"] = lm.group(1).strip()

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
