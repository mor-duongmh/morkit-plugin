# Commit Workflow

Execute via `git-manager` subagent.

## Tool 1: Pre-stage Security Check

**BEFORE staging anything**, check for sensitive file names:
```bash
git status --short | awk '/^\?\? /{print $2}' | grep -iE '(\.env($|\.[^.]+$)|\.pem$|\.key$|\.p12$|credentials\.json|secrets\.json|private.*\.json)'
```

**If any sensitive files found:** STOP immediately. Warn user, suggest adding to `.gitignore`. Do NOT proceed with staging.

Then check tracked modified files for secret patterns:
```bash
git diff | grep -iE "(AKIA[0-9A-Z]{16}|api[_-]?key|token|password|secret|credential|private[_-]?key|mongodb://|postgres://|mysql://|redis://|-----BEGIN|client_secret|oauth_token)"
```

**If matches found:** STOP, show matching lines, block staging.

## Tool 2: Stage + Analyze

Stage only after security check passes. Use specific files when possible; avoid `git add -A`:
```bash
git add <files> && \
echo "=== STAGED ===" && git diff --cached --stat && \
echo "=== GROUPS ===" && \
git diff --cached --name-only | awk -F'/' '{
  if ($0 ~ /\.(md|txt)$/) print "docs:"$0
  else if ($0 ~ /test|spec/) print "test:"$0
  else if ($0 ~ /\.claude|plugins\//) print "config:"$0
  else if ($0 ~ /package\.json|lock/) print "deps:"$0
  else print "code:"$0
}'
```

If `git add -A` is unavoidable, run the full security scan again on staged diff before continuing.

## Tool 3: Split Decision

**From groups, decide:**

**A) Single commit:** Same type/scope, FILES ≤ 3, LINES ≤ 50

**B) Multi commit:** Mixed types/scopes, group by:
- Group 1: `config:` → `chore(config): ...`
- Group 2: `deps:` → `chore(deps): ...`
- Group 3: `test:` → `test: ...`
- Group 4: `code:` → `feat|fix: ...`
- Group 5: `docs:` → `docs: ...`

See `commit-standards.md` for type rules.

## Tool 4: Commit

**Single:**
```bash
git commit -m "type(scope): description"
```

**Multi (sequential):**
```bash
git reset && git add file1 file2 && git commit -m "type(scope): desc"
```
Repeat for each group.

## Tool 5: Push (if requested)

**Only push if user explicitly requested** ("push", "commit and push"):
```bash
git push && echo "✓ pushed: yes" || echo "✓ pushed: no"
```
