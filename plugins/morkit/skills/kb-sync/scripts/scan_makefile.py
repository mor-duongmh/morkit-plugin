"""Makefile scanner — extract build/test/run/migrate commands per repo.

Conservative: parses `target:` blocks and their recipe lines. Flags known
template-leftover targets (golang-migrate/Postgres) so callers don't trust them.

CLI:
    scan_makefile.py --path 1stop-order-service --output make.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_TARGET = re.compile(r"^([A-Za-z_][A-Za-z0-9_.-]*)\s*:(?!=)")
# recipe lines start with a TAB in real Makefiles
_LEFTOVER_MIGRATE = re.compile(r"postgres://|golang-migrate|migrate\s+-path", re.IGNORECASE)

# target name → canonical role
_ROLE = {
    "dev": "run", "run": "run", "serve": "run", "start": "run",
    "test": "test", "tests": "test",
    "build": "build", "compile": "build",
    "migrate": "migrate", "migrate-up": "migrate", "migrate-apply": "migrate",
}


def parse_targets(text: str) -> dict[str, list[str]]:
    """Return {target: [recipe lines]} from Makefile text."""
    targets: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        m = _TARGET.match(line)
        if m and not line.startswith("\t"):
            current = m.group(1)
            if current == ".PHONY":
                current = None
                continue
            targets.setdefault(current, [])
        elif current and (line.startswith("\t") or line.startswith("    ")):
            stripped = line.strip()
            if stripped:
                targets[current].append(stripped)
        elif not line.strip():
            continue
        else:
            current = None
    return targets


def canonical_commands(targets: dict[str, list[str]]) -> dict[str, str | None]:
    """Map parsed targets → {build,test,run,migrate} recipe strings (or None)."""
    out: dict[str, str | None] = {"build": None, "test": None, "run": None, "migrate": None}
    for name, recipe in targets.items():
        role = _ROLE.get(name.lower())
        if role and out[role] is None and recipe:
            out[role] = " && ".join(recipe)
    return out


def scan_makefile(path: str | Path) -> dict:
    """Scan a repo dir (or Makefile path) → commands + warnings."""
    p = Path(path)
    mk = p if p.is_file() else p / "Makefile"
    if not mk.exists():
        return {"commands": {"build": None, "test": None, "run": None, "migrate": None},
                "targets": [], "warnings": ["no Makefile"]}
    text = mk.read_text(encoding="utf-8", errors="replace")
    targets = parse_targets(text)
    warnings: list[str] = []
    for name, recipe in targets.items():
        if _ROLE.get(name.lower()) == "migrate" and any(_LEFTOVER_MIGRATE.search(l) for l in recipe):
            warnings.append(f"target '{name}' looks like golang-migrate/Postgres leftover (real migration may be Atlas)")
    return {"commands": canonical_commands(targets), "targets": sorted(targets), "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Extract build/test/run/migrate from a repo Makefile")
    ap.add_argument("--path", required=True, help="repo dir or Makefile path")
    ap.add_argument("--output", help="write JSON here; default stdout")
    args = ap.parse_args(argv)
    payload = json.dumps(scan_makefile(args.path), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
