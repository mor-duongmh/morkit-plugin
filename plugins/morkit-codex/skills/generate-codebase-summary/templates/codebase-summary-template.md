<!--
Codebase Summary Template — README-style overview
Format: Markdown, hỗ trợ JP / EN / VN
Source: ProjectModel (repo_overview / tech_stack / packages / modules) +
        codebase scan via parse_codebase_tree.py.
Numbering: RPO-001 (singleton), TCH-001 (TechStackItem),
           PKG-001 (PackageInfo), MOD-001 (ModuleEntry)
-->

# Codebase Summary — {{PROJECT_NAME}}

| Field | Value |
|---|---|
| Project | {{PROJECT_NAME}} |
| Version | {{VERSION}} |
| Date | {{DATE}} |
| Language | {{LANG}} |

> LOC counts are **approximate** (pure-Python line counter, no `cloc` dependency).

---

## 1. What is this repo

{{REPO_DESCRIPTION}}

| Field | Value |
|---|---|
| Primary language | _TBD_ |
| Total LOC (approx) | _TBD_ |
| VCS | git |
| License | _TBD_ |

---

## 2. Tech Stack

Grouped by category. `confidence: detected` = inferred from manifest;
`declared` = present in user-provided ProjectModel.

### Languages
| ID | Name | Version | Confidence |
|---|---|---|---|
| TCH-001 | _TBD_ | - | detected |

### Frameworks
| ID | Name | Version | Confidence |
|---|---|---|---|

### Databases
| ID | Name | Version | Confidence |
|---|---|---|---|

### Infra / CI / Test / Build
| ID | Category | Name | Version |
|---|---|---|---|

---

## 3. Repository Layout

Depth-3 tree (auto-generated; `node_modules` / `.venv` / `dist` / `build` /
`.git` excluded).

```
.
├── (top-level dirs)
└── (...)
```

---

## 4. Packages / Workspaces

| ID | Name | Path | Manager | Version | Deps |
|---|---|---|---|---|---|
| PKG-001 | _TBD_ | _TBD_ | npm | - | 0 |

---

## 5. Entry Points

Files marked as program entry points (e.g. `main.py`, `index.ts`, `cmd/*`,
`bin/*`, `pyproject [project.scripts]`).

| ID | Path | Language | LOC | Purpose |
|---|---|---|---|---|
| MOD-001 | _TBD_ | _TBD_ | 0 | _TBD_ |

---

## 6. LOC by Language

| Language | Files | LOC (approx) | % |
|---|---|---|---|
| _TBD_ | 0 | 0 | 0% |

---

## 7. Build & Run quickstart

Detected commands (from `package.json` scripts / `Makefile` / `justfile` /
`pyproject [tool.poetry.scripts]`):

```bash
# _TBD_ — fill from detected build files
```

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | {{DATE}} | morkit (auto) | Initial generation |
