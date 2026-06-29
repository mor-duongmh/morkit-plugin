#!/usr/bin/env python3
"""Workspace tickable checklist copy + confirmed-required reader (file-based gate).

The greenfield gate is file-based: instead of rendering the required subset as
`AskUserQuestion` options (capped at 4, silently truncated past that), the
orchestrator writes a *tickable copy* of the canonical checklist into the run
workspace. The reviewer opens it, ticks `- [x]` for items they confirm, saves.
On Approve, `read_confirmed` reports which *required* ids are ticked; the gate
feeds those to `state_manager.set_gate(confirmed=...)` and `advance` enforces.

Concern split: `checklist_loader` parses; this module does workspace I/O.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import checklist_loader as cl

# Match a checked item box at line start: `- [x] ...` / `- [X] ...`.
_CHECKED_BOX_RE = re.compile(r"^(- \[)[xX](\])", re.MULTILINE)


def _reset_checkboxes(text: str) -> str:
    """Turn every `- [x]`/`- [X]` item box into an unchecked `- [ ]`."""
    return _CHECKED_BOX_RE.sub(r"\1 \2", text)


def write_workspace_copy(canonical_path: "str | Path", dest_path: "str | Path") -> Path:
    """Copy canonical checklist → workspace, resetting all boxes to unchecked.

    Idempotent-safe: if `dest_path` already exists it is left untouched (preserves
    the reviewer's ticks across gate re-entry). Returns the dest path either way.
    """
    dest = Path(dest_path)
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = Path(canonical_path).read_text(encoding="utf-8")
    dest.write_text(_reset_checkboxes(text), encoding="utf-8")
    return dest


def read_confirmed(workspace_copy_path: "str | Path") -> "list[str]":
    """Return the required ids that are ticked in the workspace copy.

    Intersection of {required} and {checked}. Non-required ticks are ignored;
    unticked required ids are excluded (so `advance` blocks until the reviewer
    ticks every must-pass item).
    """
    data = cl.load(workspace_copy_path)
    return [it["id"] for it in data["items"] if it.get("required") and it.get("checked")]


def _cmd_write(args) -> int:
    if args.gate:
        canonical = cl.find_gate(args.gate)
    elif args.canonical:
        canonical = args.canonical
    else:
        raise ValueError("write needs --gate or --canonical")
    out = write_workspace_copy(canonical, args.dest)
    print(str(out))
    return 0


def _cmd_confirmed(args) -> int:
    print(json.dumps(read_confirmed(args.path), ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Workspace gate checklist copy / confirmed reader.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pw = sub.add_parser("write", help="Write a tickable workspace copy (reset boxes).")
    pwsrc = pw.add_mutually_exclusive_group(required=True)
    pwsrc.add_argument("--gate", choices=sorted(cl.GATES), help="Resolve canonical by gate id.")
    pwsrc.add_argument("--canonical", help="Explicit canonical checklist .md path.")
    pw.add_argument("--dest", required=True, help="Workspace copy destination path.")
    pw.set_defaults(func=_cmd_write)

    pc = sub.add_parser("confirmed", help="Print ticked required ids as a JSON list.")
    pc.add_argument("--path", required=True, help="Workspace copy path.")
    pc.set_defaults(func=_cmd_confirmed)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, FileNotFoundError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
