"""The only code here that touches the network. Jira Server / Data Center, REST v2.

Every request goes through `_request`, so a test can count calls and prove that a
refused approval sent nothing.

Two things about `urllib` that the stdlib will happily do to you:

  * CPython's `HTTPRedirectHandler` copies every header except `content-*` onto the
    redirect target — `Authorization` included, to any host. One misconfigured proxy,
    one stale JIRA_BASE_URL, and the PAT is posted to somebody else's server, on the
    very first preflight call. So: no redirect handler that follows anything.
  * `build_opener()` / `urlopen()` also register FileHandler, FTPHandler and
    DataHandler. `JIRA_BASE_URL` comes from the environment. `file:///` should not
    be a reachable code path. So: an OpenerDirector with HTTPS and nothing else.

There is no other HTTP client anywhere in this plugin to copy from — this is the
first one — which is why these two are spelled out rather than assumed.
"""

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jira_config  # noqa: E402
from task_mapper import LABEL_ALL  # noqa: E402  single definition; recovery depends on it

TIMEOUT = 30  # urllib blocks forever by default
PAGE_SIZE = 100
PROJECT_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]{1,9}$")


class JiraError(RuntimeError):
    """A request failed. The message never carries the credential."""


class ConfigError(ValueError):
    """The environment is not safe to run against."""


@dataclass
class Config:
    base_url: str
    project_key: str
    story_type: str = "Story"
    task_type: str = "Task"
    # repr=False: one stray log.debug("%r", cfg) would otherwise print the credential.
    pat: str = field(default="", repr=False)
    user: str = field(default="", repr=False)
    password: str = field(default="", repr=False)
    calls: int = 0  # every _request bumps this; tests assert it stays 0 when refused

    @property
    def secret(self) -> str:
        return self.pat or self.password


@dataclass
class Preflight:
    account: str
    issue_types: list = field(default_factory=list)
    priorities: list = field(default_factory=list)

    def issue_type_missing(self, wanted) -> list:
        return sorted({w for w in wanted if w not in self.issue_types})

    def keeps_priority(self, name) -> bool:
        return bool(name) and name in self.priorities


def config_from_env(env=None, require_credential: bool = True) -> Config:
    """Resolve the settings. `env=None` reads the real environment plus the config file.

    An explicit `env` dict is taken verbatim and the user's file is left alone — that
    is how tests and CI supply values without depending on (or touching) a real machine.

    `require_credential=False` for offline work: the base URL and the project key are
    still needed, because the approval in the breakdown file is bound to them — but no
    token, because nothing is going to be sent.
    """
    env = jira_config.resolve() if env is None else env
    base_url = (env.get("JIRA_BASE_URL") or "").strip().rstrip("/")
    project_key = (env.get("JIRA_PROJECT_KEY") or "").strip()

    if not base_url:
        raise ConfigError("JIRA_BASE_URL is not set.")
    parts = urllib.parse.urlsplit(base_url)
    if parts.scheme != "https":
        raise ConfigError(
            f"JIRA_BASE_URL must be https (got {parts.scheme or 'no scheme'!r}). "
            "The credential is sent on every request; plaintext is not an option."
        )
    if parts.username or parts.password or "@" in parts.netloc:
        raise ConfigError("JIRA_BASE_URL must not embed credentials.")

    # Interpolated into JQL and into request paths. An unvalidated key here would let
    # `X" OR project = OPS` retarget the recovery query at somebody else's project —
    # whose issues we would then dutifully overwrite.
    if not PROJECT_KEY_RE.match(project_key):
        raise ConfigError(
            f"JIRA_PROJECT_KEY {project_key!r} is not a Jira project key "
            "(expected 2-10 chars, A-Z then A-Z/0-9)."
        )

    cfg = Config(
        base_url=base_url,
        project_key=project_key,
        story_type=env.get("JIRA_ISSUE_TYPE_STORY", "Story"),
        task_type=env.get("JIRA_ISSUE_TYPE_TASK", "Task"),
        pat=env.get("JIRA_PAT", ""),
        user=env.get("JIRA_USER", ""),
        password=env.get("JIRA_PASSWORD", ""),
    )
    if require_credential and not cfg.pat and not (cfg.user and cfg.password):
        raise ConfigError(
            "No Jira credential. Set JIRA_PAT (Jira 8.14+), or JIRA_USER + JIRA_PASSWORD, "
            f"in {jira_config.env_file_path()} or in the environment. "
            "Run `jira_config.py check` to see exactly what is missing."
        )
    return cfg


class _RefuseRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise JiraError(
            f"Jira answered with a redirect to {newurl!r}. The REST API does not "
            "legitimately redirect, and following it would hand the credential to "
            "whatever host is on the other end. Refusing."
        )


def _tls_context() -> ssl.SSLContext:
    """Verified TLS, stated explicitly.

    `create_default_context()` already verifies — but self-hosted Jira behind an
    internal CA is exactly the situation where someone reaches for
    `_create_unverified_context()`. Spelling the guarantee out makes removing it a
    visible edit rather than a one-word deletion.
    """
    context = ssl.create_default_context()
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def _opener() -> urllib.request.OpenerDirector:
    director = urllib.request.OpenerDirector()
    director.add_handler(urllib.request.HTTPSHandler(context=_tls_context()))
    director.add_handler(urllib.request.HTTPDefaultErrorHandler())
    director.add_handler(urllib.request.HTTPErrorProcessor())
    director.add_handler(_RefuseRedirect())
    return director  # note: no HTTP, FTP, File or Data handler


