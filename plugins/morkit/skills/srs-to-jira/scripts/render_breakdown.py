"""Write the file the reviewer signs: `tasks.json` + ledger -> `task-breakdown.md`.

Re-running this is safe and expected — after the SRS changes, or after a push. It
carries the reviewer's ticks and wording across, but it resets `status` to draft
whenever the content moved, so an old signature can never cover a new requirement.

CLI:
    render_breakdown.py --tasks tasks.json --map jira-map.json \
        --out task-breakdown.md --project PROJ --base-url https://jira.company.com
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import breakdown_file as bf  # noqa: E402
import diff_tasks as dt  # noqa: E402
import jira_map as jm  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render the approval gate file")
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--map", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--workspace", help="confine --out/--map under this dir")
    args = parser.parse_args(argv)

    out_path = Path(args.out)
    map_path = Path(args.map)
    if args.workspace:
        # Assign the result back: resolve_within RETURNS the safe path. Validating one
        # path and writing to another is not a guard.
        try:
            out_path = jm.resolve_within(args.workspace, out_path)
            map_path = jm.resolve_within(args.workspace, map_path)
        except jm.UnsafePathError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    raw = Path(args.tasks).read_bytes()
    tasks_payload = json.loads(raw)
    tasks_sha256 = hashlib.sha256(raw).hexdigest()

    try:
        book = jm.load_map(map_path)
        if book is not None:
            jm.assert_same_model(book, tasks_payload["meta"])
    except (jm.BindingError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    actions = dt.diff(tasks_payload, book)
    existing = out_path.read_text(encoding="utf-8") if out_path.exists() else None
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        bf.render(actions, tasks_payload, book, args.project, args.base_url,
                  tasks_sha256, existing=existing),
        encoding="utf-8",
    )

    counts: dict[str, int] = {}
    for action in actions:
        counts[action.action] = counts.get(action.action, 0) + 1

    print(
        json.dumps(
            {
                "ok": True,
                "out": str(out_path),
                "status": bf.frontmatter(out_path.read_text(encoding="utf-8")).get("status"),
                "counts": counts,
                "warnings": tasks_payload.get("warnings") or [],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
