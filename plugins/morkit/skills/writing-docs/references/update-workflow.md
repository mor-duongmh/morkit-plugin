# Update Workflow

`/morkit:docs update [path]`

Refresh an existing doc taxonomy against code changes. Manual/on-demand (no auto-sync). Uses front-matter `source_files` to find what drifted.

## Preconditions
- `docs/` already holds a new-style taxonomy (`00-overview/` exists). If not → tell user to run `/morkit:init`.

## Steps

1. **Detect drift candidates.** For each doc with front-matter `source_files`, check whether those paths changed since the doc's `updated` date (git log / mtime). Build a list of stale docs.
2. **Scope confirm.** Present the stale list; ask which to update (default: all). Allow `--yes` to skip.
3. **Re-scout only the changed areas** (not the whole repo) — morkit-native dispatch, read-only.
4. **Update content docs first**, then re-derive affected MAP/anchor files (same Scout → Content → MAP order, scoped).
5. **New components?** If scout finds a component with no folder yet (e.g. a DB was added), create the conditional folder + its doc.
6. **Bump `updated`** on every touched file; preserve manual edits outside the regenerated sections where possible.
6b. **Refresh agent-instructions** (`references/agent-instructions.md`): rebuild the root agent-instruction pointer block your harness auto-loads (`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex; + the other if detected) from the current docs. Expect state `[C]` — replace ONLY inside the marker; if the marker is gone, treat as `[B]` (append at end). No-op if unchanged. Approve gate per file.
7. **Validate** (same checks as init Stage 5): size, cross-links, front-matter, traceability.
8. **Report**: docs updated, docs newly created, links fixed, agent-instructions touched, remaining gaps.

## Notes
- Auto-sync / diff-engine is intentionally out of scope (KISS). This is a guided manual refresh.
- Never silently overwrite a heavily hand-edited doc — if a doc diverged a lot from its `source_files`, surface it and ask.
