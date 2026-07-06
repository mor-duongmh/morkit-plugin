"""Safety helpers for kb-sync: path-traversal guard, config validation, safe git.

All KB writes must go through `resolve_within` so a malicious `.kb-sync.json`
or `task_id` cannot escape the declared knowledge base directories.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REQUIRED_KEYS: dict[str, type] = {
    "repos_glob": str,
    "catalog": str,
    "fact_sheets": str,
    "ledger": str,
    "changes": str,
    "scanners": list,
}
OPTIONAL_KEYS: dict[str, type] = {
    "api_doc": str,
    "update_api_md": bool,
    "repo_name_prefix": str,
}


class UnsafePathError(ValueError):
    """Raised when a path would escape its allowed base directory."""


def resolve_within(base: str | Path, rel: str | Path) -> Path:
    """Resolve `rel` under `base`; raise UnsafePathError if it escapes `base`.

    Blocks `../` traversal and absolute-path escapes.
    """
    base_r = Path(base).resolve()
    target = (base_r / rel).resolve()
    if target != base_r and base_r not in target.parents:
        raise UnsafePathError(f"path {rel!r} escapes base {base_r}")
    return target


def validate_config(cfg: dict) -> dict:
    """Validate a `.kb-sync.json` dict. Raise ValueError with a clear message."""
    if not isinstance(cfg, dict):
        raise ValueError(".kb-sync.json must be a JSON object")
    missing = [k for k in REQUIRED_KEYS if k not in cfg]
    if missing:
        raise ValueError(f".kb-sync.json missing required keys: {', '.join(sorted(missing))}")
    for key, typ in REQUIRED_KEYS.items():
        if not isinstance(cfg[key], typ):
            raise ValueError(f".kb-sync.json key '{key}' must be {typ.__name__}, got {type(cfg[key]).__name__}")
    for key, typ in OPTIONAL_KEYS.items():
        if key in cfg and not isinstance(cfg[key], typ):
            raise ValueError(f".kb-sync.json key '{key}' must be {typ.__name__}")
    return cfg


def run_git(args: list[str], cwd: str | Path) -> subprocess.CompletedProcess:
    """Run git with an argument LIST (never shell=True) to avoid injection."""
    if not all(isinstance(a, str) for a in args):
        raise TypeError("git args must be strings")
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        shell=False,
        check=False,
    )
