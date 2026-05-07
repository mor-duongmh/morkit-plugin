"""Summarize a docs-hero run — line counts, section counts, missing items.

Reads `docs/srs.md`, `docs/api-docs.md`, `docs/database-design.md` (whichever
exist) and generated `docs/screen-specs/*.md`, then produces a markdown summary
suitable for showing the user or feeding into the docs-hero QA agent.

CLI:
    aggregate_report.py --docs-dir docs/ --output .tmp/docs-report.md
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Anchor patterns per doc type
_ANCHOR_PATTERNS = {
    "srs.md": [
        ("FR", re.compile(r"^###\s+FR-[A-Z0-9_-]+", re.MULTILINE)),
        ("NFR", re.compile(r"^###\s+NFR-[A-Z0-9_-]+", re.MULTILINE)),
        ("SCREEN", re.compile(r"^###\s+SCREEN-[A-Z0-9_-]+", re.MULTILINE)),
        ("DATA", re.compile(r"^DATA-[A-Z0-9_-]+", re.MULTILINE)),
        ("INT", re.compile(r"^###\s+INT-[A-Z0-9_-]+", re.MULTILINE)),
    ],
    "api-docs.md": [
        ("ENDPOINT", re.compile(r"^###\s+ENDPOINT-[A-Z]+-[A-Za-z0-9_-]+", re.MULTILINE)),
        ("ERR", re.compile(r"^###\s+ERR-[A-Za-z0-9_-]+", re.MULTILINE)),
        ("WEBHOOK", re.compile(r"^###\s+WEBHOOK-[A-Za-z0-9_-]+", re.MULTILINE)),
    ],
    "database-design.md": [
        ("TBL", re.compile(r"^###\s+TBL-[A-Za-z0-9_-]+", re.MULTILINE)),
        ("IDX", re.compile(r"^###\s+IDX-[A-Za-z0-9_-]+", re.MULTILINE)),
        ("REL", re.compile(r"^###\s+REL-[A-Za-z0-9_-]+", re.MULTILINE)),
        ("ENUM", re.compile(r"^###\s+ENUM-[A-Za-z0-9_-]+", re.MULTILINE)),
    ],
}


@dataclass
class DocStats:
    name: str
    path: Path
    exists: bool
    line_count: int = 0
    char_count: int = 0
    counts: dict[str, int] = None  # type: ignore[assignment]


def collect_stats(docs_dir: Path) -> list[DocStats]:
    """Inspect the docs directory and return per-file stats."""
    stats: list[DocStats] = []
    for filename, patterns in _ANCHOR_PATTERNS.items():
        path = docs_dir / filename
        ds = DocStats(name=filename, path=path, exists=path.exists(), counts={})
        if path.exists():
            text = path.read_text(encoding="utf-8")
            ds.line_count = text.count("\n") + 1
            ds.char_count = len(text)
            for label, pat in patterns:
                ds.counts[label] = len(pat.findall(text))
        else:
            ds.counts = {label: 0 for label, _ in patterns}
        stats.append(ds)
    return stats


def collect_screen_specs(docs_dir: Path) -> list[Path]:
    spec_dir = docs_dir / "screen-specs"
    if not spec_dir.exists():
        return []
    return sorted(spec_dir.glob("SCREEN-*.md"))


def render_report(docs_dir: Path) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    stats = collect_stats(docs_dir)
    screen_specs = collect_screen_specs(docs_dir)

    out: list[str] = []
    out.append(f"# Docs-Hero Report — {ts}\n\n")
    out.append(f"**Docs directory:** `{docs_dir}`\n\n")

    out.append("## Files\n\n")
    out.append("| File | Status | Lines | Anchors |\n|---|---|---|---|\n")
    for ds in stats:
        if ds.exists:
            anchors = ", ".join(f"{k}={v}" for k, v in ds.counts.items() if v > 0) or "-"
            out.append(f"| `{ds.name}` | ✓ | {ds.line_count} | {anchors} |\n")
        else:
            out.append(f"| `{ds.name}` | ✗ missing | - | - |\n")
    out.append("\n")

    if screen_specs:
        out.append(f"## Screen Specs ({len(screen_specs)})\n\n")
        for sp in screen_specs:
            line_count = sp.read_text(encoding="utf-8").count("\n") + 1
            out.append(f"- `screen-specs/{sp.name}` ({line_count} lines)\n")
        out.append("\n")

    # Quick health check
    out.append("## Health Check\n\n")
    issues: list[str] = []
    for ds in stats:
        if not ds.exists:
            issues.append(f"- `{ds.name}` not generated")
            continue
        if ds.line_count < 30:
            issues.append(f"- `{ds.name}` suspiciously short ({ds.line_count} lines)")
        for label, n in (ds.counts or {}).items():
            # Empty FR / TBL / ENDPOINT typically indicates upstream parser miss
            if label in {"FR", "ENDPOINT", "TBL"} and n == 0:
                issues.append(f"- `{ds.name}` has 0 `{label}` anchors")

    if not issues:
        out.append("All checks passed. Spawn docs-hero QA agent for deeper review.\n")
    else:
        out.extend(issue + "\n" for issue in issues)
        out.append("\nRun docs-hero QA agent for deeper analysis.\n")

    return "".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--docs-dir", default="docs")
    p.add_argument("--output", help="If omitted, prints to stdout")
    args = p.parse_args()

    text = render_report(Path(args.docs_dir))

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(f"Report -> {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
