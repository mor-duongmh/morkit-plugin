---
name: srs-to-jira
description: "Turn a validated SRS (ProjectModel JSON) into Jira issues on a self-hosted Jira Server/Data Center — one Story per FunctionalRequirement, one Task per NFR. Renders a task-breakdown.md the reviewer edits and signs, then pushes. Idempotent: a re-run never duplicates the backlog. Use when someone says 'push the SRS to Jira', 'tạo ticket từ SRS', 'log tasks to Jira', or after /morkit:greenfield finishes."
user-invocable: true
category: workflow
keywords: [jira, srs, tickets, backlog, brse, greenfield, issue-tracker]
allowed-tools: Bash, Read, AskUserQuestion
argument-hint: "--model <project-model.json> [--lang JP|EN|VN] [--skip-nfr] [--dry-run]"
metadata:
  author: morkit
  version: "1.0.0"
---

# SRS → Jira

**Standalone.** Reads a `project-model.json` (from `/morkit:greenfield` G5, or any
validated model) and creates the matching issues on Jira. Works for brownfield too —
it needs a model, not a greenfield run.

## Environment

```bash
PLUGIN_ROOT="${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:?set by Claude Code}}"
SKILL_DIR="${PLUGIN_ROOT}/skills/srs-to-jira"
VENV="${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data}}/docs-hero/.venv"
PY="${VENV}/bin/python3"
[ -x "$PY" ] || { echo "Run /morkit:setup first — the docs-hero venv is missing."; exit 1; }

MODEL="<--model, e.g. morkit/output/greenfield/<proj>/project-model.json>"
LANG="<JP|EN|VN — ask the user>"
WS="morkit/output/jira/${JIRA_PROJECT_KEY:?set it first}"   # never leave WS empty
```

`WS` must be a real subdirectory. The scripts refuse to write their `*` .gitignore
into a repository root, so an unset `WS` fails loudly instead of making git ignore the
user's whole project — but do not lean on that.

**No system-python fallback.** It would ImportError on pydantic halfway through and
the message would make no sense to the user.

Settings live in `~/.config/morkit/jira.env` (0600), or in the real environment, which
wins. The scripts read the file **directly** — never `source` it into a shell — so the
token stays out of the command log, out of `ps aux`, and out of the shell history.

```bash
JIRA_BASE_URL=https://jira.company.com     # https only
JIRA_PROJECT_KEY=PROJ
JIRA_PAT=<personal access token>           # Jira 8.14+; older: JIRA_USER + JIRA_PASSWORD
JIRA_ISSUE_TYPE_STORY=Story                # override if the project has no "Story"
JIRA_ISSUE_TYPE_TASK=Task
```

The config file is **refused**, not repaired, if it is world-readable, sits inside a
git repository, or carries non-`JIRA_*` secrets. Report the problem and let the user
fix it — a credential in the wrong place is something they need to know about.

## Hard rules (NON-NEGOTIABLE)

1. **The gate belongs to the human.** You write `task-breakdown.md` with
   `status: draft` and never touch that line again — not with Edit, not with `sed`,
   not by re-rendering. "I approved it" in chat does not count; the file must say
   `approved`, and the human must be the one who put it there.

   Be clear-eyed about why this rule matters: `push_jira.py` checks the file's
   *contents*, and it cannot check *who wrote them*. You have Bash. One
   `sed -i 's/draft/approved/'` would pass every check in the system. Nothing stops
   you except this rule, so the rule is the enforcement, not a reminder about it.
2. **Never invent ticket content.** The SRS already holds it. A missing field means
   no section — not "TBD", not "N/A", not a sentence you wrote.
3. **Never call Jira directly.** No `curl`, no MCP, no Bash HTTP. Every request goes
   through `jira_client.py`. If a script breaks, report it — do not route around it.
4. **Never close or delete a ticket.** ORPHAN and DEPRECATED rows are reported to the
   human and left alone.
5. **Never print the token, and never ask for it.** Not in chat, not in a report, not
   in a log, not as an `AskUserQuestion`. A token typed into chat is in the transcript
   on disk for good — storing it carefully afterwards is theatre. The user writes it
   into their own file; you only ever read it. Base URL and project key are fine to ask
   about; they are not secrets.
6. **Speak plainly.** The user is a BrSE, not a Python developer. Say "60 tickets, 3
   need a decision", not file paths and JSON.

## Workflow

Workspace: `morkit/output/jira/<PROJECT_KEY>/`.

### 0 — Config gate (guide, do not just fail)

```bash
"$PY" "$SKILL_DIR/scripts/jira_config.py" check
```
Prints what is set and what is missing. **Never prints a value** — safe to show.

**If `ok: false`**, do not raise an error at the user and stop. Walk them through it:

1. **Ask in chat** for `JIRA_BASE_URL` and `JIRA_PROJECT_KEY`. Neither is a secret.
2. **Never ask for the token.** Typing it into chat writes it into the transcript
   permanently. Instead, tell them how to mint one and how to store it — and say both
   of these while they are on the token screen, because that is the only moment they
   can act on them:
   - Jira → avatar → **Profile** → **Personal Access Tokens** → **Create token**
   - **Use a service account with rights to this project only.** A Jira Server PAT
     inherits *all* the permissions of whoever made it — a personal token can read and
     rewrite every ticket in every project they can see. Scope is what turns a leaked
     token from a disaster into an inconvenience.
   - **Set an expiry.** A 90-day token that leaks has a 90-day blast radius. A
     permanent one has a permanent radius.
