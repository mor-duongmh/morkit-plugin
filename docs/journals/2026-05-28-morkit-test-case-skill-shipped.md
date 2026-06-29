# Shipped `/morkit:generate-test-cases` — Interactive QA Test-Case Authoring Skill

**Date**: 2026-05-28 14:30
**Severity**: Low (feature addition, no breaking changes)
**Component**: morkit skills / QA tooling
**Status**: Complete

## What Happened

Brainstormed, planned, and shipped a new standalone skill: `/morkit:generate-test-cases`. Interactive tool for QA engineers to write Japanese-style test-case specifications directly into a project Excel workbook. Prior-art research confirmed no public tool combines interactive brainstorm + optional live-URL exploration + deterministic openpyxl write to user's template.

Skill shipped with full SKILL.md documentation, 4 Python writer modules, template asset, reference schemas, and 8-step execution flow. Merged to main without test suite (per user scope gate); smoke-tested manually across 4 features including forced clone scenarios.

## The Brutal Truth

This skill exists because QA handoff is broken. Testers export Jira, paste into Excel, manually key test procedures line-by-line, send back. Then devs extract one sentence per test case from a wall of text. We built an *interactive middleman* that asks for structure upfront.

The hardest part wasn't code — it was *understanding why Excel formulas break*. Spent 90 minutes discovering that `copy_worksheet()` silently drops data-validations and doesn't auto-update cross-sheet formula references when worksheet names stay generic (`Feature 1`). That's not a bug; that's how openpyxl works. Once verified, the mitigation was trivial: re-apply validations post-clone, keep tab names generic.

The frustrating part: Excel formula behavior is invisible until you open the file. We can't validate formula *values* in CI/CD with openpyxl (it doesn't evaluate formulas). We can only validate formula *syntax*. Caught by manual open.

## Technical Details

**What ships:**
- `plugins/morkit/skills/generate-test-cases/SKILL.md` — 8-step interactive flow, 10 hard rules
- 4 Python modules (each <200 lines, `py_compile` verified clean):
  - `workbook_resolver.py` — copy/append logic, `.bak` creation, atomic `os.replace`
  - `feature_sheet_writer.py` — row writing, formula stamping (rows 9-∞), DV re-application post-clone
  - `test_report_updater.py` — cross-sheet formula insertion (`='Feature N'!G5`), SUM auto-extend
  - `write_test_cases.py` — entry script, argparse, plain-language error messaging
- `assets/test-case-template.xlsx` — byte copy of team's production template
- `references/cases-schema.json` — nested row structure with `continuation` support
- `references/wording-conventions.md` — lexicon mined from Sample workbook (terse style: "Check X", blank B-cell continuation, numbered procedures)

**Critical decision: generic tab names (`Feature 1`, `Feature 2`, ..., `Feature N`)**
— Verified `copy_worksheet()` does NOT auto-update formula references on rename. Test Report module contains hardcoded `='Feature 1'!G5` formulas. Excel UI auto-updates on rename; openpyxl does not. Solution: leave names generic, embed real feature name in C1. Cheap and verified.

**Data-validation dropout on clone:**
Template has `Pass,Fail,Untested,N/A` dropdown on column H. Verified: `copy_worksheet()` creates worksheet with 0 DV entries (source has 1). Re-apply post-clone by reading template's DV, copying to cloned sheet.

**Formula pre-stamping + extension:**
Template pre-stamps `=A9`, `=B9`, ..., `=J9` formulas to row 40. Writer extends stamping beyond row 40 per row count. Test Report SUM formula auto-extends (e.g., `=COUNTA(Features!G9:G40)` → `=COUNTA(Features!G9:G99)` if 99 rows written).

**Two languages, different concerns:**
- **Communication language** (asked FIRST at invoke): sticky across session; affects error messages, explanations.
- **Output language** (per-run at Step 6): answer per feature for user preference. Decoupled from communication.

## What We Tried

1. **Rename cloned worksheets to real feature name** — Verified it breaks Test Report formulas. Reverted.
2. **Calculate formula values with openpyxl** — Not supported; only formula strings. Deferred to manual validation.
3. **Docs-hero orchestrated skill (generate-update-delete modes)** — Overkill; QA authors one feature per ticket. Chose standalone.
4. **Auto-drive live Jira login + export** — Agent-browser headed mode proof-of-concept worked, but data-mutation risk on live apps. Deferred post-v1.
5. **Formal test suite** — User scope gate: skip tests, ship v1, iterate. Smoke-tested manually instead.

## Root Cause Analysis

Why this works now: We **stopped assuming testers know Excel formula syntax**. Instead:
- Testers export Jira → Describe feature in plain language + pick scope (approved ticket).
- Skill brainstorms test cases interactively (optional live-URL exploration for edge cases).
- Skill writes deterministically into template using openpyxl.
- Skill validates only formula *strings* match template (can't validate *values* in CI).
- Testers open file, verify formulas calc correctly, send back. (1-minute check, not 30-minute manual write.)

Why it was hard: **Excel's formula reference behavior is environment-dependent.** Excel UI auto-updates on rename; openpyxl does not. That's not a bug in openpyxl — it's a design consequence. Once we accepted that, the fix was trivial: don't rename worksheets.

Why prior-art research mattered: Confirmed no public tool does this specific combo. `test-driven-development` skill handles DEV automated tests. This is QA manual specs. Different audience, different artifact. Justified building standalone.

## Lessons Learned

- **Verify Excel behavior empirically.** Formula refs, DV dropout, copy semantics — all need to be tested by opening the output file. openpyxl is great for generation but not introspection.
- **One feature per run is correct.** QA reality is ticket-by-ticket authoring. Bulk generation = shallow, AI-generated specs. Scoped it to one + append, clone on demand.
- **Scope gates are cheap prevention.** Tester edits `<feature>-test-scope.md`, sets `status: approved` before expansion. That 1-line plan is way cheaper to revise than re-generating 100 test rows.
- **Hide the machinery from non-tech users.** Plain language errors, no tracebacks, no JSON schema exposed. Testers don't care how it works.
- **Reuse existing envs.** docs-hero venv already has openpyxl 3.1.5. Zero new setup overhead.

## Next Steps

1. **Codex fork sync** — `scripts/sync-codex-fork.sh` needs manual run (deferred to separate task; avoid mid-flight merges).
2. **Jira MCP ingestion** — Task #9: once `/mcp:jira` stable, auto-ingest Jira ticket + export to temp file for skill intake (v2).
3. **Browser drive-flows** — Post-v1: headed agent-browser mode for live-URL snapshot collection, form automation (low risk read-only first).
4. **Row height auto-fit** — Cosmetic; Excel expands on open. Can add later if testers complain.
5. **Gather user feedback** — First QA team using this will find edge cases (multiline headers, conditional formatting, hidden columns). Build v1.1 from real usage.

## Unresolved Questions

- Will re-running with `--sheet-conflict append` duplicate section headers? (Acceptable v1, deferred investigation.)
- Do testers want formula validation in CI, or is manual open sufficient? (Assume manual; ask during rollout.)
- Should `/morkit:sync` auto-sync this skill on install? (Currently manual; low priority since skills auto-discover.)
