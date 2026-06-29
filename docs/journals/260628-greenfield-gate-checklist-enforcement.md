# Greenfield Gate Checklist Enforcement — Hard-Block Integration

**Date**: 2026-06-28 09:34
**Severity**: High
**Component**: `plugins/morkit/skills/greenfield-orchestrator/`, `state_manager.py`, `validate_state.py`, gate checklists (G2/G3/G4/G6)
**Status**: Resolved

## What Happened

Integrated the 4 human-gate checklists (G2/G3/G4/G6) into the `/morkit:greenfield` orchestrator workflow as hard-block gates. This reversed a deliberate prior decision — checklists' README headers stated "thủ công… KHÔNG nối vào workflow" (manual, NOT wired to workflow). The reversal was user-approved via brainstorm→plan→cook.

**Delivered**: `checklist_loader.py` (venv-compatible front-matter parser, no PyYAML), 4 canonical checklists relocated into skill refs (`plugins/morkit/skills/greenfield-orchestrator/references/gate-checklists/`), modified `state_manager.py` + `validate_state.py` + `state.schema.json`, updated skill docs, new gate integration tests. **42/42 tests pass.** Code review: DONE_WITH_CONCERNS (2 LOW parser edge cases fixed + regression-tested).

## The Brutal Truth

This work exposed a foundational gap in the existing pipeline: **`state_manager.advance()` had zero gate enforcement logic**. For 10 days, the orchestrator *assumed* the LLM agent would obey prose instructions ("do not advance until G4 decision is set"). That was net-zero protection. Hard-block was not a tweak — it was table-stakes missing capability that should have existed from launch.

The second sting: checklists lived at `docs/templates/` (repo root), which is NOT shipped inside the morkit plugin. Machine-read copies *must* live in the plugin. So the checklists had to physically MOVE to avoid drift — `docs/templates/` copies became thin pointers. A packaging insight forced a design choice that broke an implicit assumption (checklist source of truth).

## Technical Details

**The No-Guard Discovery**
- Prior code: `state_manager.advance(stage_slug)` → checks stage sequence, locks previous stage, increments to next stage. **Zero guard for gates.**
- Gate decision recorded: `state["stages"][stage_slug]["decision"]` (set by `set_gate` or LLM).
- But `advance()` never checked `decision` or required confirmed items before moving forward.
- New contract: `advance()` now checks `if stage_slug in GATED_STAGES` → must have `decision == "proceed"` AND `confirmed ⊇ required` (subset check). Raises `GateBlockedError` with remediation hint.
- G4 (`force-close`) allowed escape: can leave with non-empty note even if not all required items confirmed.

**Checklist Packaging & Relocation**
- Original: `docs/templates/{checklist-name}.md` (human-read only, not shipped in plugin).
- Canonical: `plugins/morkit/skills/greenfield-orchestrator/references/gate-checklists/{checklist-name}.md` (shipped, machine-read).
- Pointer stubs: `docs/templates/` copies now link to canonical + housekeeping note.
- **Single source of truth**: Only one editable copy; plugin refs are authoritative.

**Front-Matter Parser (Zero Dependencies)**
- Each checklist opens with YAML front-matter: `required: [item-1, item-2, …]`.
- `checklist_loader.py` parses front-matter (regex split on `---`, YAML parse, fallback to dict constructor for edge cases).
- Handles Python 3.9 (venv has no PyYAML); built regex/dict parser (~80 lines, tested for commas-in-quoted-values + missing-bold-title edge cases).
- On parse failure, returns empty `required=[]` (silent fallback; logs WARN; gate allows advance if none specified).

**State Schema & Validation**
- `state.schema.json` extended: `stages.{slug}.checklist = {name, required, confirmed, notes}`.
- `validate_state.py` loads checklist on gate set; stores `required` + `confirmed` (confirmed initially empty).
- `set_gate --decision proceed --confirmed [item-1, item-2]` atomically updates state.
- Non-breaking: legacy state (no `checklist` key) still advances (checks skipped if checklist missing).

**Tests**
- New: `test_checklist_loader.py` (12 tests: valid YAML, missing front-matter, quoted commas, malformed bold titles, empty required).
- New: `test_gate_integration.py` (18 tests: blocked advance, escape via force-close, subset validation, legacy state compat).
- Modified: `test_state_manager.py` (2 existing `test_advance_*` tests adapted to new gate contract).
- All 42/42 pass; TDD (RED→GREEN throughout).

## What We Tried

