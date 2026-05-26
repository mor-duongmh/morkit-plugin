# Summarize Workflow

`/morkit:docs summarize [path]`

Quick refresh of the two most important anchors without touching the full taxonomy. Use for a fast "where is everything now" pass.

## Examples

```bash
# Quick "where is everything now" refresh of SOURCE-MAP + DOCUMENT-MAP
/morkit:docs summarize

# Summarize a project in another directory
/morkit:docs summarize ../api-service
```

Outcome: light read-only scout → `00-overview/SOURCE-MAP` + `DOCUMENT-MAP` refreshed → `updated` bumped → short report. Feature specs, tests, and design docs are NOT touched — use `/morkit:docs update` for those.

## Steps

1. **Light scout** (read-only): directory tree, entry points, key symbols, routes, data stores. Cheaper than init's full scout.
2. **Refresh `00-overview/SOURCE-MAP`**: concern→file→symbol table + code-search keywords, reflecting current code.
3. **Refresh `00-overview/DOCUMENT-MAP`**: directory roles + read paths + canonical source rules, with links to whatever docs currently exist.
4. **If no taxonomy exists yet**: produce a minimal `00-overview/` (SOURCE-MAP + DOCUMENT-MAP + SCOPE) as a starting point and suggest `/morkit:init` for the full set.
5. Bump `updated`; report what was refreshed.

## Notes
- Does NOT regenerate feature specs, tests, or design docs — that's `init`/`update`.
- Keep it fast and cheap; this is the "quick orientation" mode.
