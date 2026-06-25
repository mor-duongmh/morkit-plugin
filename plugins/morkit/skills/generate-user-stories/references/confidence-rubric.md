# G2 Confidence Rubric — self-scoring + coverage map

> Used by `generate-user-stories` (Stage G2) to decide **where human attention is
> worth spending**. The skill self-scores each candidate story on 3 signals and
> builds a coverage map; only **low-confidence** items and **zero-coverage** areas
> trigger interactive Q&A (the rest pass to the G2 confirm gate). Depth therefore
> adapts to G1 input quality — rich brainstorm → few flags → light gate; thin
> brainstorm → many flags → more Q&A.
>
> These are **working metadata** (drive Q&A selection + the gate review-aid). They
> are NOT necessarily rendered into `user-story-list.md`.

## The 3 signals (per story)

Each candidate story carries three coarse self-assessments. Start coarse — tune
thresholds only when a real project proves them wrong (YAGNI).

| Signal | Values | `high`/`ok`/`stated` when… | `low`/`weak`/`inferred` when… | Failure mode it guards |
|---|---|---|---|---|
| `source_strength` | high \| low | the fact is a **direct statement** in `source-manifest.json` (quotable `ref`) | the story is **derived/extrapolated** from a vaguer fact | fiction · wrong-domain |
| `field_completeness` | ok \| weak | actor + goal + **concrete, testable acceptance** all present and non-generic | acceptance missing / boilerplate ("works correctly"), or actor/goal vague | shallow / generic |
| `interpretation` | stated \| inferred | the customer **said this** (manifest fact maps 1:1 to the story) | the AI **filled a gap** by reasoning about what they probably meant | wrong-domain |

A story is **flagged** (needs Q&A) if ANY signal is low/weak/inferred.
A story is **high-confidence** (gate-only, no Q&A) if all three are high/ok/stated.

## Coverage map (across stories)

Detects the **missing** failure mode — what is *absent* can't be scored per-story.

1. From `brainstorm-report.md` (G1), enumerate the **function-areas** implied by:
   actors/roles, named modules/subsystems, and `Overview.in_scope` items.
2. For each area, mark whether ≥1 story covers it.
3. Areas with **0 stories** → coverage questions (see below).
4. A **near-empty** coverage map (most areas have 0 stories) is a signal that **G1
   itself is thin** — surface this to the BrSE (manual G2→G1 revisit). Automated
   G2→G1 loop-back is deferred to v2.

## No-fiction enforcement (B1)

Hard rule (conventions §6–§7): **every emitted row carries a `source_ref`.** A
candidate with no traceable source is NOT written as a story — it becomes either a
B3 question (`interpretation: inferred`) or a G3 gap. Never invent a row to look
complete. Assert "**0 stories without `source_ref`**" before producing the list.

## Signal → question mapping (B3)

Generate one targeted question per flag, grouped by story/area, into
`g2-clarification-log.md` (same table shape as `clarification-loop`'s
`clarification-log-template.md` — reuse it, do not invent a new format):

| Trigger | Question template (lang-localized) |
|---|---|
| `interpretation: inferred` | "Story này tôi **suy luận** từ «{source fact}» — đúng ý không, hay cần sửa actor/phạm vi?" |
| `field_completeness: weak` | "Story «{title}» chưa có tiêu chí chấp nhận cụ thể — **điều kiện nào** coi là xong?" |
| `source_strength: low` (no usable ref) | "«{candidate}» không có nguồn rõ — đây là yêu cầu thật, hay nên bỏ / chuyển thành câu hỏi?" |
| coverage area with 0 stories | "Vùng «{area}» chưa có story nào — **bỏ có chủ đích**, hay tôi còn thiếu?" |

High-confidence stories are **listed for awareness only** — the BrSE can
batch-confirm them at the gate without per-story interrogation (respect the
operator's time; bias toward flagging only genuine uncertainty).

## Review-aid summary (B4 → feeds the G2 gate)

After Q&A converges, emit a compact summary the orchestrator's G2 gate presents:

```
G2 review-aid:
  stories: N total  (M interactively confirmed · K high-confidence auto)
  fiction: 0  (all rows carry source_ref)
  coverage: <areas covered>/<areas total>  — deferred: {area, …}
  still-open: {Q-IDs forwarded / unanswered}  → carry to G3 as gaps / <TBD>
```

The gate decision maps to `state_manager set-gate --stage G2`:
`Proceed` → `proceed` · `Another round` → `adjust` (re-run B2–B3) · `Abort` halts.
