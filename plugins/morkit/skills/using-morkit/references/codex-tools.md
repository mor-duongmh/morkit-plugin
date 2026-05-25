# Codex Tool Mapping

Skills use Claude Code tool names. When you encounter these in a skill, use your platform equivalent:

| Skill references | Codex equivalent |
|-----------------|------------------|
| `Task` tool (dispatch subagent) | `spawn_agent` (see [Named agent dispatch](#named-agent-dispatch)) |
| Multiple `Task` calls (parallel) | Multiple `spawn_agent` calls |
| Task returns result | `wait` |
| Task completes automatically | `close_agent` to free slot |
| `TodoWrite` (task tracking) | `update_plan` |
| `Skill` tool (invoke a skill) | Skills load natively — just follow the instructions |
| `Read`, `Write`, `Edit` (files) | Use your native file tools |
| `Bash` (run commands) | Use your native shell tools |
| `${CLAUDE_PLUGIN_ROOT}` (plugin path) | `${MORKIT_PLUGIN_ROOT}` (see [Plugin root resolution](#plugin-root-resolution)) |

## Plugin root resolution

Skills/scripts reference the plugin install dir via a cascade:
`${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-<derived>}}`. In Codex the canonical
var is **`MORKIT_PLUGIN_ROOT`** — exported into your shell rc by
`scripts/install-codex.sh` (it also aliases `CLAUDE_PLUGIN_ROOT` to the same value
for legacy refs). No file rewriting is needed: the same Claude-vocab skill files
resolve correctly on both harnesses through this cascade. If `MORKIT_PLUGIN_ROOT`
is unset, re-run `install-codex.sh` or `export` it to your morkit checkout's
`plugins/morkit`.

## Subagent dispatch requires multi-agent support

Add to your Codex config (`~/.codex/config.toml`):

```toml
[features]
multi_agent = true
```

This enables `spawn_agent`, `wait`, and `close_agent` for skills like `dispatching-parallel-agents` and `subagent-driven-development`.

## Named agent dispatch

Claude Code skills reference named agent types like `morkit:code-reviewer`.
Codex does not have a named agent registry — `spawn_agent` creates generic agents
from built-in roles (`default`, `explorer`, `worker`).

When a skill says to dispatch a named agent type:

1. Find the agent's prompt file (e.g., `agents/code-reviewer.md` or the skill's
   local prompt template like `code-quality-reviewer-prompt.md`)
2. Read the prompt content
3. Fill any template placeholders (`{BASE_SHA}`, `{WHAT_WAS_IMPLEMENTED}`, etc.)
4. Spawn a `worker` agent with the filled content as the `message`

| Skill instruction | Codex equivalent |
|-------------------|------------------|
| `Task tool (morkit:code-reviewer)` | `spawn_agent(agent_type="worker", message=...)` with `code-reviewer.md` content |
| `Task tool (general-purpose)` with inline prompt | `spawn_agent(message=...)` with the same prompt |

### Message framing

The `message` parameter is user-level input, not a system prompt. Structure it
for maximum instruction adherence:

```
Your task is to perform the following. Follow the instructions below exactly.

<agent-instructions>
[filled prompt content from the agent's .md file]
</agent-instructions>

Execute this now. Output ONLY the structured response following the format
specified in the instructions above.
```

- Use task-delegation framing ("Your task is...") rather than persona framing ("You are...")
- Wrap instructions in XML tags — the model treats tagged blocks as authoritative
- End with an explicit execution directive to prevent summarization of the instructions

### When this workaround can be removed

This approach compensates for Codex's plugin system not yet supporting an `agents`
field in `plugin.json`. When `RawPluginManifest` gains an `agents` field, the
plugin can symlink to `agents/` (mirroring the existing `skills/` symlink) and
skills can dispatch named agent types directly.

## Codex executing-plans pre-flight (checklist gate)

The plugin's PreToolUse hook (`hooks/pre-tool-checklist-gate.sh`) blocks
`apply_patch` / `Edit` / `Write` until the active change's `review-checklist.md`
has `Overall Decision: OK`. In Codex there is no `Skill` tool, so the hook narrows
by env var: **if `MORKIT_CURRENT_CHANGE` is unset, the gate fails open** and file
edits proceed unguarded.

**BEFORE issuing any file edit while running `executing-plans` /
`subagent-driven-development`** (and before dispatching implementer subagents,
which inherit the controller's env), export the active change name so the gate can
resolve `${MORKIT_ROOT:-morkit/output/spec}/$MORKIT_CURRENT_CHANGE`:

```bash
# Detect the active change (most recently modified non-archive dir), export basename.
CHANGE_DIR=$(find "${MORKIT_ROOT:-morkit/output/spec}" \
                  -mindepth 1 -maxdepth 1 -type d ! -name archive -print0 \
                  2>/dev/null \
    | xargs -0 -I{} sh -c \
        'stat -f "%m %N" "$1" 2>/dev/null || stat -c "%Y %n" "$1"' _ {} \
    | sort -rn | head -1 | sed 's/^[0-9]* //')

if [[ -n "$CHANGE_DIR" ]]; then
    export MORKIT_CURRENT_CHANGE="$(basename "$CHANGE_DIR")"
fi
```

If `MORKIT_CURRENT_CHANGE` is already set leave it alone — the snippet only
auto-detects when unset. The gate only engages when Codex hooks are enabled
(`install-codex.sh --with-hooks` + `codex features enable codex_hooks`); see the
Advisory note in `AGENTS.md`.

## Environment Detection

Skills that create worktrees or finish branches should detect their
environment with read-only git commands before proceeding:

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

- `GIT_DIR != GIT_COMMON` → already in a linked worktree (skip creation)
- `BRANCH` empty → detached HEAD (cannot branch/push/PR from sandbox)

See `using-git-worktrees` Step 0 and `finishing-a-development-branch`
Step 1 for how each skill uses these signals.

## Codex App Finishing

When the sandbox blocks branch/push operations (detached HEAD in an
externally managed worktree), the agent commits all work and informs
the user to use the App's native controls:

- **"Create branch"** — names the branch, then commit/push/PR via App UI
- **"Hand off to local"** — transfers work to the user's local checkout

The agent can still run tests, stage files, and output suggested branch
names, commit messages, and PR descriptions for the user to copy.
