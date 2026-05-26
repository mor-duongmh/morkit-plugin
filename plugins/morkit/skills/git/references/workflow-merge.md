# Merge Workflow

Execute via `git-manager` subagent.

## Variables
- TO_BRANCH: target — **must be provided explicitly; no default**
- FROM_BRANCH: source (defaults to current branch)

> **⚠️ Warning:** Never merge directly into a protected branch (main, master, production, release/*) without confirmation. Prefer creating a PR instead.

## Step 0: Confirm intent

If TO_BRANCH is a protected branch (`main`, `master`, `production`, `prod`, `release/*`):
- Use `AskUserQuestion` to confirm: "You are about to merge into a protected branch. Proceed with direct merge, or create a PR instead?"
- Default to creating a PR via `workflow-pr.md`.

## Step 1: Validate branches

Reject TO_BRANCH if it contains unsafe characters (`;`, `|`, `$`, backtick, space):
```bash
echo "$TO_BRANCH" | grep -qE '^[A-Za-z0-9._/-]+$' || { echo "Invalid branch name"; exit 1; }
```

## Step 2: Sync with Remote

```bash
git fetch origin
git checkout "$TO_BRANCH"
git pull origin "$TO_BRANCH"
```

## Step 3: Merge from REMOTE

```bash
git merge "origin/$FROM_BRANCH" --no-ff -m "merge: $FROM_BRANCH into $TO_BRANCH"
```

**Why `origin/$FROM_BRANCH`:** Ensures merging only committed+pushed changes, not local WIP.

## Step 4: Resolve Conflicts
If conflicts:
1. Resolve manually
2. `git add . && git commit`
3. If clarifications needed, report to main agent

## Step 5: Push

**Confirm with user before pushing to any protected branch.**

```bash
git push origin "$TO_BRANCH"
```

## Pre-Merge Checklist
- Fetch latest: `git fetch origin`
- Ensure FROM_BRANCH pushed to remote
- Check for conflicts: `git merge --no-commit --no-ff "origin/$FROM_BRANCH"` then abort

## Error Handling

| Error | Action |
|-------|--------|
| Merge conflicts | Resolve manually, then commit |
| Branch not found | Verify branch name, ensure pushed |
| Push rejected | `git pull --rebase`, retry |
