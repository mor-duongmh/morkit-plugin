---
name: "morkit:brainstorming"
description: Enter explore mode - a thinking partner for exploring ideas, investigating problems, and clarifying requirements before creating a change proposal.
category: Workflow
tags: [spec, brainstorming, explore, thinking]
---

Invoke the `brainstorming` skill using the Skill tool. Pass through any arguments the user provided.

The skill puts Claude into explore mode: a curious, adaptive thinking partner that asks questions, surfaces multiple directions, draws ASCII diagrams, and investigates the codebase — but does NOT write code or implement features.

At session end, the skill auto-saves a design log to `${MORKIT_ROOT:-morkit/output}/specs/YYYY-MM-DD-<topic>-design.md` (5 sections: problem framing · approaches considered · decisions · open questions · next step).

When the user is ready to commit to a change, run `/morkit:propose <name>` to generate the full proposal + design + tasks artifacts.
