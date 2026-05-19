---
name: deep-review
description: Run a deep multi-agent code review on a PR or git diff. Dispatches 5 specialist subagents (risk, security, pattern, tests, convention) in parallel and synthesizes a Markdown matrix report. Honors project CLAUDE.md as the highest source of truth.
license: MIT
---

# Deep Review Orchestrator

Run a four-phase deep code review and emit a Markdown report.

## Inputs

The user invokes via `/morkit:deep-review <target>` where `<target>` is one of:
- `#<number>` or `<number>` → GitHub PR number (uses `gh pr diff <n>`)
- `--diff` → uses `git diff` (working tree vs HEAD)
- `--diff <ref>` → uses `git diff <ref>...HEAD`
- (empty) → defaults to `--diff`
- `--json` (flag) → emit JSON instead of Markdown (Phase 3 mode)

## Phase 1 — Ingest

1. Resolve target → produce a unified diff string.
   - PR: `gh pr diff <n>` (fail with clear message if `gh` missing or unauthenticated).
   - Diff: `git diff` or `git diff <ref>...HEAD`.
2. Parse diff to derive:
   - Changed file list.
   - Languages present (by extension): `.ts`/`.tsx`, `.py`, `.go`, `.java`, `.rs`, `.cs`, `.php`, `.rb`, `.js`/`.jsx`, etc.
3. Load **convention sources** in priority order:
   - **Tier 1**: project `CLAUDE.md` (read full content; if absent, mark "no CLAUDE.md").
   - **Tier 2**: matching `profiles/<lang>.md` files for each detected language (read from `${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/profiles/`).
   - **Tier 3**: universal rules (SOLID/DRY/KISS/YAGNI) — embedded below.
4. **Graph pre-flight (CRITICAL UX step).** Before dispatching specialists:
   1. Run `bash ${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/graph-status.sh` and parse the key=value output.
   2. Cross-check with `mcp__code-review-graph__list_graph_stats_tool` if the helper indicates `graph_present=true`.
   3. Decide based on `recommendation`:

      | recommendation | Behavior |
      |----------------|----------|
      | `skip` (graph already built) | Proceed to Phase 2 silently. |
      | `auto-build` (small repo, < 1500 files) | Print: "📊 Repo chưa có graph — đang build (~Ns cho N files)..." then call `mcp__code-review-graph__build_or_update_graph_tool`. Stream progress to chat. |
      | `prompt-user` (medium, 1500–8000 files) | **Ask the user**: "Repo này chưa có code graph (N files, ước tính ~Ns build). Build ngay để có review chất lượng đầy đủ? **(y/N/skip)**". On `y` → build with progress. On `N` or `skip` → continue in degraded mode. |
      | `prompt-user-large` (> 8000 files) | **Strong warning**: "⚠️ Repo lớn (N files, ước tính ~M phút build). Chỉ cần build 1 lần — sau đó mỗi diff < 2s. **Build now (y) / Skip & degraded (N)?**". |
      | `not-applicable` (not a git repo) | Fail fast: "❌ /morkit:deep-review requires a git repo." |

   4. If user declines build OR build fails → continue in **degraded mode** (Phase 2 subagents fall back to grep/Read; report header notes the mode).

## Phase 2 — Dispatch Specialists (PARALLEL)

Dispatch all 5 subagents in **a single message with multiple Agent tool calls** (parallel). Each subagent receives:
- The diff string
- The list of changed files
- The detected languages
- The Tier-1/Tier-2/Tier-3 convention bundle
- Instruction to cite **CLAUDE.md line numbers** when CLAUDE.md is the basis for a finding

| Subagent | Agent definition | Primary tools |
|----------|----------------|---------------|
| Risk & Impact Analyst | `agents/risk-impact-analyst.md` | `code-review-graph: detect_changes_tool, get_impact_radius_tool, get_affected_flows_tool, get_bridge_nodes_tool, query_graph_tool` |
| Security Auditor | `agents/security-auditor.md` | `code-review-graph: semantic_search_nodes_tool, query_graph_tool, get_minimal_context_tool` + Read/Grep |
| Pattern & Architecture Critic | `agents/pattern-architecture-critic.md` | `code-review-graph: get_architecture_overview_tool, list_communities_tool, get_hub_nodes_tool, find_large_functions_tool, get_surprising_connections_tool` |
| Test Coverage Auditor | `agents/test-coverage-auditor.md` | `code-review-graph: query_graph_tool (tests_for), get_knowledge_gaps_tool` |
| Convention Checker | `agents/convention-checker.md` | Read (CLAUDE.md + profile), Grep |
| Performance Auditor (Phase 2) | `agents/performance-auditor.md` | `code-review-graph: get_hub_nodes_tool` + Grep |
| Documentation Auditor (Phase 2) | `agents/documentation-auditor.md` | Read, Grep |

