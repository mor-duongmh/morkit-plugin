# Gap Analysis — {{PROJECT_NAME}}

> **Canonical source.** Gaps tagged `new-requirement` become clarification
> questions (G4) and/or new FRs; gaps tagged `out-of-scope` feed
> ProjectModel `overview.out_of_scope`. Gaps needing an answer sync into
> `open_questions[]` → SRS §12. Every gap links the User-Story / FR it affects.

| GAP-ID | Description | Affected US/FR | Type | Severity | Recommended Action | Resolution |
|---|---|---|---|---|---|---|
| GAP-001 | {{what is missing / ambiguous}} | US-003, FR-002 | new-requirement | blocker | ask stakeholder (→ G4 clarify) | _open_ |
| GAP-002 | {{capability the customer asked for but is outside this release}} | US-005 | out-of-scope | info | record in `out_of_scope` | _open_ |
| GAP-003 | {{undefined NFR threshold / acceptance criterion}} | FR-004 | new-requirement | warning | placeholder `<TBD: …>` | _open_ |

**Type:** `new-requirement` (needs a requirement) · `out-of-scope` (explicitly excluded).
**Severity:** `blocker` (stops a section) · `warning` (weakens it) · `info` (note).
**Resolution:** `_open_` → `answered` (G4) / `accepted` / `dropped`.

<!-- Sync mapping (for build-project-model bridge):
  new-requirement + needs-answer → OpenQuestion{ id:Q-00x, question:Description,
    category, related_id:Affected US/FR, q_status:Open } → SRS §12.
  out-of-scope → overview.out_of_scope[] entry.
  A High-impact gap should also be raised as a RISK-00x (Category=Gaps). -->
