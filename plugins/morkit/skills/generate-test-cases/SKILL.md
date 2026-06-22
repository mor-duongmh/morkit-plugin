---
name: generate-test-cases
description: "Help a manual QA tester author test-case specifications into an Excel workbook. Interactive: understand a feature from docs/images/optional live URL, brainstorm coverage, approve a test-scope gate, then write finished test cases (description, pre-condition, procedure, expected output) into the team's Excel template. Writes specs only — never runs tests. Use when a tester says 'write test cases', 'viết test case', 'create test cases for <feature>', or needs a test-case sheet filled."
user-invocable: true
category: testing
keywords: [test-case, qa, tester, manual-testing, excel, test-spec, viewpoint, normal-abnormal, brse]
allowed-tools: Bash, Read, Write, AskUserQuestion
argument-hint: "[feature description] [--url <live-url>] [--out <workbook>] [--template <xlsx>] [--lang <comm-language>]"
metadata:
  author: morkit
  version: "1.2.0"
---

# Generate Test Cases

Interactive assistant that helps a **manual QA tester** write **test-case specifications** into the team's Excel template.

**STANDALONE skill.** Despite the `generate-*` name, this is NOT part of the docs-hero pipeline — no `init`/`sync`/`update` modes, no `ProjectModel`. It runs on its own, end to end.

**Writes specs only.** It never executes tests, never fills result columns, never logs bugs.

## Environment

```bash
PLUGIN_ROOT="${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:?set by Claude Code}}"
SKILL_DIR="${PLUGIN_ROOT}/skills/generate-test-cases"
VENV="${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data}}/docs-hero/.venv"
PY="${VENV}/bin/python3"; [ -x "$PY" ] || PY="python3"   # reuse docs-hero venv (openpyxl), fallback system
TEMPLATE_DEFAULT="${SKILL_DIR}/assets/test-case-template.xlsx"
```

If `python3 -c "import openpyxl"` fails, run `/morkit:setup` (bootstraps the docs-hero venv) and retry.

## Hard rules (NON-NEGOTIABLE)

1. **Communication language is sticky.** Ask it FIRST (Step 1), then reply ONLY in it for the whole session.
2. **Mandatory asks** (never skip): comm language → available inputs → grouping strategy + sections → scope approval → output language → sheet conflict on re-run.
3. **Scope gate is blocking — human-only approval.** You write the scope file ONCE with `status: draft` and **never touch that status line again.** Only the human reviewer may change it to `approved`/`Approved`. You MUST NOT set, flip, suggest-then-write, or "helpfully" pre-fill approval — not even if the tester says "approved" in chat; they must edit the file themselves. Before Step 6 and again before Step 7, re-read the file and confirm the human set status to approved. If it is anything else (draft, missing, blank, partial), **STOP and block** — no exceptions, no auto-approve, no "looks done so I'll proceed".
4. **Data-mutation safety.** On a live app: read-only by default (snapshot, navigate, click non-destructive elements). NEVER submit/create/edit/delete without explicit per-action confirmation.
5. **No test execution.** Never run tests; never fill result columns F–I.
6. **Don't touch human/runtime cells.** Never write F–I (R0–R3), J value, K (Bug ID), L (Note), C3 (Tester), C4 (Test requirement), stat formulas, or the BUG sheet. The Python writer enforces this — do not bypass it by editing the xlsx directly.
7. **Never mutate the user's template.** Always work on the output copy.
8. **Deterministic writer.** All Excel writing goes through `scripts/write_test_cases.py`. You produce `cases.json`; the script writes the workbook. Never hand-edit the xlsx.
9. **Soft docs rule.** Strongly recommend + coach doc retrieval, but allow proceeding without docs (warn that coverage will be weaker).
10. **Plain, non-technical tone.** Testers are non-tech. No jargon, file paths, JSON, or code talk in what you say to them. Speak QA: test cases, steps, expected results. Hide the machinery.

