"""Session lock for docs-hero — prevent concurrent mutations.

Stores a JSON lock file at `.docs-hero.lock` in the project root with PID + ISO
timestamp. A lock is considered stale if its timestamp is older than `MAX_AGE`
or its PID is not alive. Stale locks are auto-cleaned.

CLI:
    lock_manager.py acquire [--lock-file PATH]
    lock_manager.py release [--lock-file PATH]
    lock_manager.py status  [--lock-file PATH]

Public API:
    acquire(lock_path) -> bool
    release(lock_path) -> None
    is_locked(lock_path) -> tuple[bool, str]  # (locked, reason)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger(__name__)

MAX_AGE = timedelta(hours=1)


def _process_alive(pid: int) -> bool:
    """Check if a PID is still alive (POSIX). On other platforms returns True conservatively."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we can't signal it — still alive
        return True
    except OSError:
        return False
    return True


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _read_lock(lock_path: Path) -> dict | None:
    if not lock_path.exists():
        return None
    try:
        return json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def is_locked(lock_path: Path) -> tuple[bool, str]:
    """Return (locked, reason). 'locked' False means caller may acquire."""
    data = _read_lock(lock_path)
    if data is None:
        return False, "no lock"

    pid = int(data.get("pid", 0))
    ts_raw = data.get("acquired_at", "")
    try:
        ts = datetime.fromisoformat(ts_raw)
    except ValueError:
        return False, "stale (bad timestamp)"

    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    age = datetime.now(tz=timezone.utc) - ts
    if age > MAX_AGE:
        return False, f"stale (age {age})"
    if not _process_alive(pid):
        return False, f"stale (pid {pid} not alive)"

    return True, f"held by pid {pid} since {ts_raw}"


def acquire(lock_path: Path) -> bool:
    """Try to acquire the lock; return True on success, False if held."""
    locked, reason = is_locked(lock_path)
    if locked:
        log.warning("lock held: %s", reason)
        return False

    if lock_path.exists():
        log.info("removing stale lock: %s", reason)
        lock_path.unlink(missing_ok=True)

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "pid": os.getpid(),
        "acquired_at": _now_iso(),
        "host": os.uname().nodename if hasattr(os, "uname") else "unknown",
    }
    lock_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return True


def release(lock_path: Path) -> None:
    """Release the lock if held by current PID. No-op otherwise."""
    data = _read_lock(lock_path)
    if data is None:
        return
    if int(data.get("pid", -1)) == os.getpid():
        lock_path.unlink(missing_ok=True)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("command", choices=["acquire", "release", "status"])
    p.add_argument("--lock-file", default=".docs-hero.lock")
    args = p.parse_args()

    lock_path = Path(args.lock_file)

    if args.command == "acquire":
        ok = acquire(lock_path)
        if ok:
            print(f"acquired -> {lock_path}", file=sys.stderr)
            return 0
        locked, reason = is_locked(lock_path)
        print(f"FAIL: another session holds the lock — {reason}", file=sys.stderr)
        return 1

    if args.command == "release":
        release(lock_path)
        print(f"released -> {lock_path}", file=sys.stderr)
        return 0

    # status
    locked, reason = is_locked(lock_path)
    print(f"locked={locked} reason={reason}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
