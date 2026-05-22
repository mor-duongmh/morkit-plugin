---
updated: <YYYY-MM-DD>
status: draft
---

# Design Map

> This doc is the navigation index for all design docs.
> For feature catalog see [10-requirements/FEATURE-LIST.md](../10-requirements/FEATURE-LIST.md).
> For codebase entry-points see [00-overview/SOURCE-MAP.md](../00-overview/SOURCE-MAP.md).

---

## Design Layers

<!-- hint: add rows only for sub-folders / docs that actually exist in this project -->
<!-- hint: conditional layers (20-data, 30-api, 40-ui) — create only when scout finds matching component -->

| Layer | Canonical Doc | Purpose |
|---|---|---|
| Architecture | [00-core/ARCHITECTURE.md](./00-core/ARCHITECTURE.md) | Components, layers, runtime structure, crosscutting concepts |
| Invariants | [00-core/INVARIANTS.md](./00-core/INVARIANTS.md) | Rules that must not be broken by any code change |
| <placeholder: feature name> | [10-features/<FEATURE>-SYS-SPEC.md](./10-features/<FEATURE>-SYS-SPEC.md) | <placeholder: one-line purpose> |
| <placeholder: feature name> | [10-features/<FEATURE>-SYS-SPEC.md](./10-features/<FEATURE>-SYS-SPEC.md) | <placeholder: one-line purpose> |
| Data | [20-data/DATA-MAP.md](./20-data/DATA-MAP.md) | Tables, schemas, migrations *(conditional)* |
| API | [30-api/API-MAP.md](./30-api/API-MAP.md) | Endpoint map *(conditional)* |
| UI | [40-ui/UI-MAP.md](./40-ui/UI-MAP.md) | Route / component map *(conditional)* |

---

## System Overview

<!-- hint: high-level runtime flow — enough for an agent to orient; details live in ARCHITECTURE.md -->
<!-- hint: use plain text + arrows; no Mermaid -->

```text
<placeholder: entry point, e.g. Browser / CLI / External caller>
-> <placeholder: frontend layer or gateway>
-> <placeholder: API / controller layer>
-> <placeholder: service / application layer>
-> <placeholder: repository / data layer>
-> <placeholder: data store, e.g. DB / cache / queue>
```

<!-- example (delete before use):
```text
Browser
-> Vue SPA (router + apiMap)
-> REST API controllers
-> Application services (commands + results)
-> Repositories / query services
-> PostgreSQL + Redis
```
-->

---

## Key Design Decisions

<!-- hint: capture decisions that are NOT obvious from the code; include the source file / line as evidence -->
<!-- hint: decisions with deeper rationale belong in ADR/NNN-slug.md; link from here -->

- **<placeholder: decision>**: <placeholder: rationale / consequence>  *(source: `<file>`)* 
- **<placeholder: decision>**: <placeholder: rationale / consequence>  *(source: `<file>`)*
- **<placeholder: decision>**: <placeholder: rationale / consequence>  *(ADR: [ADR/001-<slug>.md](./ADR/001-<slug>.md))*
