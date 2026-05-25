---
updated: <YYYY-MM-DD>
status: draft
---

# Risk Register

> System-level and business risks. For code-time mistakes see [KNOWN-PITFALLS.md](KNOWN-PITFALLS.md). For invariants that must never break see [../../20-design/00-core/INVARIANTS.md](../../20-design/00-core/INVARIANTS.md).

---

<!-- hint: Risk = something that could go wrong in production or over time, not a coding mistake -->
<!-- hint: Impact = who/what is affected if it happens; Mitigation = concrete preventive action -->

| Risk | Impact | Mitigation |
|---|---|---|
| <e.g. "Access-control regression on list/export"> | <e.g. "Users see unauthorized data"> | <e.g. "Test allowed and denied cases in service layer before every release"> |
| <e.g. "Accidental removal of a hidden-but-active route"> | <e.g. "Silent breakage for callers not visible in UI"> | <e.g. "Search all callers before removing; see CODE-SEARCH-GUIDE.md"> |
| <e.g. "Data source confusion (current vs legacy)"> | <e.g. "Feature operates on stale or wrong records"> | <e.g. "Use SOURCE-MAP to confirm active table before writing queries"> |
| <e.g. "Serialized job args drift between producer and consumer"> | <e.g. "Background job silently ignores filters"> | <e.g. "Keep arg names in sync; add integration test for job creation"> |
| <e.g. "Dependency version upgrade breaks behavior"> | <e.g. "Runtime error in production after deploy"> | <e.g. "Pin versions; run full test suite after upgrades"> |
| <placeholder> | <placeholder> | <placeholder> |
