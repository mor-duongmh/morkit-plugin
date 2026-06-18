"""Load / init / advance / validate the greenfield ``state.json``.

The orchestrator's only stateful code — pure stage bookkeeping, no business
logic. Reuses the stage constants + validator from ``validate_state.py`` (single
source of truth; never re-declares the stage list). Writes are atomic so a kill
mid-write can't corrupt the file (resume guarantee).

Stdlib only, Python 3.9 compatible.

Public API:
    init_state(project, fmt="brse", lang="EN") -> dict
    load(path) -> dict                 # validates; raises ValueError if invalid
    save(state, path) -> None          # atomic
    advance(state) -> dict             # current → done, next → in_progress
    set_stage(state, stage, status, artifact=None) -> dict
    set_gate(state, stage, decision, note="") -> dict
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_state import (  # noqa: E402
    GATED_STAGES,
    STAGES,
    validate_state,
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def init_state(project: str, fmt: str = "brse", lang: str = "EN") -> dict:
    """Create a fresh state with every stage pending and G0 in progress."""
    now = _now()
    stages = {sid: {"status": "pending", "artifact": None, "updated": None} for sid in STAGES}
    stages["G0"]["status"] = "in_progress"
    stages["G0"]["updated"] = now
    for sid in GATED_STAGES:
        stages[sid]["gate"] = {"decision": "pending", "note": ""}
    state = {
        "project": project,
        "stage": "G0",
        "format": fmt,
        "lang": lang,
        "created": now,
        "updated": now,
        "stages": stages,
    }
    errors = validate_state(state)
    if errors:  # pragma: no cover - guards against a future constant typo
        raise ValueError("init produced invalid state: " + "; ".join(errors))
    return state


def load(path: "str | Path") -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_state(data)
    if errors:
        raise ValueError(
            f"invalid state.json at {path}: " + "; ".join(errors)
        )
    return data


def save(state: dict, path: "str | Path") -> None:
    """Atomic write: fsync a uniquely-named temp file, then os.replace.

    Unique (pid-tagged) temp name avoids a deterministic-path clash if two
    writers ever overlap; fsync + os.replace gives crash-atomic durability; the
    finally clause removes the temp on a failed write (no orphan).
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()


def _ensure(state: dict, stage: str) -> dict:
    return state.setdefault("stages", {}).setdefault(
        stage, {"status": "pending", "artifact": None, "updated": None}
    )


def set_stage(state: dict, stage: str, status: str, artifact: "str | None" = None) -> dict:
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}")
    rec = _ensure(state, stage)
    rec["status"] = status
    if artifact is not None:
        rec["artifact"] = artifact
    rec["updated"] = _now()
    state["updated"] = rec["updated"]
    return state


def set_gate(state: dict, stage: str, decision: str, note: str = "") -> dict:
    if stage not in GATED_STAGES:
        raise ValueError(f"stage {stage!r} has no gate (gated: {sorted(GATED_STAGES)})")
    rec = _ensure(state, stage)
    rec["gate"] = {"decision": decision, "note": note}
    rec["updated"] = _now()
    state["updated"] = rec["updated"]
    return state


def advance(state: dict) -> dict:
    """Mark the current stage done; move to the next and mark it in_progress.

    At the last stage (G7) advancing just marks it done (pipeline complete).
    """
    current = state.get("stage")
    if current not in STAGES:
        raise ValueError(f"current stage {current!r} not in {STAGES}")
    set_stage(state, current, "done")
    idx = STAGES.index(current)
    if idx + 1 < len(STAGES):
        nxt = STAGES[idx + 1]
        state["stage"] = nxt
        set_stage(state, nxt, "in_progress")
    return state


def _cmd_init(args) -> int:
    state = init_state(args.project, args.format, args.lang)
    save(state, args.state)
    print(f"initialized {args.state} (project={args.project}, stage=G0)", file=sys.stderr)
    return 0


def _cmd_show(args) -> int:
    state = load(args.state)
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


def _cmd_validate(args) -> int:
    try:
        load(args.state)
    except ValueError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print("OK: state.json valid", file=sys.stderr)
    return 0


def _cmd_advance(args) -> int:
    state = load(args.state)
    advance(state)
    save(state, args.state)
    print(f"advanced → stage={state['stage']}", file=sys.stderr)
    return 0


def _cmd_set_stage(args) -> int:
    state = load(args.state)
    set_stage(state, args.stage, args.status, args.artifact)
    save(state, args.state)
    print(f"{args.stage} → {args.status}", file=sys.stderr)
    return 0


def _cmd_set_gate(args) -> int:
    state = load(args.state)
    set_gate(state, args.stage, args.decision, args.note or "")
    save(state, args.state)
    print(f"{args.stage} gate → {args.decision}", file=sys.stderr)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init")
    pi.add_argument("--state", required=True)
    pi.add_argument("--project", required=True)
    pi.add_argument("--format", default="brse", choices=["brse", "agile"])
    pi.add_argument("--lang", default="EN", choices=["JP", "EN", "VN"])
    pi.set_defaults(func=_cmd_init)

    for name, fn in (("show", _cmd_show), ("validate", _cmd_validate), ("advance", _cmd_advance)):
        sp = sub.add_parser(name)
        sp.add_argument("--state", required=True)
        sp.set_defaults(func=fn)

    ps = sub.add_parser("set-stage")
    ps.add_argument("--state", required=True)
    ps.add_argument("--stage", required=True, choices=STAGES)
    ps.add_argument("--status", required=True, choices=["pending", "in_progress", "done", "blocked"])
    ps.add_argument("--artifact")
    ps.set_defaults(func=_cmd_set_stage)

    pg = sub.add_parser("set-gate")
    pg.add_argument("--state", required=True)
    pg.add_argument("--stage", required=True, choices=sorted(GATED_STAGES))
    pg.add_argument("--decision", required=True, choices=["pending", "proceed", "adjust", "force-close"])
    pg.add_argument("--note")
    pg.set_defaults(func=_cmd_set_gate)

    args = p.parse_args()
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"ERROR: state file not found: {exc.filename or exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: malformed JSON in state file: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
