# Agent Instructions (CLAUDE.md / AGENTS.md)

Generate and maintain a **thin pointer** in the project's root agent-instruction files so a cold-start
agent is sent into the `docs/` graph. This is the ONLY skill output allowed outside `docs/` —
because only `CLAUDE.md` (Claude Code) / `AGENTS.md` (Codex) are auto-loaded by the harness.

**Invariant:** the skill owns ONLY the marker block below. Never touch anything outside it.

## Which files

- **`CLAUDE.md`** — ALWAYS generate (primary target is Claude Code).
- **`AGENTS.md`** — ONLY when Codex usage is detected; same block content as CLAUDE.md, different wrapper file.

Codex detected if ANY of:
- `AGENTS.md` already exists at the target root, OR
- a Codex config is present (`.codex/`, or a nested `AGENTS.md`), OR
- the user passed `--agents`.

No signal → generate `CLAUDE.md` only; do NOT create a stray `AGENTS.md`.

## The block (B-refined: orientation + task pointers)

```markdown
<!-- morkit:docs:start (auto-generated pointer — edit docs/, not here) -->
## <Project Name> — for AI agents

<1–2 sentences: what this project is, who it serves, primary stack>

Project docs live in `docs/` — load minimal context per task, don't read everything:
- **Understand the project** (scope, architecture) → [docs/00-overview/DOCUMENT-MAP.md](docs/00-overview/DOCUMENT-MAP.md)
- **Before changing code** (rules + read order) → [docs/40-ai-coding/AI-CODING-GUIDE.md](docs/40-ai-coding/AI-CODING-GUIDE.md)
- **Must not break** → [docs/20-design/00-core/INVARIANTS.md](docs/20-design/00-core/INVARIANTS.md)
<!-- morkit:docs:end -->
```

- **Orientation line** is sourced from the opening sentence of `DOCUMENT-MAP` / root `README` (one source — copied as a snippet, refreshed by `update`).
- **Pointer-only.** Do NOT inline invariants or copy doc content (keep DRY; the truth lives in the linked docs).
- Drop a pointer line if its target was not generated (e.g. no `INVARIANTS.md`).

## State machine (per file)

```
[A] FILE MISSING        → build block → gate → write file = "# <Project>" header + block
[B] EXISTS, no marker   → build block → gate → APPEND block at the END of the file
                          (leave everything above untouched)
[C] EXISTS, has marker  → compare current block vs freshly built block
                          · identical → no-op, report "up to date"
                          · differs   → show diff → gate → replace ONLY the text between markers
```

`[B]` always appends at the **end** — never reorder or rewrite the user's hand-written lead content.

## Approve gate (two layers)

1. **Skill-level (explicit):** `AskUserQuestion` stating intent before writing
   (header "Agent Instructions", e.g. "Write the morkit docs pointer into CLAUDE.md?" → Apply / Skip).
   Required for Codex parity and to surface intent up front.
2. **Harness-level (automatic):** the `Edit`/`Write` tool shows a unified diff + native permission prompt.

Never write silently. One gate per file (CLAUDE.md and AGENTS.md approved separately — diffs differ).

## Relative paths

- **project-level:** `CLAUDE.md` at root → `docs/00-overview/DOCUMENT-MAP.md` (relative from root).
- **per-module:** `CLAUDE.md` at the module root (e.g. `packages/<mod>/CLAUDE.md`) → that module's docs,
  e.g. `../../docs/m/<mod>/00-overview/DOCUMENT-MAP.md` (or the module's local `docs/`). One pointer per module.

## No-Python / KISS

No hash, no checksum, no 3-way merge — the human gate is the safety mechanism (every change is reviewed).
If stricter detection is needed later, add a `v=N` version tag inside the start marker (LLM-readable).
