#!/usr/bin/env python3
"""Load greenfield gate checklists (front-matter + item IDs).

Single source of truth for the per-gate *required* (must-pass) subset that the
orchestrator renders into each human gate and that `state_manager.advance`
enforces. Lives next to `state_manager.py`; the canonical checklist markdown
lives in `../references/gate-checklists/`.

The venv has no PyYAML (Python 3.9), so front-matter is parsed by a tiny,
format-restricted parser — NOT general YAML. Supported value shapes (one per
line): scalar (optionally quoted), inline list `[a, b]`, inline dict
`{k: v, k2: null}`. That is all the checklists use; keep it that way.

Checklist authoring contract (verified by `load`):
  - YAML-ish front-matter between leading `---` fences.
  - `gate` matches the filename prefix (e.g. `g6-...md` -> `G6`).
  - every item line: `- [ ] [GX-ID] **Title** — ...`
  - every id in `required` resolves to an item id (no dangling).
  - `decisions` values are state.json gate enums (proceed|adjust|force-close)
    or null.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VALID_DECISIONS = {"proceed", "adjust", "force-close", None}
GATES = {"G2", "G3", "G4", "G6"}

# `- [ ] [G6-A3] **Title** ...`  (checkbox state ignored; id captured, title parsed below).
# Bold title is optional so a well-formed `- [ ] [ID] ...` item is never silently dropped.
_ITEM_RE = re.compile(r"^- \[[ xX]\]\s+\[(?P<id>[A-Z0-9-]+)\]\s+(?P<rest>.+)$")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _parse_scalar(v: str):
    v = v.strip()
    if v == "" or v.lower() == "null" or v.lower() == "~":
        return None
    return _strip_quotes(v)


def _split_top(s: str) -> "list[str]":
    """Split a comma list, ignoring commas inside quoted runs (fail-safe, not nested)."""
    parts: "list[str]" = []
    buf: "list[str]" = []
    quote = None
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == ",":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip() != ""]


def _parse_value(v: str):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        return [_strip_quotes(x) for x in _split_top(v[1:-1])]
    if v.startswith("{") and v.endswith("}"):
        out = {}
        for pair in _split_top(v[1:-1]):
            if ":" not in pair:
                raise ValueError(f"bad dict entry in front-matter: {pair!r}")
            k, _, val = pair.partition(":")
            out[k.strip()] = _parse_scalar(val)
        return out
    return _parse_scalar(v)


def parse_front_matter(text: str) -> "tuple[dict, str]":
    """Return (front_matter_dict, body_markdown)."""
    if not text.startswith("---"):
        raise ValueError("checklist missing front-matter (no leading '---')")
    parts = text.split("\n")
    if parts[0].strip() != "---":
        raise ValueError("front-matter must open with a lone '---' line")
    end = None
    for i in range(1, len(parts)):
        if parts[i].strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("front-matter not terminated by '---'")
    fm: dict = {}
    for line in parts[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"bad front-matter line: {line!r}")
        key, _, val = line.partition(":")
        fm[key.strip()] = _parse_value(val)
    body = "\n".join(parts[end + 1:])
    return fm, body


def parse_items(body: str) -> "list[dict]":
    items = []
    for line in body.split("\n"):
        m = _ITEM_RE.match(line)
        if not m:
            continue
        rest = m.group("rest").strip()
        bold = _BOLD_RE.search(rest)
        title = bold.group(1).strip() if bold else rest
        items.append({"id": m.group("id"), "title": title})
    return items


def _gate_from_filename(path: Path) -> str:
    m = re.match(r"g(\d+)-", path.name)
    return f"G{m.group(1)}" if m else ""


def load(path: "str | Path") -> dict:
    """Parse + validate one checklist file into a structured dict."""
    path = Path(path)
    fm, body = parse_front_matter(path.read_text(encoding="utf-8"))

    gate = fm.get("gate")
    if gate not in GATES:
        raise ValueError(f"{path.name}: front-matter gate {gate!r} not in {sorted(GATES)}")
    expected = _gate_from_filename(path)
    if expected and gate != expected:
        raise ValueError(f"{path.name}: gate {gate!r} != filename gate {expected!r}")

    items = parse_items(body)
    ids = [it["id"] for it in items]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValueError(f"{path.name}: duplicate item ids {dupes}")
    id_set = set(ids)

    required = fm.get("required") or []
    if not isinstance(required, list):
        raise ValueError(f"{path.name}: required must be a list, got {required!r}")
    dangling = [r for r in required if r not in id_set]
    if dangling:
        raise ValueError(f"{path.name}: required ids not found in body: {dangling}")

    decisions = fm.get("decisions") or {}
    bad = [v for v in decisions.values() if v not in VALID_DECISIONS]
    if bad:
        raise ValueError(f"{path.name}: invalid decision enum(s): {bad}")

    for it in items:
        it["required"] = it["id"] in required

    return {
        "gate": gate,
        "role": fm.get("role"),
        "artifact": fm.get("artifact") or [],
        "decisions": decisions,
        "required": required,
        "items": items,
    }


def default_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "gate-checklists"


def find_gate(gate: str, dir_: "str | Path | None" = None) -> Path:
    base = Path(dir_) if dir_ else default_dir()
    for p in sorted(base.glob("g*-*.md")):
        if _gate_from_filename(p).upper() == gate.upper():
            return p
    raise FileNotFoundError(f"no checklist for gate {gate} in {base}")


def _cmd_show(args) -> int:
    path = Path(args.path) if args.path else find_gate(args.gate, args.dir)
    data = load(path)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def main(argv=None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Load greenfield gate checklist.")
    sub = p.add_subparsers(dest="cmd", required=True)
    ps = sub.add_parser("show", help="Print parsed checklist as JSON.")
    g = ps.add_mutually_exclusive_group(required=True)
    g.add_argument("--gate", choices=sorted(GATES))
    g.add_argument("--path")
    ps.add_argument("--dir", help="Override checklist dir (default: skill references).")
    ps.set_defaults(func=_cmd_show)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, FileNotFoundError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
