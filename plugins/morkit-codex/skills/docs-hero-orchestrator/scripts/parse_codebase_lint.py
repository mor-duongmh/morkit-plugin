"""Scan a codebase for lint / format / commit configs → feeds code-standards doc.

Detected (paths only — `extends` is recorded verbatim, NOT resolved, to avoid
needing dependency installs at scan time):

    JS/TS lint:       .eslintrc(.json|.js|.cjs|.yaml|.yml), eslint.config.*
    JS/TS format:     .prettierrc(.json|.js|.yaml|.yml), prettier.config.*
    JS/TS legacy:     tslint.json
    Python lint:      pyproject.toml ([tool.ruff], [tool.flake8]), .flake8, setup.cfg
    Python format:    pyproject.toml ([tool.black], [tool.isort])
    Editor:           .editorconfig
    Go:               .golangci.yml / .golangci.yaml
    Rust:             rustfmt.toml, clippy.toml
    Ruby:             .rubocop.yml
    Commit:           .commitlintrc(.json|.js|.yaml), commitlint.config.*,
                      .husky/commit-msg, CONTRIBUTING.md (Conventional-Commits hint)

Output: list of `LintConfigDef` dicts saved as JSON.

CLI:
    parse_codebase_lint.py --paths "." --output lint.json

Public API:
    scan_lint_configs(paths) -> list[dict]
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

_DEFAULT_IGNORES = {
    ".git", "node_modules", "dist", "build", ".next", ".venv",
    "__pycache__", "vendor", "target",
}

# (tool, glob, [optional inner-key for embedded configs like pyproject.toml])
_FILE_PATTERNS: list[tuple[str, str]] = [
    ("eslint", ".eslintrc"),
    ("eslint", ".eslintrc.json"),
    ("eslint", ".eslintrc.js"),
    ("eslint", ".eslintrc.cjs"),
    ("eslint", ".eslintrc.yaml"),
    ("eslint", ".eslintrc.yml"),
    ("eslint", "eslint.config.js"),
    ("eslint", "eslint.config.cjs"),
    ("eslint", "eslint.config.mjs"),
    ("prettier", ".prettierrc"),
    ("prettier", ".prettierrc.json"),
    ("prettier", ".prettierrc.js"),
    ("prettier", ".prettierrc.yaml"),
    ("prettier", ".prettierrc.yml"),
    ("prettier", "prettier.config.js"),
    ("tslint", "tslint.json"),
    ("flake8", ".flake8"),
    ("flake8", "setup.cfg"),
    ("editorconfig", ".editorconfig"),
    ("golangci-lint", ".golangci.yml"),
    ("golangci-lint", ".golangci.yaml"),
    ("rustfmt", "rustfmt.toml"),
    ("clippy", "clippy.toml"),
    ("rubocop", ".rubocop.yml"),
    ("commitlint", ".commitlintrc"),
    ("commitlint", ".commitlintrc.json"),
    ("commitlint", ".commitlintrc.js"),
    ("commitlint", ".commitlintrc.yaml"),
    ("commitlint", "commitlint.config.js"),
    ("commitlint", "commitlint.config.cjs"),
    ("husky", ".husky/commit-msg"),
    ("husky", ".husky/pre-commit"),
]

# pyproject.toml: which `[tool.X]` sections to record as separate entries
_PYPROJECT_TOOLS = ("ruff", "black", "isort", "mypy", "pytest")

_EXTENDS_PATTERNS = [
    re.compile(r'"?extends"?\s*:\s*\[([^\]]*)\]', re.IGNORECASE),  # JSON array
    re.compile(r'"?extends"?\s*:\s*"([^"]+)"', re.IGNORECASE),       # JSON string
    re.compile(r"extends:\s*\n((?:\s*-\s*.+\n)+)", re.IGNORECASE),  # YAML list
    re.compile(r'extends:\s*"?([^\s\"]+)"?\n', re.IGNORECASE),       # YAML scalar
]

_CONVENTIONAL_HINT = re.compile(
    r"\b(?:conventional[\- ]commits|@commitlint/config-conventional|"
    r"feat\([a-z0-9_-]+\)\s*:|fix\([a-z0-9_-]+\)\s*:)\b",
    re.IGNORECASE,
)


@dataclass
class LintConfigDef:
    """One lint/format/commit config detected."""

    id: str  # LNT-<slug>
    tool: str
    config_path: str
    extends: list[str] = field(default_factory=list)
    rules_summary: dict[str, str] = field(default_factory=dict)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _is_ignored(p: Path, ignore: set[str]) -> bool:
    return any(part in ignore for part in p.parts)


def _extract_extends(text: str) -> list[str]:
    """Best-effort extraction of `extends` values from JSON / YAML configs."""
    out: list[str] = []
    for pat in _EXTENDS_PATTERNS:
        for m in pat.finditer(text):
            raw = m.group(1)
            if "\n" in raw:
                # YAML list block: split by lines, strip leading "- "
                for line in raw.splitlines():
                    line = line.strip()
                    if line.startswith("-"):
                        v = line.lstrip("-").strip().strip('"').strip("'")
                        if v:
                            out.append(v)
            else:
                # JSON array or scalar
                for v in raw.split(","):
                    v = v.strip().strip('"').strip("'")
                    if v:
                        out.append(v)
    # de-dup, preserve order
    seen: set[str] = set()
    return [v for v in out if not (v in seen or seen.add(v))]


def _scan_pyproject(path: Path, root: Path) -> list[LintConfigDef]:
    """Each `[tool.X]` section → one LintConfigDef."""
    out: list[LintConfigDef] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    rel = str(path.relative_to(root))
    for tool in _PYPROJECT_TOOLS:
        if re.search(rf"^\[tool\.{re.escape(tool)}\]", text, re.MULTILINE):
            out.append(
                LintConfigDef(
                    id=f"LNT-{_slug(tool)}",
                    tool=tool,
                    config_path=rel,
                )
            )
    return out


def _scan_contributing(path: Path, root: Path) -> LintConfigDef | None:
    """If CONTRIBUTING.md mentions Conventional Commits → record as commit policy hint."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not _CONVENTIONAL_HINT.search(text):
        return None
    return LintConfigDef(
        id="LNT-contributing-cc",
        tool="conventional-commits-hint",
        config_path=str(path.relative_to(root)),
    )


