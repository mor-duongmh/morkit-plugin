---
updated: <YYYY-MM-DD>
status: draft
---

# Code Standards

> If a project-level `CONTRIBUTING.md` exists, this doc links to it for topics already covered there — it does not duplicate.

---

## Languages & Tooling

<!-- hint: fill from detected package manifests and config files -->

| Language | Linter | Formatter | Test Runner |
|---|---|---|---|
| <e.g. TypeScript> | <e.g. ESLint> | <e.g. Prettier> | <e.g. Vitest> |
| <placeholder> | <placeholder> | <placeholder> | <placeholder> |

---

## Formatting Rules

<!-- hint: auto-extract from .prettierrc / .editorconfig / pyproject.toml / etc. -->

| ID | Tool | Option | Value | Source |
|---|---|---|---|---|
| FMT-001 | <e.g. Prettier> | <e.g. printWidth> | <e.g. 100> | <e.g. .prettierrc> |
| FMT-002 | <e.g. Prettier> | <e.g. singleQuote> | <e.g. true> | <e.g. .prettierrc> |
| FMT-003 | <placeholder> | <placeholder> | <placeholder> | <placeholder> |

---

## Naming Conventions

| ID | Scope | Pattern | Example |
|---|---|---|---|
| NAM-001 | file | `kebab-case` | `user-service.ts` |
| NAM-002 | class | `PascalCase` | `UserService` |
| NAM-003 | function / method | `camelCase` | `getUser()` |
| NAM-004 | constant | `UPPER_SNAKE` | `MAX_RETRIES` |
| NAM-005 | <placeholder scope> | <placeholder> | <placeholder> |

---

## Lint Configuration

<!-- hint: list detected lint configs; do not resolve extends chains -->

| ID | Tool | Config Path | Extends |
|---|---|---|---|
| LNT-001 | <e.g. ESLint> | <e.g. .eslintrc.js> | <e.g. eslint:recommended> |
| LNT-002 | <placeholder> | <placeholder> | — |

---

## Commit Convention

<!-- hint: default is Conventional Commits; override if project uses something else -->

```text
<type>(<scope>): <short summary>

<body — optional>

<footer — optional, e.g. BREAKING CHANGE or issue ref>
```

| ID | Style | Allowed Types | Scope Required |
|---|---|---|---|
| CMT-001 | conventional | feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert | No |

---

## Branch & PR Rules

<!-- hint: adjust merge strategy to match repo settings -->

- Branch naming: `<type>/<short-desc>` — e.g. `feat/user-auth`, `fix/null-check`
- PR title: matches squash-commit format above
- Merge strategy: `<squash | merge | rebase>` to `<main | master>`
- Minimum reviewers: `<N>`
- Force-push: forbidden on shared branches

---

## Pre-commit Hooks

<!-- hint: detect from .husky/, .pre-commit-config.yaml, lefthook.yml, etc. -->

| Hook | Tool | What It Runs |
|---|---|---|
| pre-commit | <e.g. Husky> | <e.g. lint-staged → ESLint + Prettier> |
| commit-msg | <e.g. Husky> | <e.g. commitlint> |
| <placeholder> | <placeholder> | <placeholder> |
