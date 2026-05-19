---
name: "morkit:deep-review-doctor"
description: Diagnose Deep Review installation health (uvx, code-review-graph, gh, git, graph build, CLAUDE.md presence).
category: Code Review
tags: [diagnostic, doctor, health-check]
---

Run the bundled `${CLAUDE_PLUGIN_ROOT}/scripts/doctor.sh` via Bash and stream its output to chat. Then summarize:
- Required components (git, uvx) — ok/missing
- Recommended (gh) — ok/missing
- Code graph status for current repo
- Whether a project CLAUDE.md is present (Tier-1 conventions)

If anything required is missing, propose the exact install command.
