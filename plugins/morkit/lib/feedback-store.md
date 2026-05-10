# False-Positive Feedback Store

Local, opt-in. Lives at `${HOME}/.claude/morkit:deep-review/feedback.jsonl` (JSON-lines).

## Record schema

```json
{
  "ts": "<ISO 8601>",
  "finding_id": "S1",
  "rule_source": "OWASP:A03",
  "file": "src/auth.ts",
  "line": 42,
  "verdict": "false-positive | true-positive | wont-fix",
  "note": "free text"
}
```

## CLI

A future slash command `/deep-review-feedback` (reserved):
- `dismiss <finding-id> <reason>` — mark as false-positive
- `list` — show last N entries
- `stats` — aggregate by `rule_source`

## Use at synthesis time

The orchestrator MAY downweight findings whose `rule_source` matches an entry with `verdict=false-positive` for the same file (last 90 days). This is heuristic, not authoritative.

Privacy: no upload. Local file only. Users may delete at any time.