## Workflow (8 steps)

### Step 1 — Invoke & inputs
1. **Ask communication language FIRST** (`AskUserQuestion`). Stick to it all session. (`--lang` may pre-set it.)
2. **Ask what inputs the tester can provide** (`AskUserQuestion`, multi-select): spec doc, images/screenshots, live URL, or "just my description".
3. **Coach doc retrieval** based on their answer:
   - Jira → ask them to **export the ticket** (PDF/Word) and share the file. (No Jira integration in v1.)
   - Confluence / web doc → share the page link.
   - Shared drive / local → share the file path.
4. **Resolve template:** default = bundled `test-case-template.xlsx`. Tell the tester they CAN provide a custom template (`--template`) if their project uses a different one.
5. **Resolve output:** `--out` given + exists → append to it; given + new → create from template; omitted → `./test-cases/<feature-slug>-testcases.xlsx`. Sidecar artifacts (scope, discovery, cases) live beside it.
6. **Minimum to start:** feature name + a one-line description. Everything else is gathered as you go.
7. **Resume check:** if a scope file or `cases.json` already exists for this feature, offer to resume (skip re-brainstorm).

### Step 2 — Understand the feature
Order: **ingest → clarify gaps → (explore) → refine.**
1. Ingest provided docs (PDF/docx/xlsx/md via the matching skill; web fetch; pasted text) and analyze images with your own vision.
2. Ask clarifying questions ONLY about gaps the docs/images didn't cover. Use a hybrid style: `AskUserQuestion` for standard dimensions, open chat for specifics.
3. Probe checklist (the viewpoint seed): happy-path flow · actors/roles/permissions · entry point · input fields + validations · states (empty/loaded/loading/error) · business rules · boundary/edge · error/abnormal paths · cross-browser/device.
4. Stop when you're confident you can define sections + cases. State your confidence briefly; the tester can add more.

### Step 3 — Explore the live app (optional)
Only if a URL is offered and the tester agrees. Read `references/` of the agent-browser skill if needed; load its `dogfood` taxonomy for QA viewpoints.
```bash
agent-browser open --headed <url>        # headed so the tester can watch + log in
agent-browser snapshot -i                # accessibility tree + @eN refs
agent-browser screenshot <path>
```
- **Manual login:** if auth is needed, ask the tester to log in themselves in the opened window; wait; then `agent-browser state save <path>` and continue.
- **Read-only:** snapshot, navigate, click non-destructive elements (tabs, toggles, pagination). **Never** submit forms or create/edit/delete without explicit go-ahead.
- Borrow dogfood's issue-taxonomy as a viewpoint checklist; do NOT produce a bug report.
- Save findings to `<feature-slug>-ui-discovery.md` beside the output; fold into the understanding.

### Step 4 — Sections (MUST ask)
1. Offer grouping strategies (`AskUserQuestion`): by UI area · by user flow · by function · by normal/abnormal. The tester always chooses.
2. Propose candidate sections per the chosen strategy.
3. The tester edits/reorders/confirms. This confirmation is mandatory.

### Step 5 — Scope review gate 🚦
1. Write `<feature-slug>-test-scope.md` beside the output, starting with a `status: draft` header. Under each section, draft a **markdown table** with **one row per planned case** and these columns: **Test Case Description · Pre-condition · Test Case Procedures · Expected Output**. Keep the wording **minimal — a preview/overview, NOT the full steps**: a short description, a sparse pre-condition, 1–2 brief procedure notes, a one-line expected result. The columns mirror the final Excel sheet so the tester sees at a glance what each case will become; full numbered procedures and concrete multiline expected outputs come later in Step 6. See `references/wording-conventions.md` → "Scope preview table".
2. Show a **coverage summary** (normal vs abnormal counts, viewpoints covered) and **flag suspected gaps once** (missing edge/error/empty/boundary). This summary stays in chat — the scope file carries only the four case columns; normal/abnormal and viewpoints are derived, not stored.
3. Ask the tester to **open the file themselves, review/edit it, and change `status: draft` → `status: approved` by hand.** You never edit that line. Approval given only in chat does NOT count — the file must say approved.
4. Re-read after they say they're done; if still not approved, tell them it's blocked and wait. Loop until the file shows approved. **Never proceed otherwise.**

