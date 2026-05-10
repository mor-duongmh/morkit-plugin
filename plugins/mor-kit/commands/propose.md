---
name: "mor-kit:propose"
description: Propose a new spec change - create the change folder and generate all artifacts (proposal, design, TDD-ready tasks, review-checklist) in one step. Self-contained — no OpenSpec dependency.
category: Workflow
tags: [spec, propose, superpowers, scaffold]
---

Invoke the `propose` skill using the Skill tool. Pass through any arguments the user provided.

The skill will:
- Scaffold a new change folder under `${MOR_KIT_ROOT:-mor-kit/changes}/<name>/`
- Generate `proposal.md` (what & why)
- Generate `design.md` (how, including Tech Stack — verify libraries via Context7)
- Generate `tasks.md` with Superpowers header + TDD steps
- Generate `.meta.json` (name, created_at, schema_version, archived flag)
- Auto-call `/mor-kit:review` to generate `review-checklist.md`
- Validate the produced `tasks.md` against rules R1-R6

When all artifacts are ready, the user can implement via:
- `/superpowers:executing-plans` (plugin's native runner — gated by review-checklist), or
- `/superpowers:executing-plans`, or
- `/superpowers:subagent-driven-development`
