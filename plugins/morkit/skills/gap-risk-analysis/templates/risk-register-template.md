# Risk Register — {{PROJECT_NAME}}

> **Canonical source.** ProjectModel `constraints_risks.risks[]` and SRS §13.3 are
> rendered *from this table* — never edit risks in two places. Columns map 1:1 to
> SRS §13.3 (`Probability → Likelihood`; `Score`/`Category`/`High?` are extras).
>
> **Scoring (locked):** `H/M/L → 3/2/1`, `Score = Probability × Impact` (1–9),
> **High = Score ≥ 6**. Every **High** risk **MUST** have a non-empty Mitigation
> (enforced by `compute_risk_score.py`).

| Risk-ID | Category | Risk (Description) | Probability (H/M/L) | Impact (H/M/L) | Score (1–9) | High? | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|---|---|---|
| RISK-001 | Technical | {{risk description}} | M | H | 6 | ✅ | {{mitigation — required when High}} | {{owner}} | Open |
| RISK-002 | Business | {{risk description}} | L | M | 2 | — | {{optional}} | {{owner}} | Open |
| RISK-003 | Dependency | {{external dependency risk}} | M | M | 4 | — | {{optional}} | {{owner}} | Monitoring |
| RISK-004 | Gaps | {{risk arising from an open gap GAP-00x}} | H | M | 6 | ✅ | {{mitigation}} | {{owner}} | Open |

**Categories:** `Technical` · `Business` · `Dependency` · `Gaps`.
**Status:** `Open` · `Monitoring` · `Closed` (→ ProjectModel `Risk.risk_status`).

<!-- Sync mapping (for build-project-model bridge):
  Risk-ID→Risk.id  Description→Risk.description  Probability→Risk.likelihood
  Impact→Risk.impact  Mitigation→Risk.mitigation  Owner→Risk.owner  Status→Risk.risk_status
  Score, Category, High? → extra fields (extra="allow"). Map H/M/L→High/Mid/Low. -->
