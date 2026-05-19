---
name: review
description: 'Generate the developer review checklist (human gate) for a morkit change, blocking implementation skills until the human flips "Overall Decision: OK". Triggered by /morkit:review or after /morkit:propose finishes.'
license: MIT
---

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

3. **Report status to the user.**

   Print:
   - The path of the generated checklist
   - The detected/used variant
   - A clear instruction to:
     1. Open the file
     2. Tick the items honestly
     3. Fill in the **Review Summary** section
     4. Change the bottom marker from `Overall Decision: PENDING` to `Overall Decision: OK`
     5. Re-run `/morkit:executing-plans` (or `/morkit:executing-plans` / `/morkit:subagent-driven-development`) — the plugin's hook will allow it.

   If `review-checklist.md` already existed and contained `Overall Decision: OK`, mention this and ask via **AskUserQuestion** whether the user wants to overwrite (regenerate) — flipping back to `PENDING` requires re-approval.

---

**Guardrails**

- Never silently overwrite an approved checklist (`Overall Decision: OK`). Confirm via AskUserQuestion first.
- Never modify the user's checklist content beyond regeneration. Don't auto-tick items, don't auto-flip the decision.
- Never disable or bypass the PreToolUse hook from this skill. The hook is the enforcement layer; this skill is the generator.
- When `--refresh` is used, the cache is updated; the user sees the updated content next time too.

---

**Example output**

```
✓ Wrote /path/to/openspec/changes/add-csv-export/review-checklist.md
  Variant: BE - Feature

Next steps:
  1. Open the file and review each section
  2. Tick the items, fill the Review Summary
  3. Change "Overall Decision: PENDING" → "Overall Decision: OK"
  4. Run /morkit:executing-plans (or /morkit:subagent-driven-development for parallel TDD)

The plugin's PreToolUse hook will block those skills until the decision is OK.
```
