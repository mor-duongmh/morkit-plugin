"""The ledger that makes a re-run safe: which SRS id became which Jira issue.

Shape (`jira-map.json`):

    {
      "version": 1,
      "project_key": "PROJ",
      "base_url": "https://jira.company.com",
      "source_model": {"path": "...", "sha256": "..."},
      "issues": {
        "FR-001": {
          "key": "PROJ-123",
          "state": "created",              # or "creating" — see below
          "source_hash": "sha256:...",     # of the MACHINE render. Drives the diff.
          "pushed_hash": "sha256:...",     # of what was actually SENT. Detects Jira drift.
          "overrides": {"summary": "..."}, # the reviewer's hand-edit, kept alive
          "pushed_at": "..."
        }
      }
    }

Why two hashes and an `overrides` bag, when one hash looks like enough:

    A reviewer edits a summary in the gate file. We push the edit. If we then store
    a single hash *of the edited text*, the next run re-renders tasks.json from the
    SRS (which still holds the original name), sees a hash mismatch, issues an
    UPDATE — and that UPDATE overwrites the reviewer's edit back to the machine
    text. Silently. It looks like the tool working.

    So: `source_hash` answers "did the SRS change?" and nothing else. The edit lives
    in `overrides` and is re-applied at render and at push. An unchanged SRS is a
    SKIP even for a row a human touched.

`state: "creating"` is written BEFORE the POST. If the process dies between the
request leaving and the response arriving, the issue exists in Jira but not here —
that entry is the breadcrumb that lets the next run reconcile instead of duplicate.
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

VERSION = 1
STATE_CREATING = "creating"
STATE_CREATED = "created"


class UnsafePathError(ValueError):
    """A path would escape its allowed base directory."""


class BindingError(ValueError):
    """The approved file, the ledger and the environment do not agree on a target."""


class LockedError(RuntimeError):
    """Another push holds the lock."""


def resolve_within(base: str | Path, target: str | Path) -> Path:
    """Resolve `target` under `base`; refuse to escape it.

    Mirrors kb-sync's `safe_io.resolve_within` rather than importing it: a skill has
    to install and uninstall on its own, so reaching into another skill's private
    scripts is a worse coupling than ten duplicated lines. Paths here are built by
    the model from chat text, so a prompt-injected SRS could otherwise steer
    `--map` at, say, ~/.ssh/config — and `os.replace()` would destroy it atomically.
    """
    base_r = Path(base).resolve()
    resolved = (base_r / target).resolve() if not Path(target).is_absolute() else Path(target).resolve()
    if resolved != base_r and base_r not in resolved.parents:
        raise UnsafePathError(f"path {target!r} escapes {base_r}")
    return resolved


def ensure_private_workspace(directory: str | Path) -> Path:
    """Create the workspace and make sure git will never pick it up.

    This runs inside the *customer's* repo, not ours. `jira-map.json` carries the
    internal Jira hostname and `tasks.json` carries the entire SRS; a `git add -A`
    would commit both. Relying on the consuming repo to have thought of that is not a
    plan, so the directory ignores itself.

    It must never do that to a directory that is not ours, though: writing `*` into a
    repository root would make git ignore every untracked file in the project. Bare
    `--out tasks.json` resolves its parent to `.` — so this refuses rather than
    quietly detonating.
    """
    path = Path(directory).resolve()
    if (path / ".git").exists() or path == Path.cwd().resolve():
        raise UnsafePathError(
            f"refusing to mark {path} as git-ignored — that looks like your project root, "
            "and a `*` .gitignore there would hide every untracked file. "
            "Write into a workspace instead, e.g. morkit/output/jira/<PROJECT_KEY>/."
        )
    path.mkdir(parents=True, exist_ok=True)
    marker = path / ".gitignore"
    if not marker.exists():
        marker.write_text("# Written by morkit srs-to-jira: never commit this.\n*\n", encoding="utf-8")
    return path


def new_map(project_key: str, base_url: str, model_path: str, model_sha256: str) -> dict:
    return {
        "version": VERSION,
        "project_key": project_key,
        "base_url": base_url.rstrip("/"),
        "source_model": {"path": model_path, "sha256": model_sha256},
        "issues": {},
    }


def load_map(path: str | Path) -> dict | None:
    """Return the ledger, or None when there is none yet (a first run)."""
    p = Path(path)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("version") != VERSION:
        raise ValueError(f"{p}: unsupported jira-map version {data.get('version')!r}")
    return data


def save_map_atomic(path: str | Path, data: dict) -> None:
    """Write via a temp file on the same filesystem + os.replace.

    Atomic against a crash, NOT against a concurrent writer — `map_lock` covers that.
    (kb-sync's ledger uses a plain write_text and is not safe here; do not copy it.)
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".jira-map-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, p)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


@contextmanager
def map_lock(path: str | Path):
    """Exclusive lock for the whole push.

    An atomic write stops a *crash* from corrupting the ledger; it does nothing
    about two pushes running at once. Without this, both read a 20-issue map, both
    create tickets, and whoever writes last silently orphans the other's tickets —
    invisible to every later diff.
    """
    lock_path = Path(str(path) + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("w")
    try:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise LockedError(
                f"another push is already running (lock held on {lock_path}). "
                f"Wait for it to finish rather than running two at once."
            ) from exc
        yield
    finally:
        fcntl.flock(handle, fcntl.LOCK_UN)
        handle.close()


def assert_bindings(frontmatter: dict, project_key: str, base_url: str) -> None:
    """The APPROVED FILE decides where the push goes — not the environment, not the map.

    A ledger-vs-env check is useless exactly when it matters: on a first run there is
    no ledger, and the recovery flow deliberately deletes it. The human approved a
    file that names a project; if the shell says something else, that is a mistake
    worth stopping for, not a preference to silently follow.
    """
    want = {"project": project_key, "base_url": base_url.rstrip("/")}
    for field, expected in want.items():
        actual = (frontmatter.get(field) or "").rstrip("/")
        if not actual:
            # An absent field is not a pass. The reviewer is told to hand-edit this
            # file; deleting a line they did not understand must not silently hand the
            # target over to whatever the shell happens to be exporting.
            raise BindingError(
                f"the approved breakdown has no `{field}:` in its frontmatter, so there is "
                "nothing proving the reviewer agreed to this target. Re-render the breakdown."
            )
        if actual != expected:
            raise BindingError(
                f"the approved breakdown targets {field}={actual!r} but the environment "
                f"says {expected!r}. Refusing to push somewhere the reviewer did not approve."
            )


def assert_same_model(jira_map: dict, tasks_meta: dict) -> None:
    """One ledger per SRS. Two different models sharing a Jira project would collide
    on `FR-001` and update each other's tickets."""
    known = (jira_map.get("source_model") or {}).get("sha256")
    incoming = tasks_meta.get("model_sha256")
    if known and incoming and known != incoming and jira_map.get("issues"):
        raise BindingError(
            "this jira-map was built from a different project-model "
            f"({known[:12]}… vs {incoming[:12]}…). Two SRS cannot share one map: both "
            "number their requirements FR-001 and would overwrite each other's issues. "
            "Use a separate --map for this model."
        )


def get_override(jira_map: dict, source_id: str, field: str) -> str | None:
    entry = (jira_map.get("issues") or {}).get(source_id) or {}
    return (entry.get("overrides") or {}).get(field)


def set_entry(jira_map: dict, source_id: str, **fields) -> dict:
    """Merge fields into an issue entry, creating it if needed."""
    entry = jira_map.setdefault("issues", {}).setdefault(source_id, {})
    entry.update({k: v for k, v in fields.items() if v is not None})
    return entry
