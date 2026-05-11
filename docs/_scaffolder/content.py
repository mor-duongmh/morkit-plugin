"""Curated content for morkit docs site (Vietnamese).

Mỗi entry trong CURATED có 4 field:
  - lede        : 1 câu ngắn mô tả mục đích (hiện ở đầu trang)
  - when_to_use : 2-3 bullet "Khi nào dùng" (tiếng Việt)
  - example_args: tham số gõ kèm slash command
  - example_note: 1 câu giải thích kết quả

Mọi chỉnh sửa nội dung làm tại đây, sau đó chạy
    python3 docs/_scaffolder/build.py
để regenerate 42 trang HTML.
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
# Per-item content (slug → dict).
#   Key format: "<kind>.<slug>" — vd "skills.brainstorming"
# ----------------------------------------------------------------------
CURATED = {
    # ====================================================================
    # NHÓM 1 — VIẾT SPEC
    # ====================================================================
    "skills.propose": {
        "lede": "Mô tả ý tưởng bằng 1-2 câu → tự sinh đầy đủ 4 file: proposal, design, tasks và checklist review.",
        "when_to_use": [
            "Khi muốn bắt đầu một thay đổi mới trong dự án",
            "Trước khi viết bất kỳ dòng code nào, để có spec rõ ràng",
        ],
        "example_args": "Thêm tính năng export PDF cho dashboard",
        "example_note": "Sau khi chạy, một thư mục mới sẽ được tạo trong morkit/output/spec/<tên-change>/ chứa 4 file sẵn sàng để bạn duyệt.",
    },
    "skills.review": {
        "lede": "Sinh checklist để bạn duyệt thiết kế. Khi nào bạn ghi 'Overall Decision: OK', bước thực thi mới được mở khoá.",
        "when_to_use": [
            "Sau khi vừa chạy propose xong",
            "Khi muốn làm mới checklist với một biến thể khác (BE/FE × Feature/BugFix/Refactor)",
        ],
        "example_args": "--variant FE-BugFix",
        "example_note": "Bạn mở file review-checklist.md, tick các mục, đổi dòng cuối từ PENDING sang OK. Sau đó skill executing-plans mới chịu chạy.",
    },
    "skills.archive": {
        "lede": "Đóng một change folder sau khi PR đã merge và đã deploy ổn.",
        "when_to_use": [
            "Sau khi đã merge và verify ở môi trường thật",
            "Khi muốn giữ thư mục morkit/output/spec/ gọn gàng",
        ],
        "example_args": "feat-pdf-export",
        "example_note": "Folder sẽ được di chuyển sang archive/YYYY-MM/, không bị xoá. Có thể tra lại sau này.",
    },

    "commands.propose": {
        "lede": "Slash command tương đương skill propose — gõ nhanh để tạo đầy đủ 4 file artifact.",
        "when_to_use": [
            "Khi muốn tạo nhanh một change mới mà không cần invoke skill thủ công",
        ],
        "example_args": "Thêm dark mode toggle",
        "example_note": "Một thư mục mới sẽ xuất hiện trong morkit/output/spec/ với tên tự đặt từ mô tả.",
    },
    "commands.review": {
        "lede": "Slash command sinh hoặc làm mới checklist duyệt thiết kế cho một change đang có.",
        "when_to_use": [
            "Ngay sau khi gõ /morkit:propose xong",
            "Khi muốn ép một biến thể khác hoặc đồng bộ lại checklist mới nhất từ Google Doc",
        ],
        "example_args": "--variant BE-Feature",
        "example_note": "Có thể thêm --refresh để tải lại nội dung mới nhất từ Google Doc canonical của Mor.",
    },
    "commands.archive": {
        "lede": "Slash command đóng change folder sau khi đã merge.",
        "when_to_use": [
            "Sau khi PR đã merge và feature đã chạy ổn trên môi trường thật",
        ],
        "example_args": "feat-dark-mode",
        "example_note": "Không xoá file — chỉ chuyển sang thư mục archive/ để giữ phần active luôn sạch.",
    },

    # ====================================================================
    # NHÓM 2 — LÊN KẾ HOẠCH VÀ LÀM
    # ====================================================================
    "skills.brainstorming": {
        "lede": "Cùng bạn suy nghĩ ý tưởng và khảo sát mã nguồn trước khi viết code. Chỉ tư duy — không tạo file, không sửa code.",
        "when_to_use": [
            "Khi nhận một yêu cầu chưa rõ phạm vi",
            "Trước khi viết kế hoạch chi tiết",
            "Khi cần đọc và hiểu mã nguồn hiện tại trước khi đụng vào",
        ],
        "example_args": "Thêm tính năng cộng tác thời gian thực vào editor",
        "example_note": "Skill sẽ hỏi từng câu một để làm rõ, rồi đề xuất 2-3 cách làm kèm ưu nhược điểm. Bạn chốt rồi mới qua bước viết plan.",
    },
    "skills.writing-plans": {
        "lede": "Khi đã có yêu cầu rõ ràng, dùng skill này để viết kế hoạch nhiều bước trước khi đụng code.",
        "when_to_use": [
            "Sau khi brainstorming đã chốt phương án",
            "Khi đã có yêu cầu cụ thể và cần chia nhỏ thành các bước",
        ],
        "example_args": "(tự lấy ngữ cảnh từ phiên brainstorming trước đó)",
        "example_note": "Kết quả là một file plan có các bước đánh số, mỗi bước kèm tiêu chí xác minh đã làm xong.",
    },
    "skills.executing-plans": {
        "lede": "Chạy plan từng bước trong một phiên làm việc riêng, có điểm dừng để bạn xem lại giữa chừng.",
        "when_to_use": [
            "Khi plan đã viết xong và checklist review đã được duyệt OK",
            "Khi muốn chạy có kiểm soát, dừng để confirm ở mỗi mốc quan trọng",
        ],
        "example_args": "(tự nạp plan đã viết)",
        "example_note": "Bị chặn cho đến khi human duyệt checklist. Khi chạy, dừng ở các checkpoint để bạn xác nhận trước khi đi tiếp.",
    },
    "skills.subagent-driven-development": {
        "lede": "Khi plan có nhiều việc độc lập, spawn nhiều subagent chạy song song thay vì làm tuần tự.",
        "when_to_use": [
            "Khi plan chứa các bước không phụ thuộc lẫn nhau",
            "Khi muốn đi nhanh hơn so với chạy tuần tự",
        ],
        "example_args": "(tự nạp plan)",
        "example_note": "Mỗi subagent đảm nhận một task. Vẫn bị chặn bởi gate review giống executing-plans.",
    },
    "skills.test-driven-development": {
        "lede": "Bắt buộc viết test trước, code sau. Quy trình Red → Green → Refactor.",
        "when_to_use": [
            "Khi triển khai bất kỳ tính năng hoặc bản sửa lỗi nào",
            "Trước khi viết code production",
        ],
        "example_args": "(gọi trước khi bắt tay code)",
        "example_note": "Viết test fail trước, rồi viết code tối thiểu để test pass, cuối cùng refactor cho gọn.",
    },
    "skills.systematic-debugging": {
        "lede": "Khi gặp lỗi, debug có hệ thống thay vì đoán mò. Tái hiện lỗi trước, sửa sau.",
        "when_to_use": [
            "Khi gặp bug, test thất bại hoặc hành vi bất thường",
            "Trước khi đề xuất bất kỳ bản sửa nào",
        ],
        "example_args": "(gọi khi gặp lỗi)",
        "example_note": "Tái hiện lỗi → thu hẹp phạm vi → đặt giả thuyết → xác minh → sửa. Không đoán mò.",
    },
    "skills.dispatching-parallel-agents": {
        "lede": "Khi có từ 2 việc độc lập trở lên, spawn nhiều agent chạy song song để tiết kiệm thời gian.",
        "when_to_use": [
            "Khi có 2 hoặc nhiều việc không phụ thuộc lẫn nhau",
            "Khi cần khảo sát nhiều khía cạnh cùng lúc",
        ],
        "example_args": "(gọi khi có nhiều việc song song)",
        "example_note": "Các agent chạy đồng thời, sau đó tổng hợp kết quả. Phù hợp với nghiên cứu nhiều hướng cùng lúc.",
    },
    "skills.using-git-worktrees": {
        "lede": "Tạo worktree riêng cho feature mới, không ảnh hưởng đến workspace hiện tại.",
        "when_to_use": [
            "Khi bắt đầu một feature cần làm cách ly khỏi workspace hiện tại",
            "Trước khi chạy plan thực thi có thể đụng nhiều file",
        ],
        "example_args": "(gọi trước khi cut branch)",
        "example_note": "Tạo worktree ở thư mục riêng, có kiểm tra an toàn sẵn để không xung đột với branch hiện tại.",
    },
    "skills.finishing-a-development-branch": {
        "lede": "Khi feature đã xong và test pass, skill gợi ý các lựa chọn đóng branch (merge, mở PR, hoặc bỏ).",
        "when_to_use": [
            "Khi đã code xong, test pass hết",
            "Khi cần quyết định bước đóng nhánh",
        ],
        "example_args": "(gọi khi đã làm xong feature)",
        "example_note": "Đưa ra các lựa chọn: squash merge, mở PR thường, hoặc bỏ branch. Skill không tự action — chỉ đề xuất.",
    },
    "skills.verification-before-completion": {
        "lede": "Trước khi nói \"xong rồi\" hoặc commit, bắt buộc chạy lệnh kiểm tra thật và xem output thật.",
        "when_to_use": [
            "Trước khi báo cáo \"đã làm xong\" hay \"đã sửa rồi\"",
            "Trước khi commit hoặc mở PR",
        ],
        "example_args": "(gọi trước khi commit)",
        "example_note": "Bằng chứng có trước lời khẳng định. Phải có output thật mới được nói thành công.",
    },
    "skills.requesting-code-review": {
        "lede": "Khi feature đã xong, dùng skill này để chuẩn bị xin review một cách có hệ thống.",
        "when_to_use": [
            "Sau khi đã làm xong một task hoặc một feature lớn",
            "Trước khi merge",
        ],
        "example_args": "(gọi khi feature đã xong)",
        "example_note": "Tự kiểm tra trước xem code đã đạt yêu cầu chưa. Có thể chạy /morkit:deep-review nội bộ trước khi gửi cho người.",
    },
    "skills.receiving-code-review": {
        "lede": "Khi nhận góp ý review, skill này giúp bạn hiểu rõ trước khi sửa — không đồng ý theo phản xạ.",
        "when_to_use": [
            "Khi đọc các comment review trên PR",
            "Đặc biệt khi feedback chưa rõ hoặc nghe có vẻ chưa hợp lý",
        ],
        "example_args": "(gọi khi đọc PR comments)",
        "example_note": "Bắt buộc hiểu rõ từng góp ý trước khi thực hiện. Không đồng ý lấy lệ.",
    },
    "skills.writing-skills": {
        "lede": "Khi cần tạo skill mới hoặc sửa skill cũ, dùng skill này để đảm bảo viết đúng chuẩn.",
        "when_to_use": [
            "Khi viết file SKILL.md mới",
            "Khi sửa skill có sẵn",
            "Trước khi đưa skill vào sử dụng thực tế",
        ],
        "example_args": "(gọi khi soạn SKILL.md)",
        "example_note": "Đảm bảo frontmatter đúng định dạng, nội dung rõ ràng, có ví dụ đầy đủ và đã thử chạy thật.",
    },

    "commands.brainstorm": {
        "lede": "Slash command cũ — đã được thay bằng skill morkit:brainstorming.",
        "deprecated": True,
        "when_to_use": [
            "Đừng dùng nữa — dùng skill morkit:brainstorming thay thế",
        ],
        "example_args": "",
        "example_note": "Sẽ bị gỡ ở bản major tiếp theo.",
    },
    "commands.write-plan": {
        "lede": "Slash command cũ — đã được thay bằng skill morkit:writing-plans.",
        "deprecated": True,
        "when_to_use": [
            "Đừng dùng nữa — dùng skill morkit:writing-plans thay thế",
        ],
        "example_args": "",
        "example_note": "Sẽ bị gỡ ở bản major tiếp theo.",
    },
    "commands.execute-plan": {
        "lede": "Slash command cũ — đã được thay bằng skill morkit:executing-plans.",
        "deprecated": True,
        "when_to_use": [
            "Đừng dùng nữa — dùng skill morkit:executing-plans thay thế",
        ],
        "example_args": "",
        "example_note": "Sẽ bị gỡ ở bản major tiếp theo.",
    },

    # ====================================================================
    # NHÓM 3 — REVIEW CODE
    # ====================================================================
    "skills.deep-review": {
        "lede": "Review code chuyên sâu bằng 5 chuyên gia AI chạy song song (rủi ro, bảo mật, pattern, kiểm thử, quy ước).",
        "when_to_use": [
            "Khi cần review chất lượng cao một PR hoặc git diff",
            "Trước khi merge một feature lớn",
        ],
        "example_args": "PR#123",
        "example_note": "Kết quả là một báo cáo dạng bảng Markdown gồm các phát hiện về rủi ro, bảo mật, pattern, độ phủ test và quy ước code.",
    },
    "commands.deep-review": {
        "lede": "Slash command chạy review chuyên sâu trên PR hoặc git diff, kết quả là báo cáo Markdown dạng bảng.",
        "when_to_use": [
            "Sau khi push branch, muốn tự review trước khi mời team xem",
            "Khi cần kiểm tra rủi ro, bảo mật và độ phủ test trên một PR cụ thể",
        ],
        "example_args": "123  # hoặc HEAD~3..HEAD",
        "example_note": "Báo cáo gồm các phát hiện về rủi ro, bảo mật, pattern, kiểm thử và quy ước code.",
    },
    "commands.deep-review-doctor": {
        "lede": "Kiểm tra xem cài đặt Deep Review đã đủ điều kiện chạy chưa.",
        "when_to_use": [
            "Khi /morkit:deep-review báo lỗi không chạy được",
            "Sau khi cài plugin lần đầu, muốn xác nhận môi trường đã sẵn sàng",
        ],
        "example_args": "",
        "example_note": "Chỉ đọc và báo cáo, không sửa gì. Kiểm tra uvx, code-review-graph, gh, git, build graph và CLAUDE.md.",
    },
    "commands.deep-review-post": {
        "lede": "Sau khi đã có báo cáo review, lệnh này post lên PR làm comment qua gh CLI.",
        "when_to_use": [
            "Khi vừa chạy xong /morkit:deep-review và muốn chia sẻ kết quả lên PR",
        ],
        "example_args": "",
        "example_note": "Chỉ post báo cáo, không yêu cầu thay đổi gì — quyết định cuối vẫn là của bạn.",
    },

    # ====================================================================
    # NHÓM 4 — SINH TÀI LIỆU
    # ====================================================================
    "skills.docs-hero-orchestrator": {
        "lede": "Điều phối các sub-skill để sinh hoặc cập nhật bộ tài liệu đầy đủ cho một dự án.",
        "when_to_use": [
            "Khi cần sinh nguyên bộ tài liệu (SRS, API, DB, kiến trúc…) một lần",
            "Khi muốn các sub-skill phối hợp với nhau, ít xung đột nhất có thể",
        ],
        "example_args": "(gọi qua /morkit:init hoặc /morkit:update)",
        "example_note": "Theo các chuẩn quen thuộc: BrSE ITO Japan cho SRS, arc42-lite cho kiến trúc, MADR cho ADR.",
    },
    "skills.generate-srs": {
        "lede": "Sinh hoặc cập nhật tài liệu yêu cầu phần mềm (SRS) theo chuẩn BrSE cho ITO Japan offshore.",
        "when_to_use": [
            "Khi dự án cần SRS theo chuẩn của khách Nhật",
            "Khi yêu cầu thay đổi và cần làm mới SRS",
        ],
        "example_args": "(gọi qua /morkit:init hoặc /morkit:update)",
        "example_note": "Gồm 13 mục lớn và 2 phụ lục: Doc Control, tổng quan, luồng nghiệp vụ, FR/NFR, quyền, dữ liệu, UAT, traceability...",
    },
    "skills.generate-api-docs": {
        "lede": "Sinh hoặc cập nhật tài liệu REST API.",
        "when_to_use": [
            "Khi cần tài liệu mô tả endpoint, request, response",
            "Khi route trong mã nguồn đã đổi và muốn đồng bộ lại tài liệu",
        ],
        "example_args": "(gọi qua /morkit:init / update / sync)",
        "example_note": "Chế độ init sinh từ ProjectModel; update áp dụng thay đổi; sync quét mã và đề xuất nội dung cần cập nhật.",
    },
    "skills.generate-db-design": {
        "lede": "Sinh hoặc cập nhật tài liệu thiết kế database, có sơ đồ ERD bằng Mermaid.",
        "when_to_use": [
            "Khi cần tài liệu mô tả schema DB",
            "Khi muốn đồng bộ tài liệu với ORM model trong mã nguồn",
        ],
        "example_args": "(gọi qua /morkit:init / update / sync)",
        "example_note": "Sinh file database-design.md kèm ERD vẽ bằng Mermaid. Chế độ sync quét ORM và đề xuất Thêm/Sửa/Bỏ.",
    },
    "skills.generate-system-architecture": {
        "lede": "Sinh hoặc cập nhật tài liệu kiến trúc hệ thống theo arc42-lite, kèm sơ đồ thành phần bằng Mermaid.",
        "when_to_use": [
            "Khi cần tài liệu kiến trúc cho dự án",
            "Khi muốn nhúng sơ đồ component vẽ bằng Mermaid",
        ],
        "example_args": "(gọi qua /morkit:init / update / sync)",
        "example_note": "Gồm 8 mục theo chuẩn arc42-lite. Sync quét services, packages, Docker, k8s và đồ thị import.",
    },
    "skills.generate-code-standards": {
        "lede": "Sinh hoặc cập nhật tài liệu quy ước code (Conventional Commits + cấu hình lint/format).",
        "when_to_use": [
            "Khi dự án cần một tài liệu thống nhất về quy ước code",
            "Khi muốn rút quy ước từ các file cấu hình lint/format đang có",
        ],
        "example_args": "(gọi qua /morkit:init / update / sync)",
        "example_note": "Nếu đã có CONTRIBUTING.md, sẽ link sang chứ không nhân đôi nội dung.",
    },
    "skills.generate-codebase-summary": {
        "lede": "Sinh hoặc cập nhật tài liệu tổng quan mã nguồn dạng README: tech stack, cấu trúc, gói, entry point.",
        "when_to_use": [
            "Khi cần một bản tổng quan dự án dành cho người mới onboard",
            "Khi muốn ai đó hiểu nhanh dự án mà không cần đọc hết code",
        ],
        "example_args": "(gọi qua /morkit:init / update / sync)",
        "example_note": "Liệt kê công nghệ, bố cục thư mục, các package, entry point và số dòng code theo ngôn ngữ.",
    },
    "skills.generate-design-guidelines": {
        "lede": "Sinh hoặc cập nhật tài liệu Design Principles, Patterns và các ADR (MADR format).",
        "when_to_use": [
            "Khi cần một tài liệu thống nhất về nguyên tắc thiết kế",
            "Khi muốn ghi lại các quyết định kiến trúc theo MADR format",
        ],
        "example_args": "(gọi qua /morkit:init / update)",
        "example_note": "Khi init, mỗi ADR sẽ có một file riêng tại docs/adr/NNN-slug.md. Skill này không hỗ trợ chế độ sync — guidelines do người viết.",
    },

    "commands.setup": {
        "lede": "Chạy 1 lần sau khi cài plugin để dựng môi trường Python cho docs-hero.",
        "when_to_use": [
            "Lần đầu sau khi /plugin install morkit",
            "Sau khi đổi Python version và muốn dựng lại venv",
        ],
        "example_args": "",
        "example_note": "Mất khoảng 30-60 giây. Lệnh idempotent — chạy lại không gây hại.",
    },
    "commands.init": {
        "lede": "Sinh bộ tài liệu mới (SRS, API, DB...) từ một file ProjectModel JSON.",
        "when_to_use": [
            "Khi dự án chưa có tài liệu, muốn sinh lần đầu từ ProjectModel",
        ],
        "example_args": "--lang VN",
        "example_note": "Có menu chọn tài liệu muốn sinh (SRS / API / DB / ...). Đầu ra nằm ở thư mục docs/ của dự án. Chọn 1 ngôn ngữ: JP, EN hoặc VN.",
    },
    "commands.update": {
        "lede": "Áp dụng một change hoặc plan đã chốt vào tài liệu đang có — vẫn giữ phần bạn đã sửa tay.",
        "when_to_use": [
            "Khi một change đã merge và cần cập nhật vào tài liệu tương ứng",
            "Khi plan brainstorm đã chốt và muốn cập nhật tài liệu theo plan đó",
        ],
        "example_args": "<tên-change>",
        "example_note": "Phần bạn đã sửa tay trong tài liệu sẽ được giữ nguyên nhờ diff engine.",
    },
    "commands.sync": {
        "lede": "Đọc mã nguồn, đề xuất các nội dung nên cập nhật vào tài liệu. Chỉ đọc, không ghi.",
        "when_to_use": [
            "Khi schema hoặc route trong code đã đổi nhưng tài liệu chưa cập nhật",
            "Khi muốn xem trước các thay đổi sẽ áp dụng trước khi quyết",
        ],
        "example_args": "",
        "example_note": "Xuất file sync-proposal.md có checkbox để bạn tick các nội dung muốn áp dụng. Sau đó gõ /morkit:apply-sync.",
    },
    "commands.apply-sync": {
        "lede": "Áp dụng các nội dung bạn đã tick trong sync-proposal.md vào tài liệu.",
        "when_to_use": [
            "Ngay sau khi /morkit:sync đã sinh proposal và bạn đã tick chọn",
        ],
        "example_args": "",
        "example_note": "Chuyển các mục được tick thành thay đổi cụ thể rồi chạy update flow chuẩn.",
    },
    "commands.doctor": {
        "lede": "Kiểm tra cài đặt docs-hero xem có ổn không (Python, venv, dependencies...).",
        "when_to_use": [
            "Khi /morkit:init hoặc /morkit:update báo lỗi cài đặt",
            "Sau khi cài lần đầu, muốn xác nhận môi trường đã sẵn sàng",
        ],
        "example_args": "",
        "example_note": "Chỉ đọc và báo cáo, không sửa gì. Kiểm tra Python version, venv, dependencies, schema và mmdc.",
    },

    # ====================================================================
    # NHÓM 5 — KHÁC
    # ====================================================================
    "skills.using-morkit": {
        "lede": "Skill nền — tự chạy ở đầu mỗi cuộc hội thoại để Claude biết cách tìm và dùng các skill khác.",
        "when_to_use": [
            "Tự chạy mỗi khi bắt đầu một phiên mới — bạn không cần gọi tay",
            "Khi cần Claude hiểu cách điều phối các skill khác trong morkit",
        ],
        "example_args": "(tự gọi)",
        "example_note": "Bắt buộc chạy ở đầu mỗi phiên. Đây là điều kiện để các skill khác hoạt động đúng.",
    },
}
