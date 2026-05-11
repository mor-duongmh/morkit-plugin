# Design — morkit-docs-site

## Decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | No JS runtime deps; inline JS chỉ cho theme toggle (~10 LOC) | Giữ tinh thần PR #21 — user mở HTML là chạy, không cần npm/node |
| D2 | 42 trang HTML thuần file-based routing (`<a href>` tĩnh) | Đơn giản nhất, không router, GitHub Pages serve thẳng |
| D3 | CSS inline trong mỗi file (duplication có chủ đích) | User chọn rõ. Trade-off: file to hơn nhưng zero coupling, mỗi page tự đứng được |
| D4 | Scaffolder Python (one-shot, không phải runtime dep) | 42 file × cùng cấu trúc → drift risk cao nếu viết tay. Script chạy bằng tay khi đổi nội dung; output HTML thuần check vào git |
| D5 | Template "claudekit-slim" 4 mục cho skill, 5 mục cho command | Cắt khỏi format claudekit gốc: bỏ "Configuration", "Tool access", "Frontmatter", "Hooks" — người mới không cần |
| D6 | Overview = README trừ "Workflow điển hình" và "License" | User chốt rõ |
| D7 | Branch base off `docs/morkit-landing-html` (PR #21) | User chốt rõ; PR mới cạnh PR #21 |
| D8 | Nội dung skill/command page = description trong frontmatter + heuristic extract + hand-curated "Liên quan" group map | Cân bằng giữa tốc độ (v1 review nhanh) và độ chính xác. User sẽ tinh chỉnh nội dung sau ở vòng review |

## File layout

```
docs/
├── index.html                       ← overview (handwritten)
├── docs.html                        ← PR #21 (unchanged)
├── commands/
│   ├── apply-sync.html              ┐
│   ├── archive.html                 │
│   ├── brainstorm.html              │
│   ├── deep-review-doctor.html      │
│   ├── deep-review-post.html        │
│   ├── deep-review.html             │ 15 file, scaffolder sinh
│   ├── doctor.html                  │
│   ├── execute-plan.html            │
│   ├── init.html                    │
│   ├── propose.html                 │
│   ├── review.html                  │
│   ├── setup.html                   │
│   ├── sync.html                    │
│   ├── update.html                  │
│   └── write-plan.html              ┘
├── skills/
│   ├── archive.html                 ┐
│   ├── brainstorming.html           │
│   ├── deep-review.html             │
│   ├── dispatching-parallel-agents.html
│   ├── docs-hero-orchestrator.html  │
│   ├── executing-plans.html         │
│   ├── finishing-a-development-branch.html
│   ├── generate-api-docs.html       │
│   ├── generate-code-standards.html │
│   ├── generate-codebase-summary.html
│   ├── generate-db-design.html      │ 26 file, scaffolder sinh
│   ├── generate-design-guidelines.html
│   ├── generate-srs.html            │
│   ├── generate-system-architecture.html
│   ├── propose.html                 │
│   ├── receiving-code-review.html   │
│   ├── requesting-code-review.html  │
│   ├── review.html                  │
│   ├── subagent-driven-development.html
│   ├── systematic-debugging.html    │
│   ├── test-driven-development.html │
│   ├── using-git-worktrees.html     │
│   ├── using-morkit.html            │
│   ├── verification-before-completion.html
│   ├── writing-plans.html           │
│   └── writing-skills.html          ┘
└── _scaffolder/
    ├── build.py                     ← entry point, render 41 file
    ├── templates.py                 ← string templates (overview/command/skill)
    └── content.py                   ← group map + per-item curated bullets
```

## Scaffolder I/O contract

**Input:**
- `plugins/morkit/skills/<name>/SKILL.md` — YAML frontmatter `{name, description}` + body
- `plugins/morkit/commands/<name>.md` — YAML frontmatter `{description}` + body

**Per-item processing:**
1. Parse frontmatter (PyYAML hoặc regex thuần để khỏi cần dep).
2. Fields cho template:
   - `name` — tên skill/command
   - `slug` — file basename
   - `description` — từ frontmatter (cleaned)
   - `kind` — `skill` | `command`
   - `group` — `spec` | `plan-build` | `code-review` | `doc-gen` | `misc`
   - `when_to_use` — bullets (hand-curated trong `content.py`, fallback từ description)
   - `example` — slash invocation + commentary (hand-curated, fallback generic)
   - `related` — list 3 anh em cùng group
3. Render template → ghi `docs/<kind>s/<slug>.html` (lưu ý: command kind → folder `commands`)

**Output:** HTML thuần, inline CSS, ~6-12KB/file.

## Template "claudekit-slim"

### Skill page (4 mục)

```
[ ← Quay lại tổng quan  |  morkit › skills › <slug> ]   [☾ theme]

<h1>{name}</h1>
<p class="lede">{description}</p>

<section> 1. Để làm gì
   {description đã expand thành 1-2 đoạn}
</section>

<section> 2. Khi nào dùng
   <ul>{bullets}</ul>
</section>

<section> 3. Ví dụ
   <pre>$ /morkit:{slug} {example_args}</pre>
   {commentary}
</section>

<section> 4. Liên quan
   <ul>{related links}</ul>
</section>

[footer: link sang index.html + docs.html]
```

### Command page = skill template + mục "Cách gọi"

```
<section> 1. Để làm gì ...
<section> 2. Cách gọi
   <pre>/morkit:{slug} [args]</pre>
   {args description}
<section> 3. Khi nào dùng ...
<section> 4. Ví dụ ...
<section> 5. Liên quan ...
```

## Group map (`content.py`)

```python
GROUPS = {
    "spec": {
        "commands": ["propose", "review", "archive"],
        "skills":   ["propose", "review", "archive"],
    },
    "plan-build": {
        "commands": ["brainstorm", "write-plan", "execute-plan"],
        "skills":   [
            "brainstorming", "writing-plans", "executing-plans",
            "subagent-driven-development", "test-driven-development",
            "systematic-debugging", "dispatching-parallel-agents",
            "using-git-worktrees", "finishing-a-development-branch",
            "verification-before-completion",
            "requesting-code-review", "receiving-code-review",
            "writing-skills",
        ],
    },
    "code-review": {
        "commands": ["deep-review", "deep-review-doctor", "deep-review-post"],
        "skills":   ["deep-review"],
    },
    "doc-gen": {
        "commands": ["setup", "init", "update", "sync", "apply-sync", "doctor"],
        "skills":   [
            "generate-srs", "generate-api-docs", "generate-db-design",
            "generate-system-architecture", "generate-code-standards",
            "generate-codebase-summary", "generate-design-guidelines",
            "docs-hero-orchestrator",
        ],
    },
    "misc": {
        "commands": [],
        "skills":   ["using-morkit"],
    },
}
```

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Nội dung sinh ra v1 còn cứng/generic | User review xong, tinh chỉnh hand-curated content trong `content.py`, regen |
| Drift HTML vs SKILL.md sau này | Scaffolder regenerate từ SKILL.md là source-of-truth |
| 42 file CSS inline = ~1MB total | Có chủ đích; chỉ làm to PR diff khi đổi token. Acceptable cho docs |
| User edit HTML trực tiếp → bị scaffolder ghi đè | Comment đầu file `<!-- AUTOGENERATED by docs/_scaffolder/build.py. Edit content.py + templates.py, not this file. -->` |
