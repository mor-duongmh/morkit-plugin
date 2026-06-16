---
updated: <YYYY-MM-DD>
status: draft
source_files: ["package.json", "pyproject.toml", "<other manifest glob>"]
---

# Stack

> This doc holds the tech stack, repo layout, and entry points.
> For build/run commands see [LOCAL-RUNBOOK](../90-operations/LOCAL-RUNBOOK.md).
> For detailed file-to-concern mapping see [SOURCE-MAP](SOURCE-MAP.md).

## What Is This

<!-- hint: 2-3 sentences: what the project does, who uses it, deployment target. -->
<!-- hint: e.g. "A multi-tenant SaaS API built with FastAPI, backed by PostgreSQL,
     deployed on AWS ECS. Used by operations staff via a React SPA." -->

<placeholder: project description>

| Field | Value |
|---|---|
| Primary language | <placeholder: e.g. TypeScript> |
| Total LOC (approx) | <placeholder: e.g. 18 000> |
| VCS | git |
| License | <placeholder: e.g. MIT / proprietary> |

## Tech Stack

### Languages

| ID | Name | Version | Confidence |
|---|---|---|---|
| TCH-001 | <placeholder: e.g. TypeScript> | <placeholder: e.g. 5.x> | detected |
| TCH-002 | <placeholder: e.g. Python> | <placeholder: e.g. 3.12> | detected |

### Frameworks

| ID | Name | Version | Confidence |
|---|---|---|---|
| TCH-010 | <placeholder: e.g. Next.js> | <placeholder: e.g. 14> | detected |
| TCH-011 | <placeholder: e.g. FastAPI> | <placeholder: e.g. 0.110> | detected |

### Databases

| ID | Name | Version | Confidence |
|---|---|---|---|
| TCH-020 | <placeholder: e.g. PostgreSQL> | <placeholder: e.g. 15> | detected |
| TCH-021 | <placeholder: e.g. Redis> | <placeholder: e.g. 7> | detected |

### Infra / CI / Build

| ID | Category | Name | Version |
|---|---|---|---|
| TCH-030 | CI | <placeholder: e.g. GitHub Actions> | — |
| TCH-031 | Container | <placeholder: e.g. Docker> | <placeholder: e.g. 24> |
| TCH-032 | Build | <placeholder: e.g. Vite> | <placeholder: e.g. 5> |

<!-- hint: Remove rows for categories not present. Add rows as scout detects more tools. -->

## Repository Layout

<!-- hint: Depth-2 or depth-3 tree. Exclude node_modules, .venv, dist, build, .git. -->
<!-- hint: Annotate key directories with a short comment. -->

```text
.
├── src/               <!-- hint: main application source -->
│   ├── api/           <!-- hint: route handlers / controllers -->
│   ├── services/      <!-- hint: business logic -->
│   ├── models/        <!-- hint: data models / entities -->
│   └── utils/         <!-- hint: shared utilities -->
├── tests/             <!-- hint: test suites -->
├── docs/              <!-- hint: this documentation tree -->
├── <placeholder>/     <!-- hint: add project-specific top-level dirs -->
└── <manifest files>   <!-- hint: e.g. package.json, pyproject.toml, Makefile -->
```

## Packages / Workspaces

<!-- hint: For monorepos list each workspace/package. For single-package repos, one row. -->
<!-- hint: PKG-### IDs are optional; use them only if cross-referenced elsewhere. -->

| ID | Name | Path | Manager | Version | Deps |
|---|---|---|---|---|---|
| PKG-001 | <placeholder: package name> | <placeholder: ./apps/web> | <placeholder: npm/pnpm/pip> | — | 0 |

<!-- hint: Remove the ID column if IDs are not used elsewhere in the docs. -->

## Entry Points

<!-- hint: Files where execution begins: main.py, index.ts, cmd/*, bin/*, server.ts, etc. -->
<!-- hint: LOC is approximate. Purpose is one phrase. -->

| ID | Path | Language | LOC | Purpose |
|---|---|---|---|---|
| MOD-001 | <placeholder: e.g. src/index.ts> | <placeholder: TypeScript> | — | <placeholder: e.g. HTTP server bootstrap> |
| MOD-002 | <placeholder: e.g. src/worker.ts> | <placeholder: TypeScript> | — | <placeholder: e.g. Background job processor> |

## LOC by Language

<!-- hint: Approximate counts from `cloc` or equivalent. Fill after scout runs. -->

| Language | Files | LOC (approx) | % |
|---|---|---|---|
| <placeholder: TypeScript> | — | — | —% |
| <placeholder: Python> | — | — | —% |
| <placeholder: Other> | — | — | —% |
