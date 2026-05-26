---
name: "morkit:git"
description: Git operations with conventional commits — stage, commit, push, PR, merge. Delegates to git-manager subagent.
category: Dev Tools
tags: [git, commits, PR, merge]
---

Invoke the `git` skill using the Skill tool. Pass through any arguments the user provided.

Supported operations:
- `cm` — Stage files & create commits
- `cp` — Stage files, commit and push
- `pr [to-branch] [from-branch]` — Create Pull Request
- `merge [to-branch] [from-branch]` — Merge branches

If no argument is given, the skill presents an interactive menu via `AskUserQuestion`.
