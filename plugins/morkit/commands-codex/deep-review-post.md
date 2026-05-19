---
name: "morkit:deep-review-post"
description: Post the latest deep-review report as a PR comment via `gh pr comment` (does not request changes; user retains decision).
category: Code Review
tags: [post, gh, pr]
---

Behavior:

1. Resolve target PR: argument `<pr-number>` or auto-detect from current branch via `gh pr view --json number -q .number`.
2. Locate the latest report under `morkit/output/reviews/deep-review-<timestamp>-<target>.md`. If multiple, prefer matching `<target>`.
3. Show the user the first 30 lines of the report and ask: **"Post this report to PR #<n>? (y/N)"**.
4. On `y`, run:
   ```bash
   gh pr comment <n> --body-file morkit/output/reviews/<file>.md
   ```
5. Print the resulting comment URL.

Never use `gh pr review --request-changes` or `--approve`. The plugin only **comments**; the human decides.