def _auth_header(cfg: Config) -> str:
    if cfg.pat:
        return f"Bearer {cfg.pat}"
    import base64

    raw = base64.b64encode(f"{cfg.user}:{cfg.password}".encode()).decode()
    return f"Basic {raw}"


def redact(text: str, cfg: Config) -> str:
    """Scrub the credential out of anything we are about to show a human or a log."""
    secret = cfg.secret
    return text.replace(secret, "***") if secret else text


def _request(cfg: Config, method: str, path: str, body=None):
    """The single network call site."""
    cfg.calls += 1
    url = cfg.base_url + path
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", _auth_header(cfg))
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")

    try:
        with _opener().open(request, timeout=TIMEOUT) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = redact(exc.read().decode("utf-8", "replace")[:800], cfg)
        raise JiraError(f"{method} {path} -> HTTP {exc.code}. {detail}") from None
    except urllib.error.URLError as exc:
        raise JiraError(f"{method} {path} -> {redact(str(exc.reason), cfg)}") from None
    except json.JSONDecodeError as exc:
        # A 200 whose body is not JSON means we are not talking to Jira — an SSO or
        # proxy interstitial, most likely. Left unwrapped this escapes the caller's
        # `except JiraError` and aborts the push halfway through the backlog.
        raise JiraError(
            f"{method} {path} -> answered 200 with a non-JSON body ({exc.msg}). "
            "Something in front of Jira is intercepting the request (SSO? proxy?)."
        ) from None
    except OSError as exc:
        # socket.timeout is an OSError and is NOT wrapped by urllib once the response
        # headers are in — it fires while reading the body. Thirty seconds into one of
        # sixty sequential posts, that is routine, not exotic.
        raise JiraError(f"{method} {path} -> {redact(str(exc), cfg)}") from None


# --- preflight: fail before the reviewer spends an hour, not after -------


def preflight(cfg: Config) -> Preflight:
    account = _request(cfg, "GET", "/rest/api/2/myself").get("name", "?")

    project = urllib.parse.quote(cfg.project_key, safe="")
    meta = _request(
        cfg,
        "GET",
        f"/rest/api/2/issue/createmeta?projectKeys={project}&expand=projects.issuetypes",
    )
    issue_types = [
        it.get("name")
        for proj in meta.get("projects", [])
        for it in proj.get("issuetypes", [])
    ]

    priorities = [p.get("name") for p in _request(cfg, "GET", "/rest/api/2/priority")]
    return Preflight(account=account, issue_types=issue_types, priorities=priorities)


# --- writes: one issue per request ---------------------------------------


def create_issue(cfg: Config, task: dict, summary: str, priority) -> str:
    """POST one issue, get one key back.

    Deliberately not /issue/bulk: its response array holds only the successes,
    compacted, while `failedElementNumber` indexes what was submitted. One rejected
    element mid-batch and the two stop lining up — bind key N to requirement N+1 and
    the next run's UPDATE overwrites the wrong ticket. Sixty sequential posts take
    about twelve seconds; that is a cheap price for an index that cannot slip.
    """
    fields = {
        "project": {"key": cfg.project_key},
        "summary": summary,
        "description": task["description"],
        "issuetype": {"name": _issue_type(cfg, task)},
        "labels": task["labels"],
    }
    if priority:
        fields["priority"] = {"name": priority}
    return _request(cfg, "POST", "/rest/api/2/issue", {"fields": fields})["key"]


def update_issue(cfg: Config, key: str, task: dict, summary: str, priority) -> None:
    fields = {"summary": summary, "description": task["description"]}
    if priority:
        fields["priority"] = {"name": priority}
    _request(cfg, "PUT", f"/rest/api/2/issue/{urllib.parse.quote(key, safe='')}", {"fields": fields})


def get_issue(cfg: Config, key: str) -> dict:
    quoted = urllib.parse.quote(key, safe="")
    data = _request(cfg, "GET", f"/rest/api/2/issue/{quoted}?fields=summary,description")
    fields = data.get("fields") or {}
    return {"summary": fields.get("summary") or "", "description": fields.get("description") or ""}


def _issue_type(cfg: Config, task: dict) -> str:
    return cfg.story_type if task["issue_type"] == "Story" else cfg.task_type


# --- reads: recovery and reconciliation ----------------------------------


def search_by_label(cfg: Config, label: str) -> list:
    """Paginated JQL. Both the project key and the label are validated upstream, so
    neither can break out of the quoted string."""
    jql = f'project = "{cfg.project_key}" AND labels = "{label}"'
    found, start = [], 0
    while True:
        query = urllib.parse.urlencode(
            {"jql": jql, "startAt": start, "maxResults": PAGE_SIZE, "fields": "labels,summary"}
        )
        page = _request(cfg, "GET", f"/rest/api/2/search?{query}")
        issues = page.get("issues") or []
        found.extend(issues)
        start += len(issues)
        if not issues or start >= page.get("total", 0):
            return found


def find_by_label(cfg: Config, label: str):
    """Used to reconcile a create that may or may not have landed."""
    for issue in search_by_label(cfg, label):
        if label in (issue.get("fields", {}).get("labels") or []):
            return issue.get("key")
    return None
