"""Where the Jira credential lives, and what it has to satisfy before we will use it.

The token goes **file -> this process**. It is never sourced into a shell, never
passed as `JIRA_PAT=... python script.py`, never echoed. Cutting the shell out cuts
out every path by which a credential normally escapes: the command log, `ps aux`, and
the shell history.

Three refusals, none of which we fix on the user's behalf — a secret sitting in the
wrong place is something they need to know about, not something to quietly tidy up:

  * **Inside a git repository.** `git add -A` is the single most common way a
    credential reaches the internet. A secrets file must not be somewhere a commit
    can reach it.
  * **Readable by group or other.** 0600 or nothing.
  * **Carrying non-JIRA keys.** We would rather not load somebody's AWS keys into this
    process at all, and a shared secrets file is the wrong thing to point us at.

Precedence: the real environment wins over the file, so CI can inject the values
without a file existing at all.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

DEFAULT_ENV_FILE = "~/.config/morkit/jira.env"
REQUIRED = ("JIRA_BASE_URL", "JIRA_PROJECT_KEY")
CREDENTIAL_SETS = (("JIRA_PAT",), ("JIRA_USER", "JIRA_PASSWORD"))

_KEY = re.compile(r"^(?:export\s+)?(?P<key>[A-Z][A-Z0-9_]*)\s*=\s*(?P<value>.*)$")
_JIRA_KEY = re.compile(r"^JIRA_[A-Z0-9_]+$")


class ConfigFileError(ValueError):
    """The file exists but is not safe to read a secret from."""


def env_file_path(env=None) -> Path:
    env = os.environ if env is None else env
    return Path(env.get("MORKIT_JIRA_ENV") or DEFAULT_ENV_FILE).expanduser()


def _inside_git_repo(path: Path) -> bool:
    """True if a commit could reach this file."""
    try:
        done = subprocess.run(
            ["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return False  # no git installed; nothing can commit it
    return done.returncode == 0


def _parse(text: str) -> dict:
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = _KEY.match(line)
        if match:
            value = match.group("value").strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[match.group("key")] = value
    return values


def inspect(path: Path) -> dict:
    """Report on the file WITHOUT revealing any value. Safe to print, safe to log."""
    report = {"path": str(path), "exists": path.is_file(), "problems": [], "keys": []}
    if not report["exists"]:
        return report

    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        report["problems"].append(
            f"{path} is mode {mode:04o} — other users on this machine can read your token. "
            f"Fix it yourself:  chmod 600 {path}"
        )

    if _inside_git_repo(path):
        report["problems"].append(
            f"{path} sits inside a git repository. One `git add -A` puts your token in a "
            f"commit. Move it out — {DEFAULT_ENV_FILE} is the intended home."
        )

    values = _parse(path.read_text(encoding="utf-8"))
    report["keys"] = sorted(values)  # names only; never the values
    strays = [k for k in values if not _JIRA_KEY.match(k)]
    if strays:
        report["problems"].append(
            f"{path} also holds {strays} — this looks like a shared secrets file. Give Jira "
            "its own file rather than loading unrelated credentials into this process."
        )
    return report


def load(path: Path) -> dict:
    """Parse the file, refusing outright if it is not safe to read a secret from."""
    report = inspect(path)
    if not report["exists"]:
        return {}
    if report["problems"]:
        raise ConfigFileError("\n".join(report["problems"]))
    return _parse(path.read_text(encoding="utf-8"))


def resolve(env=None) -> dict:
    """File values, with the real environment layered on top. Environment wins."""
    environ = os.environ if env is None else env
    values = load(env_file_path(environ))
    values.update({k: v for k, v in environ.items() if k.startswith("JIRA_") and v})
    return values


def missing(values: dict) -> list:
    """Which variables are still needed. Names only."""
    gaps = [key for key in REQUIRED if not values.get(key)]
    if not any(all(values.get(k) for k in group) for group in CREDENTIAL_SETS):
        gaps.append("JIRA_PAT")  # or JIRA_USER + JIRA_PASSWORD
    return gaps


def check(env=None) -> dict:
    """The verdict the skill shows the user. Contains no secret."""
    environ = os.environ if env is None else env
    path = env_file_path(environ)
    report = inspect(path)
    try:
        values = resolve(environ)
    except ConfigFileError:
        return {"ok": False, "file": report, "missing": list(REQUIRED) + ["JIRA_PAT"],
                "hint": "the file was refused — fix the problems above and try again"}

    gaps = missing(values)
    return {
        "ok": not gaps,
        "file": report,
        "missing": gaps,
        "project": values.get("JIRA_PROJECT_KEY", ""),
        "base_url": values.get("JIRA_BASE_URL", ""),  # not a secret
        "credential": "set" if values.get("JIRA_PAT") or values.get("JIRA_PASSWORD") else "missing",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check the Jira connection settings")
    parser.add_argument("command", choices=["check"])
    parser.parse_args(argv)

    result = check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