### Step 6 — Expand to full cases
0. **Approval gate (BLOCKING).** Re-read the scope file and confirm the human set it to approved before doing anything else in this step:
   ```bash
   grep -iqE '^[[:space:]]*status:[[:space:]]*approved[[:space:]]*$' <feature-slug>-test-scope.md \
     && echo "APPROVED" || echo "BLOCKED — scope not approved"
   ```
   If this prints `BLOCKED`, STOP: do not expand cases, do not emit `cases.json`, do not run the writer. Return to Step 5 and wait for the human to approve in the file. Never edit the status line to unblock yourself.
1. **Ask the output language** for the test-case text (`AskUserQuestion`: English / Vietnamese / Japanese). This is per-run and distinct from the communication language.
2. Expand each approved scope row into full content following `references/wording-conventions.md`: terse `Check "X"` descriptions, blank-B continuation rows, sparse pre-conditions, numbered procedures, multiline concrete expected outputs. A single scope row may become one case with several continuation rows.
3. Emit `cases.json` beside the output, conforming to `references/cases-schema.json` (nested `rows[]` per case for continuations; `viewpoint`/`type` are metadata only).

### Step 7 — Write to Excel
Invoke the deterministic writer (never edit the xlsx yourself):
```bash
"$PY" "${SKILL_DIR}/scripts/write_test_cases.py" \
  --cases <feature-slug>-cases.json \
  --template "${TEMPLATE_DEFAULT}"   `# or the tester's --template` \
  --out <output.xlsx> \
  [--sheet-conflict append|new|overwrite]
```
- If this feature already has a sheet, ask the tester: append below / new sheet / overwrite → pass as `--sheet-conflict`.
- The script prints a JSON result. On `{"ok": false, ...}`, explain the problem to the tester in plain language and note the previous file is safe (a `.bak` was kept). Then fix and retry; if the script itself is broken, fix the script.

### Step 8 — Report & close
Report in the communication language:
- Output file + which sheet was used (and new-vs-appended), case + section counts, normal/abnormal split, viewpoints covered, any gaps the tester chose to skip.
- **What's left for the tester (manual):** the skill did NOT fill results (R0–R3), Tester, Test requirement, Bug IDs, or Notes — those are filled during actual test execution.
- Artifacts written (scope, discovery if any, the workbook + `.bak`).
- Offer to open the workbook (`open <path>` on macOS); let the tester decide.

## References
- `references/cases-schema.json` — the `cases.json` contract for Step 6/7.
- `references/wording-conventions.md` — B/C/D/E wording style to mimic.

## Template contract (what the writer fills)
Per feature sheet: `C1` = feature name; section rows (column B only); case rows from row 9 with `B` description (blank on continuation), `C` pre-condition, `D` procedure, `E` expected. The writer also stamps the ID (`A`) and Final-Result (`J`) formulas and the Pass/Fail/Untested/N/A dropdown, and wires the Test Report sheet. After writing, the writer **renames the sheet tab to the feature name** (sanitized to Excel's rules, ≤31 chars, unique), **deletes any unused placeholder `Feature N` tabs**, and **rebuilds the Test Report** so its formula refs and module labels point at the renamed tabs. The `Test Report` tab itself keeps its name. Identity of a feature sheet is structural (the `=COUNT(A9…)` cell in `C2`), not the tab label — so re-runs still find a feature by its `C1` name after renaming.

## Workflow position
**Standalone.** Pairs naturally after a feature is built/specced. Not chained into the morkit propose→execute→review flow.
