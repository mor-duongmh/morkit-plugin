"""Check the Jira side BEFORE the reviewer is asked to read anything.

This exists as its own CLI for one reason: ordering. A Kanban project typically
offers `Task` and `Bug` and no `Story` at all. Discovering that inside the push —
after someone spent forty minutes reading sixty rows, editing summaries and signing
the file — is the wrong time to find out. SKILL.md runs this first and only renders
the breakdown if it passes.

Reports the instance's real priority scheme too, so `build_tasks.py` output can be
checked against it rather than having Jira quietly drop a field we made up.

CLI:
    preflight_check.py --tasks tasks.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jira_client as jc  # noqa: E402
import jira_config  # noqa: E402


def check(tasks_payload: dict = None, env=None) -> dict:
    """Verify the Jira target. `tasks_payload` is optional: with no SRS in hand this is
    still a useful "does my connection work" check, which is what someone setting the
    credential up for the first time actually needs."""
    tasks_payload = tasks_payload or {}
    cfg = jc.config_from_env(env)
    pre = jc.preflight(cfg)

    wanted_types = {
        cfg.story_type if task["issue_type"] == "Story" else cfg.task_type
        for task in tasks_payload.get("tasks") or []
    }
    missing_types = pre.issue_type_missing(wanted_types)

    wanted_priorities = {t["priority"] for t in tasks_payload.get("tasks") or [] if t["priority"]}
    unknown_priorities = sorted(p for p in wanted_priorities if not pre.keeps_priority(p))

    problems = []
    if missing_types:
        problems.append(
            f"project {cfg.project_key} has no issue type {missing_types}; "
            f"it offers: {', '.join(pre.issue_types) or '(none)'}. "
            "Set JIRA_ISSUE_TYPE_STORY / JIRA_ISSUE_TYPE_TASK to names it does have."
        )

    warnings = []
    if unknown_priorities:
        # Not fatal: an issue with no priority still beats no issue.
        warnings.append(
            f"this Jira has no priority named {unknown_priorities}; those tickets will "
            f"be created without a priority. It offers: {', '.join(pre.priorities)}."
        )

    return {
        "ok": not problems,
        "account": pre.account,
        "project": cfg.project_key,
        "issue_types": pre.issue_types,
        "priorities": pre.priorities,
        "problems": problems,
        "warnings": warnings,
        "requests": cfg.calls,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verify the Jira target before the gate")
    parser.add_argument(
        "--tasks",
        help="tasks.json from build_tasks.py. Omit to check the connection on its own — "
        "useful when setting the credential up, before there is any SRS to push.",
    )
    args = parser.parse_args(argv)

    try:
        payload = json.loads(Path(args.tasks).read_bytes()) if args.tasks else None
        result = check(payload)
    except (jc.ConfigError, jc.JiraError, jira_config.ConfigFileError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
