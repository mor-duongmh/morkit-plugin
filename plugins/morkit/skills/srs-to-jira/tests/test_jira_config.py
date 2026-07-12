"""Where the credential lives, and the three ways we refuse to read it.

The refusals matter more than the happy path. A token in a 0644 file inside a git
repo is not a smaller version of a working setup — it is a credential one `git add -A`
away from the internet, and the tool should say so rather than quietly using it.
"""

from __future__ import annotations

import subprocess

import pytest

import jira_client as jc
import jira_config as cfgfile

TOKEN = "s3cret-token-value"


def write_env(path, body: str, mode: int = 0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(mode)
    return path


def good_env_file(tmp_path, mode: int = 0o600):
    return write_env(
        tmp_path / "jira.env",
        f"export JIRA_BASE_URL=https://jira.example.com\n"
        f"export JIRA_PROJECT_KEY=PROJ\n"
        f"export JIRA_PAT={TOKEN}\n",
        mode,
    )


# --- the happy path -------------------------------------------------------


def test_values_come_from_the_file(tmp_path):
    path = good_env_file(tmp_path)
    values = cfgfile.resolve({"MORKIT_JIRA_ENV": str(path)})
    assert values["JIRA_BASE_URL"] == "https://jira.example.com"
    assert values["JIRA_PAT"] == TOKEN


def test_the_environment_wins_over_the_file(tmp_path):
    """So CI can inject the values with no file on disk at all."""
    path = good_env_file(tmp_path)
    values = cfgfile.resolve({"MORKIT_JIRA_ENV": str(path), "JIRA_PROJECT_KEY": "OTHER"})
    assert values["JIRA_PROJECT_KEY"] == "OTHER"
    assert values["JIRA_PAT"] == TOKEN  # the rest still comes from the file


def test_quotes_and_comments_are_handled(tmp_path):
    path = write_env(
        tmp_path / "jira.env",
        '# my jira\nJIRA_BASE_URL="https://jira.example.com"\n\n'
        "JIRA_PROJECT_KEY='PROJ'\nJIRA_PAT=abc\n",
    )
    values = cfgfile.load(path)
    assert values == {
        "JIRA_BASE_URL": "https://jira.example.com",
        "JIRA_PROJECT_KEY": "PROJ",
        "JIRA_PAT": "abc",
    }


def test_a_missing_file_is_not_an_error(tmp_path):
    """It just means nothing is configured yet — which is a state to guide out of, not
    to crash on."""
    assert cfgfile.load(tmp_path / "nope.env") == {}


# --- the three refusals ---------------------------------------------------


def test_a_world_readable_file_is_refused(tmp_path):
    path = good_env_file(tmp_path, mode=0o644)
    with pytest.raises(cfgfile.ConfigFileError, match="can read your token"):
        cfgfile.load(path)


def test_a_file_inside_a_git_repo_is_refused(tmp_path):
    """`git add -A` is the most common way a credential reaches the internet. A secrets
    file must not be somewhere a commit can reach it."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    path = good_env_file(tmp_path)
    with pytest.raises(cfgfile.ConfigFileError, match="git repository"):
        cfgfile.load(path)


def test_a_shared_secrets_file_is_refused(tmp_path):
    """We would rather not pull somebody's AWS keys into this process at all."""
    path = write_env(
        tmp_path / "jira.env",
        "JIRA_BASE_URL=https://jira.example.com\nJIRA_PAT=abc\nAWS_SECRET_ACCESS_KEY=xyz\n",
    )
    with pytest.raises(cfgfile.ConfigFileError, match="shared secrets file"):
        cfgfile.load(path)


def test_we_do_not_quietly_fix_an_unsafe_file(tmp_path):
    """A secret in the wrong place is something the user needs to know about, not
    something to tidy up behind their back."""
    path = good_env_file(tmp_path, mode=0o644)
    with pytest.raises(cfgfile.ConfigFileError):
        cfgfile.load(path)
    assert path.stat().st_mode & 0o077  # still 0644 — we changed nothing


# --- the verdict never leaks a value --------------------------------------


def test_the_report_names_keys_but_never_prints_them(tmp_path):
    path = good_env_file(tmp_path)
    report = cfgfile.inspect(path)
    assert report["keys"] == ["JIRA_BASE_URL", "JIRA_PAT", "JIRA_PROJECT_KEY"]
    assert TOKEN not in str(report)


def test_the_check_verdict_carries_no_secret(tmp_path):
    path = good_env_file(tmp_path)
    verdict = cfgfile.check({"MORKIT_JIRA_ENV": str(path)})
    assert verdict["ok"] is True
    assert verdict["credential"] == "set"  # that it exists, not what it is
    assert TOKEN not in str(verdict)


def test_the_check_verdict_says_exactly_what_is_missing(tmp_path):
    path = write_env(tmp_path / "jira.env", "JIRA_BASE_URL=https://jira.example.com\n")
    verdict = cfgfile.check({"MORKIT_JIRA_ENV": str(path)})
    assert verdict["ok"] is False
    assert set(verdict["missing"]) == {"JIRA_PROJECT_KEY", "JIRA_PAT"}


def test_an_unreadable_file_does_not_crash_the_check(tmp_path):
    path = good_env_file(tmp_path, mode=0o644)
    verdict = cfgfile.check({"MORKIT_JIRA_ENV": str(path)})
    assert verdict["ok"] is False
    assert "can read your token" in verdict["file"]["problems"][0]


# --- offline needs no token -----------------------------------------------


def test_offline_does_not_demand_a_credential():
    """The rehearsal path exists for someone who does not have a token yet. Demanding
    one made it useless to the only people it was for — and made SKILL.md a liar."""
    env = {"JIRA_BASE_URL": "https://jira.example.com", "JIRA_PROJECT_KEY": "PROJ"}
    with pytest.raises(jc.ConfigError, match="No Jira credential"):
        jc.config_from_env(env)

    cfg = jc.config_from_env(env, require_credential=False)
    assert cfg.project_key == "PROJ"  # still bound to a target; just cannot send


def test_an_explicit_env_never_touches_the_users_file(tmp_path, monkeypatch):
    """Tests and CI pass values directly. Reading the developer's real ~/.config would
    make the suite depend on the machine it runs on."""
    monkeypatch.setenv("MORKIT_JIRA_ENV", str(good_env_file(tmp_path)))
    cfg = jc.config_from_env(
        {"JIRA_BASE_URL": "https://other.example.com", "JIRA_PROJECT_KEY": "OTHER", "JIRA_PAT": "t"}
    )
    assert cfg.base_url == "https://other.example.com"
    assert cfg.pat == "t"  # not TOKEN from the file
