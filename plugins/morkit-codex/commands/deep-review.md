---
name: "morkit:deep-review"
description: Run a deep multi-agent code review on a PR or git diff. Produces a Markdown matrix report with risk, security, design pattern, test coverage, and convention findings.
category: Code Review
tags: [code-review, security, risk, pattern, tests]
---

Invoke the `deep-review` skill. Pass through any arguments the user provided as `<target>`:

- `/morkit:deep-review 123` → review PR #123
- `/morkit:deep-review #123` → review PR #123
- `/morkit:deep-review --diff` → review uncommitted changes vs HEAD
- `/morkit:deep-review --diff main` → review HEAD vs main
- `/morkit:deep-review` → defaults to `--diff`
- `/morkit:deep-review --json` → emit JSON instead of Markdown (CI/CD mode)

The skill orchestrates 5 parallel subagents and prints a full Markdown report directly to chat. It also saves a copy under `morkit/output/reviews/` if the directory is writable.

## First-time on a repo (no graph yet)

The skill performs a **pre-flight check** before dispatching specialists:

| Repo size | Behavior |
|-----------|----------|
| < 1500 files | Auto-build the graph silently with a one-line progress message (~10–40s). |
| 1500–8000 files | Ask: "Build now? (y/N/skip)". Skip → degraded mode. |
| > 8000 files | Strong warning + same prompt. Build is 1-time; incremental updates after are < 2s. |

If `gh` is missing for a PR target, the skill exits with installation instructions.
If the code-review-graph MCP is unavailable or the user declines build, the skill runs in **degraded mode** (graph-dependent findings fall back to grep with reduced confidence) and notes this in the report header.