def scan_lint_configs(paths: list[str], ignore: set[str] | None = None) -> list[LintConfigDef]:
    """Scan one or more roots; return merged LintConfig list."""
    ignore_set = ignore or _DEFAULT_IGNORES
    out: dict[str, LintConfigDef] = {}

    for raw in paths:
        root = Path(raw).resolve()
        if not root.is_dir():
            log.warning("not a directory, skipping: %s", root)
            continue

        # Standard file patterns (match anywhere under root)
        for tool, name in _FILE_PATTERNS:
            for hit in root.rglob(name):
                if _is_ignored(hit, ignore_set) or not hit.is_file():
                    continue
                rel = str(hit.relative_to(root))
                lid = f"LNT-{_slug(tool)}-{_slug(rel)}"
                if lid in out:
                    continue
                cfg = LintConfigDef(id=lid, tool=tool, config_path=rel)
                # Only attempt extends extraction on text-readable configs
                if name not in (".husky/commit-msg", ".husky/pre-commit"):
                    try:
                        text = hit.read_text(encoding="utf-8", errors="replace")
                        cfg.extends = _extract_extends(text)
                    except OSError:
                        pass
                out[lid] = cfg

        # pyproject.toml sub-sections
        for hit in root.rglob("pyproject.toml"):
            if _is_ignored(hit, ignore_set) or not hit.is_file():
                continue
            for cfg in _scan_pyproject(hit, root):
                if cfg.id not in out:
                    out[cfg.id] = cfg

        # CONTRIBUTING.md hint
        for hit in root.rglob("CONTRIBUTING.md"):
            if _is_ignored(hit, ignore_set) or not hit.is_file():
                continue
            cfg = _scan_contributing(hit, root)
            if cfg and cfg.id not in out:
                out[cfg.id] = cfg

    return sorted(out.values(), key=lambda c: c.id)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--paths", required=True, help="Comma-separated repo roots")
    p.add_argument("--output", required=True, help="JSON output file")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    paths = [s.strip() for s in args.paths.split(",") if s.strip()]
    configs = scan_lint_configs(paths)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps([asdict(c) for c in configs], indent=2), encoding="utf-8"
    )
    print(f"Detected {len(configs)} lint configs -> {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
