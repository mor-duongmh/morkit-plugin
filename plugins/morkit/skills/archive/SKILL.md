---
name: archive
description: Archive a completed morkit change. Moves it from active to archive subfolder and updates .meta.json. Use when implementation is complete and merged.
license: MIT
---

# Archive a change

Archive a completed change by moving it from `${MORKIT_ROOT:-morkit/output/spec}/<name>/` to `${MORKIT_ROOT:-morkit/output/spec}/archive/<name>/` and updating `.meta.json.archived` + `archived_at`.

**Input:** Optionally specify a change name. If omitted, list active changes and prompt.

---

**Steps**

1. **Select the change to archive**

   List active changes (excluding archive/):
   ```bash
   bash "${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/list-changes.sh" --json
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

3. **Docs bridge gate (soft — only when docs-hero is set up)**

   This change's `proposal`/`design`/`tasks`/`spec` only reach `docs/` via the
   docs bridge. Once archived, the change is out of bridge scope. So **before
   moving**, offer to bridge — but only if the project actually uses docs-hero
   (otherwise skip silently; never force a docs-hero dependency on spec-only users):

   ```bash
   # Gate condition: docs-hero venv + project meta both present
   VENV="${HOME}/.claude/plugins/data/docs-hero/.venv"
   if [ -d "$VENV" ] && [ -f "${PWD}/.docs-hero-meta.json" ]; then
     echo "docs-hero in use → offer bridge (AskUserQuestion below)"
   else
     echo "docs-hero not set up → skip gate, archive directly"
   fi
   ```

   If the gate condition holds, use **AskUserQuestion**:
   "Change `<name>` sắp được archive. Bridge nội dung vào `docs/` trước không?
   (sau khi archive, WHAT/WHY của change không vào được `docs/` nữa)"
   - `Bridge trước (khuyến nghị)` → run `/morkit:docs-update --from-openspec <name>`
     (preserves manual edits via the diff engine), then continue to the move.
   - `Archive luôn` → skip the bridge, continue.
   - `Hủy` → abort archive (do **not** move).

   If the gate condition is false, skip this step entirely.

4. **Move to archive**

   ```bash
   ROOT="${MORKIT_ROOT:-morkit/output/spec}"
   mkdir -p "$ROOT/archive"
   mv "$ROOT/<name>" "$ROOT/archive/<name>"
   ```

5. **Update `.meta.json`**

   ```bash
   META="$ROOT/archive/<name>/.meta.json"
   tmp="$(mktemp)"
   jq --arg ts "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
      '.archived = true | .archived_at = $ts' \
      "$META" > "$tmp" && mv "$tmp" "$META"
   ```

6. **Report**

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
- Honor `MORKIT_ROOT` env.
