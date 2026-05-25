---
updated: <YYYY-MM-DD>
status: draft
---

# Document Map

> This doc is the entry point for this project/module. It holds read paths and canonical source
> rules. For scope boundaries see [SCOPE](SCOPE.md); for file-to-code mapping see
> [SOURCE-MAP](SOURCE-MAP.md).

<!-- hint: One sentence describing what this project/module provides. -->
<placeholder: e.g. "This module provides X for Y via Z.">

## Directory Roles

<!-- hint: One row per folder that was generated. Remove rows for absent folders. -->

| Directory | Role |
|---|---|
| `00-overview/` | Entry docs: navigation, scope, source map, dependency map, glossary, stack |
| `10-requirements/` | Feature catalog (WHAT) and user-facing flows |
| `20-design/` | Architecture, per-feature specs, data/API/UI maps, ADRs |
| `30-test/` | Test strategy, runbook, traceability matrix |
| `40-ai-coding/` | Guides optimized for AI agents: coding guide, pitfalls, change playbooks |
| `90-operations/` | Local runbook and troubleshooting |

## Read Paths

<!-- hint: Each task is a common reason a developer/agent opens these docs. -->
<!-- hint: List files in the order they should be read for that task. -->
<!-- hint: Include at least 3 tasks. Rename tasks to match this project's actual features. -->

### Understand The Project

1. `00-overview/SCOPE.md`
2. `00-overview/SOURCE-MAP.md`
3. `20-design/00-core/ARCHITECTURE.md`

### Change <Feature A>

<!-- hint: Replace <Feature A> with an actual feature name (e.g. "the User List"). -->

1. `20-design/10-features/<FEATURE-A>-SYS-SPEC.md`
2. `20-design/30-api/API-MAP.md` <!-- hint: include only if API-MAP was generated -->
3. `20-design/20-data/DATA-MAP.md` <!-- hint: include only if DATA-MAP was generated -->
4. `40-ai-coding/COMMON-CHANGE-PLAYBOOKS.md`
5. `30-test/TEST-RUNBOOK.md`

### Change <Feature B>

<!-- hint: Replace <Feature B> with a second feature. -->

1. `20-design/10-features/<FEATURE-B>-SYS-SPEC.md`
2. `20-design/20-data/DATA-MAP.md`
3. `40-ai-coding/AI-CODING-GUIDE.md`
4. `30-test/TEST-RUNBOOK.md`

### Investigate <Cross-Cutting Concern>

<!-- hint: e.g. "Investigate Legacy Endpoints", "Debug Export Failures". -->

1. `20-design/10-features/<CONCERN>-SYS-SPEC.md`
2. `40-ai-coding/RISK-REGISTER.md`
3. `40-ai-coding/KNOWN-PITFALLS.md`

## Canonical Source Rules

<!-- hint: Identify the single source of truth for the most-changed concerns. -->
<!-- hint: Format: "- <concern>: `path/to/file`" — one line per concern. -->
<!-- hint: e.g. "- Route truth: `src/router/index.ts`" -->

- <placeholder concern>: `<path/to/canonical/file>`
- <placeholder concern>: `<path/to/canonical/file>`
- <placeholder concern>: `<path/to/canonical/file>`
