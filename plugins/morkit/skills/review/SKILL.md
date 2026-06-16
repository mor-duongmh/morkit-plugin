---
name: review
description: 'Generate the developer review checklist (human gate) for a morkit change, blocking implementation skills until the human flips "Overall Decision: OK". Triggered by /morkit:review or after /morkit:propose finishes.'
license: MIT
---

# Review checklist (human gate)

Generate or refresh the **developer review checklist** for a morkit change. This file is the human gate that the plugin's PreToolUse hook checks before allowing implementation skills to run.

The skill never modifies the user's review judgement — it only prepares the file. The human is the one who reads, ticks, and flips the decision.

---

**Inputs (parsed from the user's invocation):**

- `[change-name]` — optional; otherwise pick the most recently modified change folder under `${MORKIT_ROOT:-morkit/output/spec}/` (excluding `archive/`).
- `--refresh` — force re-fetch the canonical Google Doc, bypassing the 24h cache.
- `--variant <id>` — override auto-detection; valid: `BE-Feature`, `BE-BugFix`, `BE-Refactor`, `FE-Feature`, `FE-BugFix`, `FE-Refactor`.

---

**Steps**

1. **Resolve change directory.**

   - If a name was provided, set `CHANGE_DIR="${MORKIT_ROOT:-morkit/output/spec}/<name>"` and verify it exists.
   - Otherwise, find the most recent non-archive folder:
     ```bash
     ROOT="${MORKIT_ROOT:-morkit/output/spec}"
     CHANGE_DIR=$(find "$ROOT" -mindepth 1 -maxdepth 1 -type d ! -name archive \
       -exec stat -f "%m %N" {} \; 2>/dev/null \
       | sort -rn | head -1 | awk '{print $2}')
     ```
     (Use `stat -c "%Y %n"` on Linux.)

   - If no change folder exists, stop and tell the user to run `/morkit:propose` first.

2. **Generate the checklist.**

   Run the helper script bundled with the plugin:
   ```bash
   "${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/generate-checklist.sh" "$CHANGE_DIR" [--refresh] [--variant <id>]
   ```

   The script will:
   - Fetch the Mor Developer Review Checklist Google Doc (cached locally; 24h TTL).
   - Auto-detect or accept the override variant.
   - Extract the matching section.
   - Write `<change-dir>/review-checklist.md` with a header, the variant section, and the gate footer (`Overall Decision: PENDING`).

   On failure, the script prints a clear error explaining whether the issue is fetch (network/sharing), variant detection, or missing files.

3. **Offer a native tick widget (preferred path).**

   The generated file now uses real `- [ ]` checkboxes. When the `mcp__visualize__show_widget` tool is available, let the user tick items directly in chat instead of editing the file by hand.

   - **Parse** the items from `review-checklist.md`: read the `- [ ]` lines, grouped by their `###` section headings. Assign each item a stable **item-id** = its 1-based index among all `- [ ]` lines in the file, counted top-to-bottom across every section (the 1st checkbox is `1`, the 2nd is `2`, …). For each item, capture any trailing ref codes like `[A1]` / `[C1]` (Security references) so they can be shown beside the item. Do **not** embed the whole "Tham khảo Security" section — just the codes.
   - **Render** an interactive tick table via `mcp__visualize__show_widget` (HTML mode): a checklist grouped by section heading, each item offering a 3-state choice — **Pass** / **Fail** / **N/A** — with its ref codes shown inline. The widget must carry each item's item-id so the round-trip is unambiguous. Include a **Submit** button whose handler calls the global `sendPrompt(text)` to return the per-item state as a compact payload — one line per item: `<item-id>=pass|fail|na`.
   - **Transcribe** each submitted state back onto the exact `- [ ]` line identified by its item-id (the Nth checkbox line in the file), so wording collisions across sections cannot misroute a state:
     - Pass → `- [x]`
     - Fail → `- [ ]`
     - N/A → `- [~]`
   - When the user approves overall, set the footer to `Overall Decision: OK`. Do **not** force `PENDING` even if some Security items are left unticked — the human decides (see guardrails).

   **Guardrail:** transcribe **only** what the user actually submitted. Never auto-tick an item, never infer a state the user did not choose, and never auto-set `Overall Decision: OK`. If the widget returns nothing (user closed it without submitting), leave the file unchanged and fall back to step 3a.

   **3a. Fallback when the widget tool is unavailable.**

   If `mcp__visualize__show_widget` is not present (e.g. an install without that MCP), fall back to the previous behavior: instruct the user to tick the `- [ ]` boxes directly in `review-checklist.md` and set `Overall Decision: OK` themselves. Because the file now contains real `- [ ]` checkboxes, it is tickable in any editor either way — Pass → `- [x]`, Fail → leave `- [ ]`, N/A → `- [~]`.

4. **Report status to the user.**

   Print:
   - The path of the generated checklist
   - The detected/used variant
   - A clear instruction to:
     1. Open the file (or use the tick widget above)
     2. Tick the items honestly
     3. Fill in the **Review Summary** section
     4. Change the bottom marker from `Overall Decision: PENDING` to `Overall Decision: OK`
     5. Re-run `/morkit:executing-plans` (or `/morkit:executing-plans` / `/morkit:subagent-driven-development`) — the plugin's hook will allow it.

   If `review-checklist.md` already existed and contained `Overall Decision: OK`, mention this and ask via **AskUserQuestion** whether the user wants to overwrite (regenerate) — flipping back to `PENDING` requires re-approval.

---

**Guardrails**

- Never silently overwrite an approved checklist (`Overall Decision: OK`). Confirm via AskUserQuestion first.
- Never modify the user's checklist content beyond regeneration. Don't auto-tick items, don't auto-flip the decision.
- When transcribing a tick-widget submission, write **only** the states the user submitted (Pass → `- [x]`, Fail → `- [ ]`, N/A → `- [~]`) and set `Overall Decision: OK` only on the user's explicit approval. Never auto-tick, auto-fail, or auto-approve. The human decides — unticked Security items do not force `PENDING`.
- Never disable or bypass the PreToolUse hook from this skill. The hook is the enforcement layer; this skill is the generator.
- When `--refresh` is used, the cache is updated; the user sees the updated content next time too.

---

**Example output**

```
✓ Wrote /path/to/morkit/output/spec/add-csv-export/review-checklist.md
  Variant: BE - Feature

Next steps:
  1. Open the file and review each section
  2. Tick the items, fill the Review Summary
  3. Change "Overall Decision: PENDING" → "Overall Decision: OK"
  4. Run /morkit:executing-plans (or /morkit:subagent-driven-development for parallel TDD)

The plugin's PreToolUse hook will block those skills until the decision is OK.
```
