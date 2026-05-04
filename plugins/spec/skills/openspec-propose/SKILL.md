---
name: openspec-propose
description: Propose a new change with all artifacts generated in one step. Use when the user wants to quickly describe what they want to build and get a complete proposal with design, specs, and tasks ready for implementation.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.3.0"
---

Propose a new change - create the change and generate all artifacts in one step.

I'll create a change with artifacts:
- proposal.md (what & why)
- design.md (how)
- tasks.md (implementation steps)

When ready to implement, run /spec:apply

---

**Input**: The user's request should include a change name (kebab-case) OR a description of what they want to build.

**Steps**

1. **If no clear input provided, ask what they want to build**

   Use the **AskUserQuestion tool** (open-ended, no preset options) to ask:
   > "What change do you want to work on? Describe what you want to build or fix."

   From their description, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).

   **IMPORTANT**: Do NOT proceed without understanding what the user wants to build.

2. **Create the change directory**
   ```bash
   npx -y @fission-ai/openspec@latest new change "<name>"
   ```
   This creates a scaffolded change at `openspec/changes/<name>/` with `.openspec.yaml`. All OpenSpec CLI calls in this skill MUST go through `npx -y @fission-ai/openspec@latest` — do not assume a global `openspec` binary exists.

3. **Get the artifact build order**
   ```bash
   npx -y @fission-ai/openspec@latest status --change "<name>" --json
   ```
   Parse the JSON to get:
   - `applyRequires`: array of artifact IDs needed before implementation (e.g., `["tasks"]`)
   - `artifacts`: list of all artifacts with their status and dependencies

4. **Create artifacts in sequence until apply-ready**

   Use the **TodoWrite tool** to track progress through the artifacts.

   Loop through artifacts in dependency order (artifacts with no pending dependencies first):

   a. **For each artifact that is `ready` (dependencies satisfied)**:
      - Get instructions:
        ```bash
        npx -y @fission-ai/openspec@latest instructions <artifact-id> --change "<name>" --json
        ```
      - The instructions JSON includes:
        - `context`: Project background (constraints for you - do NOT include in output)
        - `rules`: Artifact-specific rules (constraints for you - do NOT include in output)
        - `template`: The structure to use for your output file
        - `instruction`: Schema-specific guidance for this artifact type
        - `outputPath`: Where to write the artifact
        - `dependencies`: Completed artifacts to read for context
      - Read any completed dependency files for context
      - Create the artifact file using `template` as the structure
      - Apply `context` and `rules` as constraints - but do NOT copy them into the file
      - Show brief progress: "Created <artifact-id>"

   b. **Continue until all `applyRequires` artifacts are complete**
      - After creating each artifact, re-run `npx -y @fission-ai/openspec@latest status --change "<name>" --json`
      - Check if every artifact ID in `applyRequires` has `status: "done"` in the artifacts array
      - Stop when all `applyRequires` artifacts are done

   c. **If an artifact requires user input** (unclear context):
      - Use **AskUserQuestion tool** to clarify
      - Then continue with creation

5. **Show final status**
   ```bash
   npx -y @fission-ai/openspec@latest status --change "<name>"
   ```

6. **Generate the developer review checklist (human gate).**

   Run the bundled helper to create `review-checklist.md` for this change:
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/generate-checklist.sh" "openspec/changes/<name>"
   ```

   The script auto-detects the variant (BE/FE × Feature/BugFix/Refactor) from `proposal.md` + `tasks.md`, fetches the Mor Developer Review Checklist from the canonical Google Doc (with 24h cache fallback), and writes a populated checklist with `Overall Decision: PENDING`.

   This step is REQUIRED. Until the human flips the decision to `OK`, the plugin's PreToolUse hook will refuse `/spec:apply`, `/superpowers:executing-plans`, and `/superpowers:subagent-driven-development` for this change.

   If the script fails (network down, variant detection ambiguous), report the error and tell the user to run `/spec:review` manually with `--variant` override.

**Output**

After completing all artifacts AND the review checklist, summarize:
- Change name and location
- List of artifacts created with brief descriptions
- The path of the generated `review-checklist.md` and detected variant
- Clear next-step instruction:
  > "Open `<path>/review-checklist.md`, tick the items honestly, fill the Review Summary, then change `Overall Decision: PENDING` → `Overall Decision: OK`. The plugin's hook blocks all implementation skills for this change until you do."
- Use the **AskUserQuestion tool** to let the user pick an implementation path FOR LATER (after they approve the checklist):
  - **`/spec:apply`** — native OpenSpec runner, tuần tự task theo thứ tự
  - **`/superpowers:executing-plans`** — TDD discipline với 1 agent (recommended cho plan ngắn)
  - **`/superpowers:subagent-driven-development`** — parallel subagents (recommended khi plan có ≥3 task groups độc lập về Files block)

  Nếu user chưa biết chọn gì, default đề xuất `/superpowers:subagent-driven-development` cho plan có nhiều task groups và `/superpowers:executing-plans` cho plan đơn giản. Remind that NONE of these will run until the checklist's `Overall Decision: OK`.

**Artifact Creation Guidelines**

- Follow the `instruction` field from `openspec instructions` for each artifact type
- The schema defines what each artifact should contain - follow it
- Read dependency artifacts for context before creating new ones
- Use `template` as the structure for your output file - fill in its sections
- **IMPORTANT**: `context` and `rules` are constraints for YOU, not content for the file
  - Do NOT copy `<context>`, `<rules>`, `<project_context>` blocks into the artifact
  - These guide what you write, but should never appear in the output

**Library research with Context7 (when filling Tech Stack)**

The `superpowers-driven` schema requires `design.md` to declare an explicit `## Tech Stack` section. Before listing a library/framework with version, verify it via Context7 — this prevents hallucinated APIs and stale version numbers:
- **MCP path (preferred when Context7 MCP installed):** call `mcp__context7__resolve-library-id` (`libraryName` + `query`) → take the best Context7 ID like `/reactjs/react.dev` → call `mcp__context7__query-docs` (`libraryId` + `query`) for the actual docs. Retry once with `researchMode: true` if shallow. Skip step 1 if user gave you `/org/project`.
- **CLI fallback (lazy via npx):**
  ```bash
  npx -y ctx7 library "<library-name>" "<topic>"   # Step 1: resolve to Context7 ID
  npx -y ctx7 docs "<library-id>" "<topic>"         # Step 2: query docs for that ID
  ```

Apply the same check inside `tasks.md`: when a TDD step calls a library API (e.g., "Implement using `@aws-sdk/client-s3` v3 PutObjectCommand"), confirm the API shape via Context7 first. Cheaper than rewriting tasks later.

**Guardrails**
- Create ALL artifacts needed for implementation (as defined by schema's `apply.requires`)
- Always read dependency artifacts before creating a new one
- If context is critically unclear, ask the user - but prefer making reasonable decisions to keep momentum
- If a change with that name already exists, ask if user wants to continue it or create a new one
- Verify each artifact file exists after writing before proceeding to next
