"""Scan a codebase for existing MADR-style ADR files → seed ADR entities.

Unlike the other scanners, this one is a **one-shot import helper**, not
part of a sync loop (design-guidelines doesn't support sync). Useful at
init time to pull existing `docs/adr/*.md` content into the ProjectModel
so the rendered `design-guidelines.md` §3 isn't blank.

Searches:
    docs/adr/*.md
    docs/decisions/*.md
    architecture/decisions/*.md
    adr/*.md
    decisions/*.md

Recognized MADR sections (case-insensitive):
    Status / Date / Context / Decision / Consequences / Superseded by

Output: list of `ADRDef` dicts saved as JSON.

CLI:
    parse_codebase_adrs.py --paths "." --output adrs.json

Public API:
    scan_adrs(paths) -> list[dict]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

_ADR_DIRS = (
    "docs/adr",
    "docs/decisions",
    "architecture/decisions",
    "adr",
    "decisions",
)

_DEFAULT_IGNORES = {".git", "node_modules", ".venv", "dist", "build"}

# ADR-001 / 0001 / 001-title.md
_ID_PATTERN = re.compile(r"^(?:ADR-?)?(\d{1,4})", re.IGNORECASE)

# `# ADR-001: Title` or `# 001 — Title` or `# Title`
_TITLE_LINE = re.compile(r"^#\s+(?P<title>.+?)\s*$", re.MULTILINE)
_ADR_PREFIX = re.compile(r"^(?:ADR-?\d+|\d+)\s*[:\-—–]\s*", re.IGNORECASE)

# Section headers (## or ###) — body runs until next heading of any level
_SECTION = lambda name: re.compile(  # noqa: E731
    rf"^#{{2,3}}\s+{re.escape(name)}\s*\n(?P<body>.*?)(?=^#{{1,6}}\s|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)
_STATUS_RE = _SECTION("Status")
_DATE_RE = _SECTION("Date")
_CONTEXT_RE = _SECTION("Context")
_DECISION_RE = _SECTION("Decision")
_CONSEQUENCES_RE = _SECTION("Consequences")

# Inline `Status: accepted` style (when there's no `## Status` section)
_STATUS_INLINE = re.compile(r"^\s*Status\s*:\s*(?P<v>.+?)\s*$", re.MULTILINE | re.IGNORECASE)
_DATE_INLINE = re.compile(r"^\s*Date\s*:\s*(?P<v>.+?)\s*$", re.MULTILINE | re.IGNORECASE)
_SUPERSEDED_INLINE = re.compile(
    r"^\s*Superseded\s+by\s*:\s*(?P<v>.+?)\s*$", re.MULTILINE | re.IGNORECASE
)

_STATUS_NORMALIZE = {
    "proposed": "proposed",
    "draft": "proposed",
    "accepted": "accepted",
    "approved": "accepted",
    "deprecated": "deprecated",
    "superseded": "superseded",
}


@dataclass
class ADRDef:
    id: str  # ADR-001
    title: str
    status: str = "accepted"
    date: str | None = None
    context: str = ""
    decision: str = ""
    consequences: str = ""
    superseded_by: str | None = None
    source_path: str = ""


def _is_ignored(p: Path, ignore: set[str]) -> bool:
    return any(part in ignore for part in p.parts)


def _id_from_filename(filename: str) -> str | None:
    m = _ID_PATTERN.match(filename)
    if not m:
        return None
    return f"ADR-{int(m.group(1)):03d}"


def _strip_id_prefix(title: str) -> str:
    return _ADR_PREFIX.sub("", title).strip()


def _section_or_inline(text: str, section_re: re.Pattern, inline_re: re.Pattern | None = None) -> str:
    m = section_re.search(text)
    if m:
        return m.group("body").strip()
    if inline_re:
        m = inline_re.search(text)
        if m:
            return m.group("v").strip()
    return ""


def _normalize_status(raw: str) -> str:
    if not raw:
        return "accepted"
    head = re.split(r"\s|,|\(|—|–|-", raw.strip(), maxsplit=1)[0].lower()
    return _STATUS_NORMALIZE.get(head, "accepted")


def parse_adr_file(path: Path, root: Path) -> ADRDef | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    aid = _id_from_filename(path.stem)
    if aid is None:
        return None

    # Title from first H1
    title = path.stem
    tm = _TITLE_LINE.search(text)
    if tm:
        title = _strip_id_prefix(tm.group("title")) or title

    status_raw = _section_or_inline(text, _STATUS_RE, _STATUS_INLINE)
    date_raw = _section_or_inline(text, _DATE_RE, _DATE_INLINE)
    context = _section_or_inline(text, _CONTEXT_RE)
    decision = _section_or_inline(text, _DECISION_RE)
    consequences = _section_or_inline(text, _CONSEQUENCES_RE)
    superseded_raw = ""
    sm = _SUPERSEDED_INLINE.search(text)
    if sm:
        superseded_raw = sm.group("v").strip()

    return ADRDef(
        id=aid,
        title=title,
        status=_normalize_status(status_raw),
        date=date_raw or None,
        context=context,
        decision=decision,
        consequences=consequences,
        superseded_by=(superseded_raw or None),
        source_path=str(path.relative_to(root)),
    )


def scan_adrs(paths: list[str], ignore: set[str] | None = None) -> list[ADRDef]:
    ignore_set = ignore or _DEFAULT_IGNORES
    out: dict[str, ADRDef] = {}

    for raw in paths:
        root = Path(raw).resolve()
        if not root.is_dir():
            log.warning("not a directory: %s", root)
            continue

        for adr_dir in _ADR_DIRS:
            d = root / adr_dir
            if not d.is_dir():
                continue
            for f in sorted(d.glob("*.md")):
                if _is_ignored(f, ignore_set) or not f.is_file():
                    continue
                # Skip README files
                if f.stem.lower() in {"readme", "index", "template"}:
                    continue
                adr = parse_adr_file(f, root)
                if adr and adr.id not in out:
                    out[adr.id] = adr

    return sorted(out.values(), key=lambda a: a.id)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--paths", required=True, help="Comma-separated repo roots")
    p.add_argument("--output", required=True, help="JSON output file")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    paths = [s.strip() for s in args.paths.split(",") if s.strip()]
    adrs = scan_adrs(paths)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps([asdict(a) for a in adrs], indent=2), encoding="utf-8"
    )
    print(f"Detected {len(adrs)} ADRs -> {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