1. **Brainstorm (User-Approved)**
   - Proposal A1 (Deferred): Checklist items as JSON enum in state schema (static, tight coupling).
   - Proposal A2 (Chosen): Front-matter `required` subset per checklist (single source, user editable).
   - A2 approved because operators can tweak required items without code change; gate logic stays in Python.

2. **Implementation Phase 1: Parser**
   - Tried: Import PyYAML (not in venv). Fallback: regex + dict constructor (works for flat front-matter; tested 5 edge cases).
   - Decided: Dependency-free parser (venv constraint is permanent; PyYAML not planned for skills).

3. **Implementation Phase 2: Relocation**
   - Tried: Keep checklists in `docs/templates/`, load from repo root in skill. Rejected: checklists not shipped in plugin; offline divergence inevitable.
   - Decided: Copy to canonical location in plugin; update pointer stubs in `docs/templates/`.

4. **Code Review Feedback**
   - **LOW-1 (FIXED)**: Parser silently accepted commas inside quoted values (e.g., `"item, part A"` splits wrong). Fixed: regex now respects quotes + added regression test.
   - **LOW-2 (FIXED)**: Parser crashed if item key lacked `**bold title**`. Fixed: fallback to item key as label; added test.

## Root Cause Analysis

**Why Was Gate Enforcement Missing?**
- Original design (260618) assumed LLM orchestrator agent would self-enforce prose rules ("respect G2 gate"). Worked in testing (human-like LLM); fails in production (LLMs hallucinate stage jumps, forget gate decisions).
- No test coverage existed for gate violation (tests mocked `advance()` success paths only).
- False confidence: state machine *recorded* gate decisions but never *checked* them.

**Why Did Checklists Have to Move?**
- Morkit plugin is distributed as a `.zip` with only `plugins/morkit/` contents (docs/ excluded).
- Checklist at `docs/templates/` → not shipped → LLM can't load it at runtime in plugin context.
- Solution forced by packaging: canonical copy in plugin, pointer stubs in repo docs (satisfies both offline reference + plugin distribution).

## Lessons Learned

1. **Gate Recording ≠ Gate Enforcement**: A state machine that *records* decisions but doesn't *check* them is theater. Hard-block (raise exception on violation) is the only reliable gate. LLMs will explore all paths; machines must enforce contracts.

2. **Reversing a Decision Requires Justification**: Checklists' README said "manual, not wired". This wasn't arbitrary — it was a deliberate trade-off (simpler initial MVP, operator decides when to advance). The reversal was sound (hard-block safety > simplicity), but it needed user approval + a story (provided in brainstorm).

3. **Packaging Constraints Drive Design**: Plugin distribution (zipfile, no repo root) meant `docs/templates/` copies were dead code. Single source of truth works only if it's in the shipped artifact. Early architecture review would have caught this.

4. **Zero-Dependency Parsing is Viable (But Brittle)**: Regex + dict constructor works for simple YAML (flat, no nesting). It breaks on commas-in-values + missing-keys silently. Justified here (venv constraint + low schema complexity), but not a pattern to replicate elsewhere.

5. **Fallback Behavior Matters**: Parser returns `required=[]` on failure (gate allows advance by default). This is safe (gate doesn't break pipeline) but risky (missing checklist silently allows proceed). Logged as WARN; acceptable for MVP. v2: require explicit checklist presence or fail hard.

## Next Steps

1. **Required Item Sign-Off**: The `required` ID sets per gate (e.g., G2 `{item-1, item-3}`) still need BA/BrSE validation. Currently placeholder IDs; confirm against actual checklist wording.

2. **Fallback Testing**: Have an LLM operator skip a gate (no checklist, no decision) and observe the "allow by default" behavior. Verify it's acceptable or tighten to "deny by default" in v2.

3. **Integration with Clarification Loop**: G4 (Clarification) allows `force-close` escape. Verify downstream workflows handle non-empty notes (escalation trigger vs silent skip).

4. **Docs Update**: Publish gate contract in `greenfield-conventions.md` (advance rules, escape hatches, fallback behavior).

5. **Plugin Release**: Re-zip plugin with relocated checklists; verify load-time checklist discovery works in distributed context.

**Owner**: (Maintainer to validate required item IDs, test with LLM orchestration, release)

---

**Source reports**:
- `/Users/dangtuanphong/Desktop/claude-plugins/plans/260628-0034-integrate-greenfield-gate-checklists/reports/` (code review, testing reports TBD)

**Plan**: `/Users/dangtuanphong/Desktop/claude-plugins/plans/260628-0034-integrate-greenfield-gate-checklists/`
