# Severity Calibration Matrix

Subagents emit `severity: Critical|High|Medium|Low|Info`. The orchestrator may **adjust** severity using this matrix at synthesis time.

## Severity weights

| Severity | Weight |
|----------|-------:|
| Critical | 100 |
| High     | 60 |
| Medium   | 30 |
| Low      | 10 |
| Info     | 1 |

## Modifiers (applied multiplicatively, capped 0.5x to 2.0x)

| Modifier | Factor |
|----------|-------:|
| Finding inside critical flow (auth/payment/admin/crypt) | ×1.5 |
| Bridge node touched | ×1.3 |
| Impact radius ≥ 50 | ×1.4 |
| Impact radius ≥ 20 | ×1.2 |
| Symbol has 0 tests | ×1.2 |
| Confidence ≥ 90 | ×1.1 |
| Confidence ≤ 50 | ×0.7 |
| Already covered by lint/typecheck (assume project enforces) | ×0.5 |

## Overall risk

`overall_score = max(finding_score)` — but if ≥ 2 Critical findings, escalate one rank.

| Score | Overall risk |
|------:|--------------|
| ≥ 100 | CRITICAL |
| ≥ 60 | HIGH |
| ≥ 30 | MEDIUM |
| ≥ 10 | LOW |
| < 10 | INFO |

## Decision

- Any **Critical** after modifiers → BLOCK
- Any **High** after modifiers → APPROVE WITH CHANGES
- Otherwise → APPROVE
