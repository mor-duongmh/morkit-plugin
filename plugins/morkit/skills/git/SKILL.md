---
name: git
description: "Use when the user asks to commit, push, create a PR, or merge branches. Handles conventional commits, secret scanning, and auto-splits commits by type/scope."
category: dev-tools
keywords: [git, commits, staging, PR, merge]
argument-hint: "cm|cp|pr|merge [args]"
---

# Git Operations

## Safety Rules (always apply)

These rules apply on **every** platform, whether or not the `git-manager` subagent is loaded:

- **Confirm before any destructive op** — push, force-push, `reset --hard`, `checkout -- <file>`, branch delete, or merge into a protected branch (`main`, `master`, `production`, `prod`, `release/*`). Confirm via `AskUserQuestion` on Claude Code; on platforms without it (e.g. Codex — see `using-morkit/references/codex-tools.md`), ask the user inline in plain text and **wait for a reply**. Never skip the confirmation.
- **No unsolicited pushes or force operations** — only perform git actions the user explicitly requested.
- **Always run the secret scan before staging** (Step 1). Block on any match.

## Default (No Arguments)

If invoked without arguments, use `AskUserQuestion` (or, on platforms without it, a plain-text prompt) to present available git operations:

| Operation | Description |
|-----------|-------------|
| `cm` | Stage files & create commits |
| `cp` | Stage files, create commits and push |
| `pr` | Create Pull Request |
| `merge` | Merge branches |

Present as options via `AskUserQuestion` with header "Git Operation", question "What would you like to do?".

Execute git workflows via the `git-manager` subagent to isolate verbose output.

**Platform note (delegation):** if your platform has no named-agent registry (e.g. Codex — its plugin system does not yet load the `agents/` directory), do **not** try to spawn `git-manager`. Instead read `agents/git-manager.md`, apply its safety rules (also listed above), and run the workflow inline. See `using-morkit/references/codex-tools.md` → "Named agent dispatch".

**IMPORTANT:**
- Sacrifice grammar for the sake of concision.
- Ensure token efficiency — pass minimal context to subagent.
- Never chain subagent calls back to this skill (delegation loop).

## Arguments
- `cm`: Stage files & create commits
- `cp`: Stage files, create commits and push
- `pr`: Create Pull Request [to-branch] [from-branch]
  - `to-branch`: Target branch (default: main)
  - `from-branch`: Source branch (default: current branch)
- `merge`: Merge [to-branch] [from-branch]
  - `to-branch`: Target branch — **required, no default**
  - `from-branch`: Source branch (default: current branch)

## Quick Reference

| Task | Reference |
|------|-----------|
| Commit | `references/workflow-commit.md` |
| Push | `references/workflow-push.md` |
| Pull Request | `references/workflow-pr.md` |
| Merge | `references/workflow-merge.md` |
| Standards | `references/commit-standards.md` |
| Safety | `references/safety-protocols.md` |
| Branches | `references/branch-management.md` |
| GitHub CLI | `references/gh-cli-guide.md` |

## Core Workflow

### Step 1: Pre-stage Security Check

Run before staging anything — see `references/workflow-commit.md` for the full check.

Check file names for secrets:
```bash
git status --short | awk '/^\?\? /{print $2}' | grep -iE '(\.env($|\.[^.]+$)|\.pem$|\.key$|\.p12$|credentials\.json|secrets\.json)'
```

Check content for secret patterns (strong regex from `references/safety-protocols.md`):
```bash
git diff | grep -iE "(AKIA[0-9A-Z]{16}|api[_-]?key|token|password|secret|credential|private[_-]?key|mongodb://|postgres://|mysql://|redis://|-----BEGIN|client_secret|oauth_token)"
```

**If either check matches:** STOP, warn user, suggest `.gitignore`. Do not proceed.

### Step 2: Stage + Analyze

Use specific files when possible; avoid `git add -A`:
```bash
git diff --cached --stat && git diff --cached --name-only
```

### Step 3: Split Decision

See `references/workflow-commit.md` for full logic. Summary:
- Single commit: same type/scope, ≤ 3 files, ≤ 50 lines
- Multi commit: mixed types/scopes — group by config/deps/test/code/docs

### Step 4: Commit
```bash
git commit -m "type(scope): description"
```

## Output Format
```
✓ staged: N files (+X/-Y lines)
✓ security: passed
✓ commit: HASH type(scope): description
✓ pushed: yes/no
```

## Error Handling

| Error | Action |
|-------|--------|
| Secrets detected | Block commit, show files |
| No changes | Exit cleanly |
| Push rejected | Suggest `git pull --rebase` |
| Merge conflicts | Suggest manual resolution |

## References

- `references/workflow-commit.md` - Commit workflow with split logic
- `references/workflow-push.md` - Push workflow with error handling
- `references/workflow-pr.md` - PR creation with remote diff analysis
- `references/workflow-merge.md` - Branch merge workflow
- `references/commit-standards.md` - Conventional commit format rules
- `references/safety-protocols.md` - Secret detection (canonical regex), branch protection
- `references/branch-management.md` - Naming, lifecycle, strategies
- `references/gh-cli-guide.md` - GitHub CLI commands reference
