<!--
Code Standards Template — Conventional Commits + auto-extracted style guide
Format: Markdown, hỗ trợ JP / EN / VN
Source: ProjectModel (lint_configs / naming_conventions / commit_policies /
        formatting_rules) + codebase scan via parse_codebase_lint.py.
Numbering: LNT-001 (LintConfig), NAM-001 (NamingConvention),
           CMT-001 (CommitPolicy), FMT-001 (FormattingRule)
-->

# Code Standards — {{PROJECT_NAME}}

| Field | Value |
|---|---|
| Project | {{PROJECT_NAME}} |
| Version | {{VERSION}} |
| Date | {{DATE}} |
| Language | {{LANG}} |

> If a project-level `CONTRIBUTING.md` exists, this document **links** to it
> for any topic already covered there — it does not duplicate.

---

## 1. Languages & Tooling

Primary languages and the lint/format toolchain detected.

| Language | Linter | Formatter | Test |
|---|---|---|---|
| _TBD_ | _TBD_ | _TBD_ | _TBD_ |

---

## 2. Formatting Rules

Auto-extracted from detected config files. Each row anchored to the source.

| ID | Tool | Option | Value | Source |
|---|---|---|---|---|
| FMT-001 | _TBD_ | _TBD_ | _TBD_ | _TBD_ |

---

## 3. Naming Conventions

| ID | Scope | Pattern | Example |
|---|---|---|---|
| NAM-001 | file | `kebab-case` | `user-service.ts` |
| NAM-002 | class | `PascalCase` | `UserService` |
| NAM-003 | function | `camelCase` | `getUser()` |
| NAM-004 | const | `UPPER_SNAKE` | `MAX_RETRIES` |

---

## 4. Lint Configuration

Detected lint configs. `extends` chains are listed verbatim and **not**
resolved (avoids needing dependency installs at scan time).

| ID | Tool | Config Path | Extends |
|---|---|---|---|
| LNT-001 | _TBD_ | _TBD_ | - |

---

## 5. Commit Convention

Default: [Conventional Commits](https://www.conventionalcommits.org/).

```
<type>(<scope>): <short summary>

<body>

<footer>
```

**Allowed types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
`build`, `ci`, `chore`, `revert`.

**Examples**:
- `feat(auth): add JWT refresh endpoint`
- `fix(db): null check on user lookup`
- `docs: update API examples`

| ID | Style | Allowed Types | Scope Required |
|---|---|---|---|
| CMT-001 | conventional | feat,fix,docs,style,refactor,perf,test,build,ci,chore,revert | No |

---

## 6. Branch & PR Rules

- **Branch naming**: `{type}/{short-desc}` (e.g. `feat/auth-jwt`, `fix/db-null-check`)
- **PR title**: matches the squash-commit format above
- **Merge strategy**: squash + merge to `main`
- **Review**: at least 1 reviewer; required CI checks must pass
- **Force-push**: forbidden on shared branches

---

## 7. Pre-commit Hooks

Detected hooks (e.g. via Husky / pre-commit / lefthook):

| Hook | Tool | What it runs |
|---|---|---|
| pre-commit | _TBD_ | _TBD_ |

---

## Appendix: Detected Config Paths

For human cross-reference. Listed paths are **not** parsed beyond what's
already summarized in §2 / §4.

| Tool | Path |
|---|---|
| _TBD_ | _TBD_ |

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | {{DATE}} | morkit (auto) | Initial generation |
