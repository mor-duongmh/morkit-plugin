---
name: clarification-loop
description: "The S4 human-in-the-loop for /morkit:greenfield. AI generates clarifying questions per user-story/gap into clarification-log.md; BA/BrSE answers inline or marks forwarded→<stakeholder>; on re-run AI ingests answers, updates the ProjectModel OpenQuestion/FR detail, and fills <TBD> placeholders. Async + multi-session: all state lives in the markdown file so the loop resumes from the file alone. Closed Q&A renders into SRS §12."
category: documentation
keywords: [clarification, open-questions, human-in-the-loop, greenfield, srs, resume, ba]
argument-hint: "--workspace morkit/output/greenfield/<proj>"
metadata:
  author: morkit-greenfield
  version: "1.0.0"
---

# Clarification Loop

Stage **G4** of `/morkit:greenfield`. Closes the open questions raised at G3
before the bridge (G5) freezes the ProjectModel.

> Conventions: [`../greenfield-orchestrator/references/greenfield-conventions.md`](../greenfield-orchestrator/references/greenfield-conventions.md).
> Template: [`templates/clarification-log-template.md`](templates/clarification-log-template.md).

## Depth decision (locked: template-only)

Per the plan's deferred decision, this skill ships **template-only**:
- **State = the markdown table.** No tracker code, no deadlines/reminders engine.
- Resume by re-reading `clarification-log.md`. Matches KISS/YAGNI.
- **State-machine depth (deadlines, stakeholder owners, reminders) is deferred to
  v2** — add it only if a real project proves template-only insufficient.

## Inputs

From the run workspace `morkit/output/greenfield/<proj>/`:
- `user-story-list.md` (G2), `gap-analysis.md` (G3) — what to question.
- `clarification-log.md` — prior rounds' state (created on round 1).
- ProjectModel `open_questions[]` (once the bridge has run) / any `<TBD: …>` markers.

## Round logic

1. **Generate (round N):** from open `<TBD>` markers, G3 gaps, and existing
   `OpenQuestion`s, emit grouped questions into `clarification-log.md` (per US/gap).
   Each `Q-00x` starts `status: open`. Do **not** invent answers.
2. **Ingest (re-run, round N+1):** parse the log. For each `answered` row, update
   the target FR detail / fill its `<TBD>`, set `Resolved-FR`, and mark the matching
   `OpenQuestion.q_status = Answered`. `forwarded` rows stay open (still waiting on a
   stakeholder). Report the remaining open count for the gate.
3. **G4 GATE — enough-answered / force-close:** via `AskUserQuestion`, either close
   the loop (open-count ≤ threshold, or BA forces) or run another round. Persist the
   decision into `state.json` (`stages.G4.gate`).
4. **Closure:** on close, answered Q&A flows (via the bridge) into ProjectModel
   `open_questions` → SRS §12. Unanswered/forwarded questions carry forward as
   `<TBD>` / `Open` — never silently dropped.

## Resume guarantee

Because the only state is `clarification-log.md`, the loop survives across sessions
and days: re-invoking the skill on the same workspace continues exactly where it
left off. Use a strict table format (template columns) so answer parsing is robust.

## Anti-patterns

- ❌ Inventing an answer to close a question faster → violates the no-fiction rule.
- ❌ Looping forever → the G4 gate always offers force-close.
- ❌ A second state store (DB/json) → state is the log file only (template-only depth).
