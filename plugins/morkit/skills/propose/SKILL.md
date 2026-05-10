---
name: propose
description: Propose a new morkit change with all artifacts generated in one step. Use when the user wants to describe what they want to build and get a complete proposal with design, tasks, and review-checklist ready for implementation. No OpenSpec or external CLI dependency — plugin scaffolds directly.
license: MIT
---

Create a new morkit change with all artifacts in `${MORKIT_ROOT:-morkit/output/spec}/<name>/`:

- `proposal.md` — what & why
- `design.md` — how, including Tech Stack
- `tasks.md` — TDD-ready, Superpowers header
- `.meta.json` — name, created_at, schema_version, archived flag
- `review-checklist.md` — auto-generated from canonical Google Doc (human gate)

When ready to implement, run `/morkit:executing-plans` (blocked until review-checklist `Overall Decision: OK`).

---

**Input:** the user's request should include a kebab-case name OR a description from which a name can be derived.

**Steps**

1. **If no clear input provided, ask what they want to build**

   Use the **AskUserQuestion tool** (open-ended, no preset options):
   > "What change do you want to work on? Describe what you want to build or fix."

   Derive a kebab-case name (e.g. "add user authentication" → `add-user-auth`).

   **IMPORTANT:** Do NOT proceed without a clear description.

2. **Scaffold the change folder**

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold-change.sh" "<name>"
   ```

   On success the script creates `<root>/<name>/{proposal,design,tasks}.md` + `.meta.json` + ensures `<root>/.morkit` marker.

   On `already exists`: report to user and ask via AskUserQuestion whether to `--force` overwrite.

3. **Fill artifacts based on the user's description**

   Use the **TodoWrite tool** to track progress through artifacts.

   Edit the three files (Edit tool) replacing template placeholders with substantive content:
   - `proposal.md`: Why, What changes (concrete bullets), Impact (affected components/users/migration), Out of scope.
   - `design.md`: Architecture, **Tech Stack** (REQUIRED — verify libraries via Context7 if uncertain), Data model, API contract, Open questions.
   - `tasks.md`: keep the Superpowers header line, Goal/Architecture/Tech Stack summary matching design.md, File Structure (New / Modified / Deleted), and Task N blocks each with `**Files:**` + TDD `- [ ]` checkboxes.

4. **Validate the tasks.md**

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/validate-tasks.sh" "<root>/<name>/tasks.md"
   ```

   On failure, fix the cited rule (R1-R6) and re-validate. Do NOT claim success until validator exits 0.

5. **Generate the review-checklist (human gate)**

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/generate-checklist.sh" "<root>/<name>"
   ```

   Auto-detects variant (BE/FE × Feature/BugFix/Refactor) from proposal+tasks signals. Override with `--variant <id>` if user specifies.

   On fetch failure (no network, Google Doc unreachable, no cache): report the error verbatim and tell the user to run `/morkit:review` manually with `--variant`.

6. **Report**

   ```
   ## Spec Change Created

   **Path:** <root>/<name>/
   **Files:**
     - proposal.md
     - design.md
     - tasks.md
     - .meta.json
     - review-checklist.md (variant: <detected>)

   **Next:**
     1. Open review-checklist.md, tick items, fill summary
     2. Set "Overall Decision: OK"
     3. Run /morkit:executing-plans
   ```

---

**Guardrails**

- Never scaffold without an explicit user description — the AskUserQuestion in Step 1 is non-negotiable.
- Never auto-tick the review checklist — that's the human's responsibility.
- Never silently overwrite an existing change folder — confirm via AskUserQuestion before passing `--force`.
- Never bypass `validate-tasks.sh` — if the schema fails, fix and re-validate; do not claim done.
- All script paths use `${CLAUDE_PLUGIN_ROOT}` — never hardcode absolute paths.
- Honor `MORKIT_ROOT` env if set in the user's shell.
