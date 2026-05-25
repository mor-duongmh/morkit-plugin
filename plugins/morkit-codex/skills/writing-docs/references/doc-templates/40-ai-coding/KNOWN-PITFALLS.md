---
updated: <YYYY-MM-DD>
status: draft
---

# Known Pitfalls

> Code-time mistakes commonly made in this codebase. For runtime diagnostics see [../../90-operations/TROUBLESHOOTING.md](../../90-operations/TROUBLESHOOTING.md).

---

<!-- hint: each row = one concrete mistake an agent or dev has made or is likely to make -->
<!-- hint: "Why It Happens" = root cause; "How To Avoid" = actionable rule -->

| Pitfall | Why It Happens | How To Avoid |
|---|---|---|
| <e.g. "Editing the wrong table/model"> | <e.g. "Two systems coexist with similar names"> | <e.g. "Check SOURCE-MAP for which table serves the active feature"> |
| <e.g. "Partial update overwrites absent fields with null"> | <e.g. "Default ORM behavior replaces entire record"> | <e.g. "Use merge/patch pattern; load existing record first"> |
| <e.g. "Auth check missing on new endpoint"> | <e.g. "Copied handler without copying middleware chain"> | <e.g. "Verify auth guard is applied; test with unauthenticated request"> |
| <e.g. "Constants updated in code but not in DB seed"> | <e.g. "Lookup table and code constant are separate"> | <e.g. "Always update both; see playbook in COMMON-CHANGE-PLAYBOOKS.md"> |
| <e.g. "Import removed but still used elsewhere"> | <e.g. "IDE auto-removed unused import in the edited file only"> | <e.g. "Run `rg -n '<symbol>'` across full src before removing"> |
| <e.g. "Test passes locally, fails in CI"> | <e.g. "Test depends on local env variable or fixture not in CI"> | <e.g. "Check CI env config; use fixtures committed to repo"> |
| <placeholder> | <placeholder> | <placeholder> |
