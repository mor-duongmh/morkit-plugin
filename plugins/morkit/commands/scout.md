---
name: "morkit:scout"
description: Fast codebase scouting — spawn parallel Explore agents to locate the files a task needs and return a concise report, without loading file contents into the main context.
category: Workflow
tags: [scout, codebase, file-discovery, search, parallel]
argument-hint: "<search-target>"
---

Invoke the `scout` skill using the Skill tool. Pass through any arguments the user provided.

Args:
- `<search-target>` (optional) — what to find (a feature, symbol, concern, or "where does X live")

The skill will:
- Parse the search target and estimate the scale of the codebase with Grep/Glob.
- Split the directory tree into non-overlapping slices and dispatch one `Explore` agent per slice in parallel (reusing the `dispatching-parallel-agents` pattern).
- Collect each agent's findings, deduplicate paths, and return a single Scout Report (relevant files + patterns + unresolved questions).
- Keep file contents in the sub-agents' context — only paths and one-line descriptions reach the main context.

**Usage:**
```
/morkit:scout authentication flow      # find auth-related files across the repo
/morkit:scout where is the SRS rendered # locate a feature you don't know the home of
```
