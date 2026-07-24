---
name: "morkit:to-jira"
description: Turn a validated SRS (ProjectModel JSON) into Jira issues — one Story per FunctionalRequirement, one Task per NFR. Renders a breakdown the reviewer signs, then pushes to Jira Server/Data Center. Re-running never duplicates the backlog.
category: Workflow
tags: [jira, srs, tickets, backlog, brse, greenfield]
argument-hint: "--model <project-model.json> [--lang JP|EN|VN] [--skip-nfr] [--dry-run]"
---

Invoke the `srs-to-jira` skill using the Skill tool. Pass through the user's
arguments (`--model`, `--lang`, `--skip-nfr`, `--dry-run`).

The skill will:
1. Render the model into `tasks.json` — mechanically. The SRS already holds the
   ticket content; nothing is invented.
2. **Preflight the Jira target first** — a Kanban project often has no `Story` issue
   type, and that is not something to discover after an hour of review.
3. Write `task-breakdown.md`, one row per issue, with ⚠ flags on requirements that
   are still thin.
4. **Wait for a human** to edit it and set `status: approved` themselves. Claude never
   touches that line, and the push re-checks it anyway.
5. Push, recording each requirement → issue key in `jira-map.json`.

Prerequisite: the docs-hero venv (`/morkit:setup`).

**Jira settings are not a prerequisite — the skill sets them up with you.** On the
first run it checks `~/.config/morkit/jira.env`, and if nothing is there it asks for
the base URL and project key, explains how to mint a Personal Access Token (and why it
should belong to a scoped service account with an expiry), and hands you a one-liner to
store it. It never asks for the token in chat: a token typed there lives in the
transcript for good. `/morkit:doctor` reports the same status ahead of time.

> Follows `/morkit:greenfield` naturally, but does not require it — any validated
> `project-model.json` works, brownfield included.
