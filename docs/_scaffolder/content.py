"""Curated content for morkit docs site.

This file is hand-edited. Content here drives the "Khi nào dùng", "Ví dụ",
and "Liên quan" sections of each command/skill detail page. The "Để làm gì"
section is rendered from `description` in SKILL.md/command.md frontmatter,
unless an override is supplied here.
"""

# ----------------------------------------------------------------------
# Group taxonomy + display labels
# ----------------------------------------------------------------------
GROUPS = {
    "spec": {
        "commands": ["propose", "review", "archive"],
        "skills":   ["propose", "review", "archive"],
    },
    "plan-build": {
        "commands": ["brainstorm", "write-plan", "execute-plan"],
        "skills": [
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
        "skills": [
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

GROUP_LABELS = {
    "spec":        "Spec workflow",
    "plan-build":  "Plan & build",
    "code-review": "Code review",
    "doc-gen":     "Doc generation",
    "misc":        "Khác",
}

# Reverse lookup helper
def group_of(kind, slug):
    """kind: 'skills' | 'commands' ; slug: file basename"""
    for g, items in GROUPS.items():
        if slug in items.get(kind, []):
            return g
    return "misc"


# ----------------------------------------------------------------------
# Per-item curated content
#   Keys are "<kind>.<slug>" — "skills.brainstorming", "commands.propose".
#   Any missing field falls back to a heuristic in build.py.
# ----------------------------------------------------------------------
CURATED = {
    # -------- SPEC WORKFLOW (skills) --------
    "skills.propose": {
        "when_to_use": [
            "Khi bạn muốn mô tả 1 thay đổi mới và cần đầy đủ proposal + design + tasks + review-checklist",
            "Trước khi bắt tay implement bất kỳ feature nào",
        ],
        "example_args": "Thêm tính năng export PDF cho dashboard",
        "example_note": "Sinh 1 change folder `morkit/output/spec/<tên>/` với 4 file artifacts, sẵn sàng cho bước review-checklist.",
    },
    "skills.review": {
        "when_to_use": [
            "Sau khi `propose` hoàn tất — cần kích hoạt human gate trước khi code",
            "Khi muốn refresh checklist từ Google Doc canonical của Mor",
        ],
        "example_args": "--variant FE-BugFix",
        "example_note": "Tạo `review-checklist.md`. Bạn mở file, tick, đổi `Overall Decision: PENDING → OK` để mở khoá `executing-plans`.",
    },
    "skills.archive": {
        "when_to_use": [
            "Sau khi implementation đã merge và verified production",
            "Khi muốn dọn dẹp `morkit/output/spec/` để giữ active changes gọn",
        ],
        "example_args": "feat-pdf-export",
        "example_note": "Move folder change từ active sang `archive/YYYY-MM/` + update `.meta.json`.",
    },

    # -------- SPEC WORKFLOW (commands, slash-command thin wrappers) --------
    "commands.propose": {
        "when_to_use": [
            "Khi nhanh muốn scaffold đầy đủ artifacts cho 1 change mới",
            "Equivalent với skill `propose` nhưng gọi qua slash command",
        ],
        "example_args": "Thêm dark mode toggle",
        "example_note": "Sinh `morkit/output/spec/<auto-named>/` với proposal/design/tasks/review-checklist.",
    },
    "commands.review": {
        "when_to_use": [
            "Sau khi `/morkit:propose` chạy xong",
            "Khi muốn override variant (BE/FE × Feature/BugFix/Refactor) hoặc refresh từ Google Doc",
        ],
        "example_args": "--variant BE-Feature",
        "example_note": "Tạo `review-checklist.md` theo variant chỉ định. `--refresh` để re-fetch Google Doc canonical.",
    },
    "commands.archive": {
        "when_to_use": [
            "Sau khi PR đã merge và feature đã verified ở production",
        ],
        "example_args": "feat-dark-mode",
        "example_note": "Đóng change folder. Không xoá — chỉ move sang archive subfolder.",
    },

    # -------- PLAN & BUILD (skills) --------
    "skills.brainstorming": {
        "when_to_use": [
            "Khi nhận task chưa rõ scope hoặc requirements",
            "Trước khi viết plan implementation",
            "Khi cần map codebase trước khi đụng code",
        ],
        "example_args": "Thêm real-time collab vào editor",
        "example_note": "Skill hỏi 1 câu/lần để clarify, rồi đề xuất 2-3 approaches kèm trade-offs. KHÔNG code.",
    },
    "skills.writing-plans": {
        "when_to_use": [
            "Sau khi `brainstorming` đã chốt design",
            "Khi có spec/requirements rõ ràng và cần break xuống steps",
        ],
        "example_args": "(tự lấy context từ brainstorming session)",
        "example_note": "Output là plan file với numbered steps, mỗi step có verification criteria.",
    },
    "skills.executing-plans": {
        "when_to_use": [
            "Sau khi plan đã viết và review-checklist đã `Overall Decision: OK`",
            "Khi muốn chạy plan trong session riêng với review checkpoints",
        ],
        "example_args": "(tự load plan đã viết)",
        "example_note": "Bị block bởi review-gate cho tới khi human approve checklist. Chạy step-by-step, dừng để confirm ở các checkpoint.",
    },
    "skills.subagent-driven-development": {
        "when_to_use": [
            "Khi plan có nhiều task độc lập có thể parallel",
            "Khi muốn iterate nhanh hơn so với sequential execution",
        ],
        "example_args": "(tự load plan)",
        "example_note": "Spawn subagents song song, mỗi agent chạy 1 task. Bị block bởi review-gate giống executing-plans.",
    },
    "skills.test-driven-development": {
        "when_to_use": [
            "Khi implement bất kỳ feature hoặc bugfix nào",
            "Trước khi viết code production",
        ],
        "example_args": "(invoke trước khi code)",
        "example_note": "Red → Green → Refactor. Viết test fail trước, code tối thiểu để pass, refactor.",
    },
    "skills.systematic-debugging": {
        "when_to_use": [
            "Khi gặp bug, test failure, hoặc behavior bất thường",
            "Trước khi đề xuất fix",
        ],
        "example_args": "(invoke khi gặp lỗi)",
        "example_note": "Reproduce → narrow scope → form hypothesis → verify → fix. Không guess.",
    },
    "skills.dispatching-parallel-agents": {
        "when_to_use": [
            "Khi đối mặt 2+ task độc lập không chia sẻ state",
            "Khi cần research/investigation song song trên nhiều khía cạnh",
        ],
        "example_args": "(invoke khi có ≥2 task độc lập)",
        "example_note": "Spawn nhiều Agent tool calls trong 1 message với `run_in_background: true`.",
    },
    "skills.using-git-worktrees": {
        "when_to_use": [
            "Khi bắt đầu feature cần isolation khỏi workspace hiện tại",
            "Trước khi execute implementation plan có thể đụng nhiều file",
        ],
        "example_args": "(invoke trước khi cut branch)",
        "example_note": "Tạo worktree ở thư mục riêng, không ảnh hưởng working tree chính. Safety checks built-in.",
    },
    "skills.finishing-a-development-branch": {
        "when_to_use": [
            "Khi implementation đã xong, tests pass",
            "Khi cần quyết định merge / open PR / cleanup",
        ],
        "example_args": "(invoke khi xong feature)",
        "example_note": "Đưa structured options: squash merge, regular PR, hoặc abandon. Không tự action — đề xuất rồi user chọn.",
    },
    "skills.verification-before-completion": {
        "when_to_use": [
            "Khi sắp claim 'xong' / 'fixed' / 'passing'",
            "Trước khi commit hoặc mở PR",
        ],
        "example_args": "(invoke trước khi commit)",
        "example_note": "Bắt buộc chạy verification command thật, xem output thật, mới được claim success. Evidence before assertions.",
    },
    "skills.requesting-code-review": {
        "when_to_use": [
            "Sau khi complete task, implement major feature, hoặc trước khi merge",
        ],
        "example_args": "(invoke khi feature đã xong)",
        "example_note": "Verify work đáp ứng requirements trước khi xin review. Có thể gọi `/morkit:deep-review` nội bộ.",
    },
    "skills.receiving-code-review": {
        "when_to_use": [
            "Khi nhận code review feedback",
            "Đặc biệt khi feedback unclear hoặc technically questionable",
        ],
        "example_args": "(invoke khi đọc PR comments)",
        "example_note": "Technical rigor + verification, không 'agree' theo phản xạ. Mỗi suggestion phải hiểu rõ trước khi implement.",
    },
    "skills.writing-skills": {
        "when_to_use": [
            "Khi tạo skill mới, edit skill có sẵn",
            "Khi verify 1 skill hoạt động trước deploy",
        ],
        "example_args": "(invoke khi viết SKILL.md)",
        "example_note": "Đảm bảo frontmatter đúng format, content rõ ràng, examples đầy đủ, đã test trong session thật.",
    },

    # -------- PLAN & BUILD (commands — deprecated wrappers) --------
    "commands.brainstorm": {
        "deprecated": True,
        "when_to_use": [
            "Command này deprecated — dùng skill `morkit:brainstorming` thay thế",
        ],
        "example_args": "",
        "example_note": "Sẽ bị remove ở major release tiếp theo.",
    },
    "commands.write-plan": {
        "deprecated": True,
        "when_to_use": [
            "Command này deprecated — dùng skill `morkit:writing-plans` thay thế",
        ],
        "example_args": "",
        "example_note": "Sẽ bị remove ở major release tiếp theo.",
    },
    "commands.execute-plan": {
        "deprecated": True,
        "when_to_use": [
            "Command này deprecated — dùng skill `morkit:executing-plans` thay thế",
        ],
        "example_args": "",
        "example_note": "Sẽ bị remove ở major release tiếp theo.",
    },

    # -------- CODE REVIEW --------
    "skills.deep-review": {
        "when_to_use": [
            "Khi cần review code chất lượng cao trên git diff hoặc PR",
            "Trước khi merge feature lớn",
        ],
        "example_args": "PR#123",
        "example_note": "Dispatch 5 chuyên gia (risk, security, pattern, tests, convention) song song. Output là Markdown matrix report.",
    },
    "commands.deep-review": {
        "when_to_use": [
            "Sau khi push branch và muốn review trước khi xin team review",
            "Khi cần verify rủi ro / security / test coverage trên 1 PR cụ thể",
        ],
        "example_args": "123  # hoặc HEAD~3..HEAD",
        "example_note": "Output Markdown matrix với risk/security/pattern/tests/convention findings.",
    },
    "commands.deep-review-doctor": {
        "when_to_use": [
            "Khi `/morkit:deep-review` báo lỗi setup",
            "Sau khi cài lần đầu để verify env sẵn sàng",
        ],
        "example_args": "",
        "example_note": "Check uvx, code-review-graph, gh, git, graph build, CLAUDE.md presence. Read-only.",
    },
    "commands.deep-review-post": {
        "when_to_use": [
            "Sau khi `/morkit:deep-review` xong và muốn post report làm PR comment",
        ],
        "example_args": "",
        "example_note": "Dùng `gh pr comment` để post report. Không request changes — user vẫn giữ quyền quyết định.",
    },

    # -------- DOC GENERATION (skills) --------
    "skills.docs-hero-orchestrator": {
        "when_to_use": [
            "Khi muốn sinh hoặc update bộ docs đầy đủ cho 1 project",
            "Khi cần coordinate nhiều sub-skill (SRS/API/DB/arch...) một lúc",
        ],
        "example_args": "(invoke qua /morkit:init hoặc /morkit:update)",
        "example_note": "Orchestrate 7 sub-skill, conflict-minimal updates. Standards: BrSE ITO Japan, arc42-lite, MADR.",
    },
    "skills.generate-srs": {
        "when_to_use": [
            "Khi project cần SRS theo chuẩn BrSE ITO Japan",
            "Khi muốn refresh SRS sau khi requirements thay đổi",
        ],
        "example_args": "(invoke qua /morkit:init hoặc /morkit:update)",
        "example_note": "13 sections + 2 appendices: Doc Control, Overview, Business Flow, FR/NFR, Roles, Data Items, Acceptance/UAT, Traceability...",
    },
    "skills.generate-api-docs": {
        "when_to_use": [
            "Khi cần REST API documentation",
            "Khi muốn sync docs theo route changes trong codebase",
        ],
        "example_args": "(invoke qua /morkit:init / update / sync)",
        "example_note": "Init render từ ProjectModel; update apply Delta; sync scan codebase và đề xuất changes.",
    },
    "skills.generate-db-design": {
        "when_to_use": [
            "Khi cần DB design document với Mermaid ERD",
            "Khi muốn sync schema từ ORM models",
        ],
        "example_args": "(invoke qua /morkit:init / update / sync)",
        "example_note": "Render `database-design.md` với Mermaid ERD. Sync scan ORM models và propose Add/Update/Deprecate.",
    },
    "skills.generate-system-architecture": {
        "when_to_use": [
            "Khi cần arc42-lite architecture document",
            "Khi muốn embed Mermaid component diagram",
        ],
        "example_args": "(invoke qua /morkit:init / update / sync)",
        "example_note": "8 sections arc42-lite, embed Mermaid. Sync scan services/packages/Docker/k8s/import graph.",
    },
    "skills.generate-code-standards": {
        "when_to_use": [
            "Khi cần code standards doc",
            "Khi muốn extract rules từ lint/format/commit configs hiện có",
        ],
        "example_args": "(invoke qua /morkit:init / update / sync)",
        "example_note": "Conventional Commits + auto-extracted lint/format rules. Link CONTRIBUTING.md thay vì duplicate.",
    },
    "skills.generate-codebase-summary": {
        "when_to_use": [
            "Khi cần README-style overview cho codebase",
            "Khi onboard team member mới cần hiểu tech stack + layout",
        ],
        "example_args": "(invoke qua /morkit:init / update / sync)",
        "example_note": "Tech stack, repo layout, packages, entry points, LOC by language.",
    },
    "skills.generate-design-guidelines": {
        "when_to_use": [
            "Khi cần Design Principles + Patterns + ADRs",
            "Khi muốn record kiến trúc quyết định theo MADR format",
        ],
        "example_args": "(invoke qua /morkit:init / update)",
        "example_note": "MADR format. Init emit per-ADR stubs ở `docs/adr/NNN-slug.md`. Sync intentionally not supported — guidelines là manual.",
    },

    # -------- DOC GENERATION (commands) --------
    "commands.setup": {
        "when_to_use": [
            "Lần đầu sau khi `/plugin install morkit`",
            "Sau khi đổi Python version hoặc rebuild venv",
        ],
        "example_args": "",
        "example_note": "Bootstrap Python venv tại `~/.claude/plugins/data/docs-hero/.venv` + install pinned deps. Idempotent, ~30-60s.",
    },
    "commands.init": {
        "when_to_use": [
            "Khi project chưa có doc nào, muốn sinh fresh từ ProjectModel JSON",
        ],
        "example_args": "--lang VN",
        "example_note": "Multi-select gate hỏi pick doc nào (SRS/API/DB/...). Output ra `./docs/`. Single-language (JP|EN|VN).",
    },
    "commands.update": {
        "when_to_use": [
            "Khi OpenSpec change đã merge và cần apply vào doc tương ứng",
            "Khi brainstorm plan đã chốt và muốn update doc",
        ],
        "example_args": "<change-name>",
        "example_note": "Apply OpenSpec change/plan vào doc hiện có. Preserve manual edits qua diff engine.",
    },
    "commands.sync": {
        "when_to_use": [
            "Khi schema/route trong code đã đổi nhưng doc chưa update",
            "Khi muốn propose changes mà chưa apply ngay",
        ],
        "example_args": "",
        "example_note": "Read-only scan ORM + REST routes. Output `sync-proposal.md` với checkboxes ADD/UPDATE/DEPRECATE.",
    },
    "commands.apply-sync": {
        "when_to_use": [
            "Sau khi `/morkit:sync` đã sinh proposal và user đã tick checkboxes",
        ],
        "example_args": "",
        "example_note": "Convert ticked items thành Delta, chạy standard update flow.",
    },
    "commands.doctor": {
        "when_to_use": [
            "Khi `/morkit:init` hoặc `/morkit:update` báo lỗi setup",
            "Sau khi cài lần đầu để verify env sẵn sàng",
        ],
        "example_args": "",
        "example_note": "Check Python version, venv, deps, schema importable, mmdc availability. Read-only.",
    },

    # -------- MISC --------
    "skills.using-morkit": {
        "when_to_use": [
            "Tự động invoke khi bắt đầu mỗi conversation",
            "Khi cần hiểu cách find và dùng các skill khác",
        ],
        "example_args": "(auto-invoke)",
        "example_note": "Establish how to find and use skills. Required ở đầu mọi conversation.",
    },
}
