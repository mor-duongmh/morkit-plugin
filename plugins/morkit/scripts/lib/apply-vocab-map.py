#!/usr/bin/env python3
"""apply-vocab-map.py — apply codex/vocab-map.yaml swap rules to a single file.

Used by:
  - scripts/sync-codex-fork.sh (Task 4 — bulk regenerate skills-codex/)
  - scripts/check-codex-drift.sh (Task 5 — hash post-swap content)

CLI:
  python3 apply-vocab-map.py --map <vocab-map.yaml> --input <file>
                             [--output <file>]

Semantics:
  - Reads YAML map (must have a top-level `rules:` list).
  - Reads input file as UTF-8 text. If decode fails (binary), exits non-zero
    so the caller can decide to skip / copy verbatim.
  - For each rule in `rules:` (in order):
      * type=literal → str.replace(pattern, replacement)
      * type=regex   → re.sub(pattern, _translate_backrefs(replacement), text)
        where _translate_backrefs converts `$N` (vocab-map convention) to `\\N`
        (Python re convention). Backslashes in replacement are escaped first
        so `$1` doesn't collide with literal backslashes.
  - apply_to globs (e.g. ["*.md"]) are matched against the input file's
    basename via fnmatch. If no globs match, the rule is skipped.
  - The `preserve:` list is NOT consumed here — that's the wrapper's job.

Exit codes:
  0 — success (transformed content written to stdout or --output)
  1 — invalid CLI args
  2 — file/yaml read error
  3 — input is not valid UTF-8 (caller should copy verbatim)
"""

import argparse
import fnmatch
import os
import re
import sys
from typing import Any, Dict, List


def _translate_backrefs(replacement: str) -> str:
    """Convert `$N` backrefs (vocab-map YAML convention) to `\\N` (Python re).

    Steps:
      1. Escape literal backslashes in the user-provided replacement so they
         survive re.sub's own backslash interpretation.
      2. Replace `$N` (N = one or more digits) with `\\N`.

    Note: vocab-map.yaml authors use `$1`, `$2`, etc. — sed/JS convention.
    """
    # Escape any pre-existing backslashes so re.sub treats them literally
    escaped = replacement.replace("\\", "\\\\")
    # $N → \N (regex backref)
    return re.sub(r"\$(\d+)", r"\\\1", escaped)


def _basename_matches_any(basename: str, globs: List[str]) -> bool:
    """True if `basename` matches any glob in `globs` (fnmatch semantics)."""
    if not globs:
        return False
    return any(fnmatch.fnmatch(basename, g) for g in globs)


def _load_map(path: str) -> Dict[str, Any]:
    try:
        import yaml  # PyYAML; documented dep
    except ImportError:
        print(
            "ERROR: PyYAML not installed — install via `pip install pyyaml`",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except FileNotFoundError:
        print(f"ERROR: vocab-map not found: {path}", file=sys.stderr)
        sys.exit(2)
    except yaml.YAMLError as e:
        print(f"ERROR: vocab-map YAML malformed: {e}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(data, dict) or "rules" not in data:
        print(
            "ERROR: vocab-map missing top-level `rules:` array",
            file=sys.stderr,
        )
        sys.exit(2)
    if not isinstance(data["rules"], list):
        print("ERROR: vocab-map `rules` must be a list", file=sys.stderr)
        sys.exit(2)
    return data


def apply_rules(content: str, rules: List[Dict[str, Any]], basename: str) -> str:
    """Apply all matching rules, in order, to `content`. Returns new content."""
    out = content
    for idx, rule in enumerate(rules):
        rtype = rule.get("type")
        pattern = rule.get("pattern")
        replacement = rule.get("replacement", "")
        apply_to = rule.get("apply_to") or []

        if pattern is None or rtype is None:
            print(
                f"ERROR: rule[{idx}] missing required field (type/pattern)",
                file=sys.stderr,
            )
            sys.exit(2)

        if not _basename_matches_any(basename, apply_to):
            continue

        if rtype == "literal":
            out = out.replace(pattern, replacement)
        elif rtype == "regex":
            translated = _translate_backrefs(replacement)
            try:
                out = re.sub(pattern, translated, out)
            except re.error as e:
                print(
                    f"ERROR: rule[{idx}] id={rule.get('id','?')} "
                    f"invalid regex `{pattern}`: {e}",
                    file=sys.stderr,
                )
                sys.exit(2)
        else:
            print(
                f"ERROR: rule[{idx}] unknown type `{rtype}` "
                "(expected literal|regex)",
                file=sys.stderr,
            )
            sys.exit(2)
    return out


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(
        description="Apply vocab-map.yaml swap rules to a single file.",
    )
    p.add_argument("--map", required=True, help="Path to vocab-map.yaml")
    p.add_argument("--input", required=True, help="Path to input file")
    p.add_argument(
        "--output",
        default=None,
        help="Output path (default: stdout)",
    )
    args = p.parse_args(argv)

    data = _load_map(args.map)
    rules = data["rules"]

    if not os.path.isfile(args.input):
        print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
        return 2

    try:
        with open(args.input, "r", encoding="utf-8") as fh:
            content = fh.read()
    except UnicodeDecodeError:
        # Binary file — caller should copy verbatim instead.
        print(
            f"ERROR: input is not valid UTF-8 (binary?): {args.input}",
            file=sys.stderr,
        )
        return 3

    basename = os.path.basename(args.input)
    transformed = apply_rules(content, rules, basename)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(transformed)
    else:
        sys.stdout.write(transformed)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
