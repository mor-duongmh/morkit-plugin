# Clarification Log — {{PROJECT_NAME}}

> **Resume-able state lives in THIS file** (template-only depth — no tracker code).
> AI generates questions; BA/BrSE answers inline or marks `forwarded → <stakeholder>`.
> On re-run, AI ingests answers, updates the ProjectModel, and fills `<TBD>`.
> Questions are grouped by the User-Story / Gap that spawned them.
>
> **Status:** `open` · `answered` · `forwarded`. The loop closes when open-count
> meets the threshold (or the BA force-closes at the G4 gate). Answered Q&A renders
> into SRS §12.

## Round {{N}} — {{DATE}}

### US-001 / {{story title}}

| Q-ID | Question | Status | Answer | Forwarded-to | Resolved-FR |
|---|---|---|---|---|---|
| Q-001 | {{clarifying question}} | open | | | |
| Q-002 | {{clarifying question}} | answered | {{stakeholder answer}} | | FR-001 |
| Q-003 | {{question needing a 3rd party}} | forwarded | | customer-pm | |

### GAP-002 / {{gap description}}

| Q-ID | Question | Status | Answer | Forwarded-to | Resolved-FR |
|---|---|---|---|---|---|
| Q-004 | {{question}} | open | | | |

---

**Loop status:** open={{open_count}} · answered={{answered_count}} · forwarded={{forwarded_count}}

<!-- Bridge mapping (build-project-model): each Q → OpenQuestion{ id:Q-00x,
  question, q_status: Open|Answered (forwarded stays Open), answer,
  related_id: US/GAP/FR } → SRS §12. An "answered" Q resolves its `<TBD>` in the
  target FR's detail and may set Resolved-FR. -->
