# Git Safety Protocols

## Secret Detection Patterns

### Scan Command (canonical — use this regex everywhere)
```bash
git diff --cached | grep -iE "(AKIA[0-9A-Z]{16}|api[_-]?key|token|password|secret|credential|private[_-]?key|mongodb://|postgres://|mysql://|redis://|-----BEGIN|client_secret|oauth_token)"
```

### Patterns to Detect

| Category | Pattern | Example |
|----------|---------|---------|
| API Keys | `api[_-]?key`, `apiKey` | `API_KEY=abc123` |
| AWS | `AKIA[0-9A-Z]{16}` | `AKIAIOSFODNN7EXAMPLE` |
| Tokens | `token`, `auth_token`, `jwt` | `AUTH_TOKEN=xyz` |
| Passwords | `password`, `passwd`, `pwd` | `DB_PASSWORD=secret` |
| Private Keys | `-----BEGIN PRIVATE KEY-----` | PEM files |
| DB URLs | `mongodb://`, `postgres://`, `mysql://` | Connection strings |
| OAuth | `client_secret`, `oauth_token` | `CLIENT_SECRET=abc` |

### Files to Warn About
- `.env`, `.env.*` (except `.env.example`)
- `*.key`, `*.pem`, `*.p12`
- `credentials.json`, `secrets.json`
- `config/private.*`

### Action on Detection
1. **BLOCK commit immediately**
2. Show matching lines: `git diff --cached | grep -B2 -A2 <pattern>`
3. Suggest: "Add to .gitignore or use environment variables"
4. Offer to unstage: `git reset HEAD <file>`

## Branch Protection

### Never Force Push To
- `main`, `master`, `production`, `prod`, `release/*`

### Pre-Merge Checks
```bash
# Check for conflicts before merge
git merge --no-commit --no-ff origin/{branch} && git merge --abort
```

### Remote-First Operations
Always use `origin/{branch}` for comparisons:
- ✅ `git diff origin/main...origin/feature`
- ❌ `git diff main...HEAD` (includes local uncommitted)

## Environment Detection (sandbox / worktree)

Before any `push`, `pr`, or `merge`, detect the environment with read-only git commands:

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

- `GIT_DIR != GIT_COMMON` → already inside a linked worktree.
- `BRANCH` empty → **detached HEAD** (common in a Codex App sandbox) → cannot branch/push/PR.

**If the sandbox blocks push/branch** (detached HEAD in an externally managed worktree): commit the work locally, then tell the user to use the host App's native controls ("Create branch" / "Hand off to local"). Still output suggested branch name, commit message, and PR body for the user to copy. See `using-morkit/references/codex-tools.md` → "Codex App Finishing".

## Error Recovery

### Undo Last Commit (unpushed)
```bash
git reset --soft HEAD~1  # Keep changes staged
git reset HEAD~1         # Keep changes unstaged
```

### Abort Merge
```bash
git merge --abort
```

### Discard Local Changes

**MANDATORY: Confirm before running any of the commands below.** Use `AskUserQuestion` on Claude Code; on platforms without it (e.g. Codex — see `using-morkit/references/codex-tools.md`), ask the user inline and wait for a reply.

```bash
git checkout -- <file>   # Single file — CONFIRM FIRST
git reset --hard HEAD    # All files (DANGER) — CONFIRM FIRST
```

Also require confirmation before:
- `git push --force` / `git push -f` on any branch
- `git branch -D <branch>` (force-delete local branch)
- `git push origin --delete <branch>` (delete remote branch)