3. Give them this to paste into **their own terminal** (not into chat). `read -rs`
   means the token never appears on screen and never enters their shell history:
   ```bash
   mkdir -p ~/.config/morkit && chmod 700 ~/.config/morkit
   read -rs -p "Paste the Jira token (it will not echo): " T && \
     printf 'export JIRA_BASE_URL=%s\nexport JIRA_PROJECT_KEY=%s\nexport JIRA_PAT=%s\n' \
       '<base-url>' '<PROJECT>' "$T" > ~/.config/morkit/jira.env && \
     unset T && chmod 600 ~/.config/morkit/jira.env && echo "saved"
   ```
4. Wait. When they say it is done, run `jira_config.py check` again and carry on.

**If the file is refused** (world-readable, inside a git repo, holds other secrets):
report exactly what the check said and **let them fix it**. Do not `chmod` or `mv` it
for them.

### 1 — Resolve the run
`--model` (required) and `--lang` (JP/EN/VN — **ask if unset**; it decides the language
of the ticket headings, and a Japanese client should not get Vietnamese ones). Confirm
the project key with the user before anything else.

### 2 — Preflight (BEFORE the reviewer reads anything)
```bash
"$PY" "$SKILL_DIR/scripts/build_tasks.py" --model "$MODEL" --lang "$LANG" \
    --out "$WS/tasks.json" [--skip-nfr]
"$PY" "$SKILL_DIR/scripts/preflight_check.py" --tasks "$WS/tasks.json"
```
On `ok: false`, **stop and fix it**. A Kanban project usually has `Task` and `Bug`
and no `Story`; discovering that after someone spent an hour reviewing sixty rows is
the wrong time.

### 3 — Render the breakdown
```bash
"$PY" "$SKILL_DIR/scripts/render_breakdown.py" \
    --tasks "$WS/tasks.json" --map "$WS/jira-map.json" --out "$WS/task-breakdown.md" \
    --project "$JIRA_PROJECT_KEY" --base-url "$JIRA_BASE_URL" --workspace "$WS"
```
Show the user: how many will be created, how many updated, how many unchanged, and
**every ⚠ row** — those are requirements still carrying a `<TBD:>` or missing a
metric. Suggest fixing the SRS rather than shipping a thin ticket.

### 4 — The human signs it
Ask them to open `$WS/task-breakdown.md`, edit Summary/Priority in the table, untick
anything they want held back, and change `status: draft` → `status: approved`
themselves. Then wait. Re-read the file; if it still says draft, say so and wait
again. **Never edit that line for them.**

### 5 — Push
```bash
"$PY" "$SKILL_DIR/scripts/push_jira.py" \
    --breakdown "$WS/task-breakdown.md" --tasks "$WS/tasks.json" \
    --map "$WS/jira-map.json" --workspace "$WS" [--dry-run]
```

| Flag | When |
|---|---|
| `--dry-run` | Preflight and diff, send nothing. Offer this first if they are nervous. |
| `--offline` | No network at all. The rehearsal path, and the only one that works with no token. |
| `--force` | Update a ticket even though someone edited it on Jira since. **Ask the user first** — it overwrites their team's work. |
| `--recover` | Only when `jira-map.json` is genuinely lost. Rebuilds it from the issue labels. Refuses to run if the ledger is still there. |

### 6 — Report
Keys created/updated, rows held back, and the ORPHAN/DEPRECATED list — those are
issues on Jira the SRS no longer describes, and **only the user** decides whether to
close them. Say it in their language, in plain words.

## Re-running is safe

`jira-map.json` records which requirement became which issue. A second run **writes
nothing**: unchanged requirements are skipped, changed ones are updated, and the
signature is retired once a push succeeds. (Preflight still makes three read-only
calls — "no writes", not "no requests".)

A reviewer's hand-edited summary survives future runs. The ledger keeps the SRS hash
and the text that was actually sent apart, precisely so that an unchanged SRS never
"corrects" a human's wording back to the machine's.

If `jira-map.json` is ever lost, `--recover` rebuilds it from the `morkit-id-*` labels
on the issues rather than creating a second backlog.

## Files
- `scripts/jira_config.py` — where the credential lives, and the checks it must pass
- `scripts/build_tasks.py` — model → `tasks.json` (mechanical render; no LLM in the loop)
- `scripts/preflight_check.py` — verify the Jira target. `--tasks` optional: with none,
  it is a plain "does my connection work" check, which is what a first-time setup needs
- `scripts/render_breakdown.py` — `tasks.json` + ledger → the file the human signs
- `scripts/push_jira.py` — the only script that writes to Jira
- `references/tasks-schema.json` — the `tasks.json` contract

## Workflow position
Follows `/morkit:greenfield` (G7) or any `/morkit:init` run that produced a model.
Not part of the docs pipeline — it consumes its output.