**Each subagent returns a YAML-Markdown findings block:**

```yaml
findings:
  - id: <S1|R1|P1|T1|C1|Pf1|D1>-<n>
    category: Security|Risk|Pattern|Tests|Convention
    severity: Critical|High|Medium|Low|Info
    file: path/to/file.ts
    line: 42
    title: short description
    detail: longer explanation
    source: "CLAUDE.md:L<line>" | "profile:typescript" | "universal:SOLID-S" | "graph:impact_radius" | "OWASP:A03"
    suggested_fix: code or text
    confidence: 0-100
```

## Phase 3 — Synthesize

1. Merge findings from all 5 subagents.
2. Deduplicate (same file:line + same title).
3. Apply severity calibration matrix in `${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/lib/severity-calibration.md` (multiply weights by modifiers).
4. Rank: Critical first, then High, Medium, Low, Info.
5. Build executive summary:
   - Overall Risk: highest individual severity (capped at HIGH unless ≥2 Critical → CRITICAL).
   - Decision: BLOCK if any Critical; APPROVE WITH CHANGES if any High; APPROVE otherwise.
   - Confidence: weighted average.

## Phase 4 — Output

1. Render `${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/templates/report-template.md` with computed values.
2. **Print full report directly to chat.**
3. Save to `morkit/output/reviews/deep-review-<timestamp>-<target>.md` if writable; otherwise skip silently.
4. If `--json` flag passed, emit JSON instead (see "JSON output mode" below).
5. **Suggest next step at the end of the report** based on Decision:
   - **BLOCK** → "Fix Critical findings, push fix commit, then re-run `/morkit:deep-review <target>`."
   - **APPROVE WITH CHANGES** → "Address High findings (or defer with justification), push, then merge."
   - **APPROVE** → "Ready to merge. After merge, close out the change with `/morkit:archive <name>` if this PR was linked to a morkit change."

## Universal Rules (Tier 3, embedded)

- **SOLID**: Single-responsibility, Open/closed, Liskov, Interface-segregation, Dependency-inversion violations are findings.
- **DRY**: Three or more near-identical blocks → finding.
- **KISS / YAGNI**: Speculative abstraction, dead branches, unused parameters → finding.
- **Cyclomatic complexity** > 10 in changed functions → finding.
- **Magic numbers** (non-0/1/-1) without named constant → finding.
- **Long methods** > 60 lines (changed) → finding.
- **Error swallowing** (empty catch / `pass` on except / `_ = err`) → finding.
- **Resource leaks** (no `defer`/`finally`/`with`) → finding.

## Tier-1 Override Rule (CRITICAL)

If CLAUDE.md states a convention that conflicts with the language profile, **CLAUDE.md wins**. Cite the CLAUDE.md line in `source`. Findings derived from a profile rule that is contradicted by CLAUDE.md MUST be suppressed and instead recorded as `Info`-level note "profile rule overridden by CLAUDE.md:L<n>".

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `gh` missing for PR target | Fail with: "Install GitHub CLI: brew install gh && gh auth login" |
| Graph build fails | Continue in degraded mode; subagents fall back to Read/Grep; report header notes "⚠️ Degraded mode (no graph)" |
| Empty diff | Print "No changes to review." and exit |
| Subagent timeout | Skip that subagent; report header notes which categories were skipped |

## Severity calibration

Apply the matrix in `${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/lib/severity-calibration.md` during Phase 3 (Synthesize). Multiply base weight by modifiers; recompute overall risk and decision per the matrix.

## JSON output mode

When the invocation includes the `--json` flag, Phase 4 emits a JSON object instead of Markdown:

```json
{
  "schema_version": 1,
  "target": "<PR# or diff ref>",
  "timestamp": "<ISO 8601>",
  "mode": "full | degraded-no-graph | degraded-no-gh",
  "overall": {
    "risk": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
    "decision": "BLOCK|APPROVE_WITH_CHANGES|APPROVE",
    "confidence": 0
  },
  "convention_sources": {
    "claude_md_present": true,
    "language_profiles": ["typescript", "python"]
  },
  "findings": [
    {
      "id": "S1",
      "category": "Security",
      "severity": "Critical",
      "file": "src/auth.ts",
      "line": 42,
      "title": "...",
      "detail": "...",
      "source": "OWASP:A03",
      "suggested_fix": "...",
      "confidence": 95,
      "score": 110
    }
  ],
  "positives": ["..."],
  "actions": ["..."]
}
```

JSON mode is intended for CI/CD pipelines. Save to `deep-review.json` instead of `morkit/output/reviews/*.md` when `--json` is set.
