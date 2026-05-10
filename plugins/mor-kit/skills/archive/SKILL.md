---
name: archive
description: Archive a completed mor-kit change. Moves it from active to archive subfolder and updates .meta.json. Use when implementation is complete and merged.
license: MIT
---

Archive a completed change by moving it from `${MOR_KIT_ROOT:-mor-kit/changes}/<name>/` to `${MOR_KIT_ROOT:-mor-kit/changes}/archive/<name>/` and updating `.meta.json.archived` + `archived_at`.

**Input:** Optionally specify a change name. If omitted, list active changes and prompt.

---

**Steps**

1. **Select the change to archive**

   List active changes (excluding archive/):
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/list-changes.sh" --json
   ```

   If no name was provided, use **AskUserQuestion tool** to let the user pick.
   Show only changes whose `tasks.md` is fully ticked (no remaining `- [ ]`) by default; surface partial ones with a warning.

   **Do NOT auto-select.**

2. **Sanity check completion**

   - Verify all tasks are done:
     ```bash
     pending=$(grep -cE '^[[:space:]]*-[[:space:]]+\[[[:space:]]\]' "$CHANGE_DIR/tasks.md" || echo 0)
     ```
     If `$pending > 0`, ask via AskUserQuestion whether to archive anyway.

3. **Move to archive**

   ```bash
   ROOT="${MOR_KIT_ROOT:-mor-kit/changes}"
   mkdir -p "$ROOT/archive"
   mv "$ROOT/<name>" "$ROOT/archive/<name>"
   ```

4. **Update `.meta.json`**

   ```bash
   META="$ROOT/archive/<name>/.meta.json"
   tmp="$(mktemp)"
   jq --arg ts "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
      '.archived = true | .archived_at = $ts' \
      "$META" > "$tmp" && mv "$tmp" "$META"
   ```

5. **Report**

   ```
   ✓ Archived <name>
     From: <root>/<name>/
     To:   <root>/archive/<name>/
     Archived at: <ts>
   ```

---

**Guardrails**

- Never archive without user confirmation when the change has pending tasks.
- Never delete the archive folder — `mv` only.
- Never silently overwrite an existing archive entry — if `archive/<name>` exists, ask.
- Honor `MOR_KIT_ROOT` env.
