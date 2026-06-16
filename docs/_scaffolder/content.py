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
        "commands": ["brainstorming", "write-plan", "execute-plan"],
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
        "commands": ["setup", "init", "update-doc", "sync", "apply-sync", "doctor"],
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
        "details": [
            "Đặt tên change tự động từ mô tả ngắn của bạn",
            "Sinh ra 4 file artifact: <strong>proposal</strong> (lý do), <strong>design</strong> (cách làm), <strong>tasks</strong> (chia bước theo TDD), <strong>review-checklist</strong> (để bạn duyệt)",
            "Tất cả nằm trong <code>morkit/output/spec/&lt;tên-change&gt;/</code>",
            "Không phụ thuộc OpenSpec hay CLI ngoài — plugin tự dựng",
        ],
        "when_to_use": [
            "Khi muốn bắt đầu một thay đổi mới trong dự án",
            "Trước khi viết bất kỳ dòng code nào, để có spec rõ ràng",
        ],
        "example_args": "Thêm tính năng export PDF cho dashboard",
        "example_note": "Sau khi chạy, một thư mục mới sẽ được tạo trong morkit/output/spec/<tên-change>/ chứa 4 file sẵn sàng để bạn duyệt.",
    },
    "skills.review": {
        "lede": "Sinh checklist để bạn duyệt thiết kế. Khi nào bạn ghi 'Overall Decision: OK', bước thực thi mới được mở khoá.",
        "details": [
            "Tải checklist canonical từ Google Doc của Mor",
            "Tự phát hiện variant: <strong>BE/FE</strong> × <strong>Feature/BugFix/Refactor</strong>",
            "Sinh file <code>review-checklist.md</code> trong change folder",
            "Là chốt chặn human-in-the-loop — 2 lớp bảo vệ song song:",
            "<ul><li>PreToolUse hook chặn ở mức harness</li><li>Mỗi skill thực thi tự kiểm tra ở Step 0</li></ul>",
        ],
        "when_to_use": [
            "Sau khi vừa chạy propose xong",
            "Khi muốn làm mới checklist với một biến thể khác (BE/FE × Feature/BugFix/Refactor)",
        ],
        "example_args": "--variant FE-BugFix",
        "example_note": "Bạn mở file review-checklist.md, tick các mục, đổi dòng cuối từ PENDING sang OK. Sau đó skill executing-plans mới chịu chạy.",
    },
    "skills.archive": {
        "lede": "Đóng một change folder sau khi PR đã merge và đã deploy ổn.",
        "details": [
            "Di chuyển thư mục change sang <code>archive/YYYY-MM/</code> theo tháng",
            "Cập nhật <code>.meta.json</code> với trạng thái <code>archived</code>",
            "Không xoá file — bạn vẫn có thể tra lại sau này",
            "Giữ thư mục <code>morkit/output/spec/</code> chỉ chứa change đang làm dở",
        ],
        "when_to_use": [
            "Sau khi đã merge và verify ở môi trường thật",
            "Khi muốn giữ thư mục morkit/output/spec/ gọn gàng",
        ],
        "example_args": "feat-pdf-export",
        "example_note": "Folder sẽ được di chuyển sang archive/YYYY-MM/, không bị xoá. Có thể tra lại sau này.",
    },

    "commands.propose": {
        "lede": "Command tương đương skill propose — gõ nhanh để tạo đầy đủ 4 file artifact.",
        "when_to_use": [
            "Khi muốn tạo nhanh một change mới mà không cần invoke skill thủ công",
        ],
        "example_args": "Thêm dark mode toggle",
        "example_note": "Một thư mục mới sẽ xuất hiện trong morkit/output/spec/ với tên tự đặt từ mô tả.",
    },
    "commands.review": {
        "lede": "Command sinh hoặc làm mới checklist duyệt thiết kế cho một change đang có.",
        "when_to_use": [
            "Ngay sau khi gõ /morkit:propose xong",
            "Khi muốn ép một biến thể khác hoặc đồng bộ lại checklist mới nhất từ Google Doc",
        ],
        "example_args": "--variant BE-Feature",
        "example_note": "Có thể thêm --refresh để tải lại nội dung mới nhất từ Google Doc canonical của Mor.",
    },
    "commands.archive": {
        "lede": "Command đóng change folder sau khi đã merge.",
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
        "lede": "Cùng bạn suy nghĩ ý tưởng và khảo sát mã nguồn ở chế độ explore — tự do mở thread, vẽ ASCII diagram, không bao giờ viết code.",
        "details": [
            "<strong>Stance, not workflow</strong>: không có bước cố định — agent adapt theo idea bạn mang đến",
            "Hỏi câu mở thread thay vì checklist; pivot khi có thông tin mới",
            "Vẽ <strong>ASCII diagram</strong> khi cần làm rõ (state machine, comparison table, data flow)",
            "Khảo sát codebase, surface risks &amp; unknowns, so sánh approaches",
            "Có <strong>Context7</strong> để verify API library (tránh hallucinate)",
            "Tự lưu design log cuối phiên vào <code>morkit/output/specs/YYYY-MM-DD-&lt;topic&gt;-design.md</code> (gồm 5 mục: problem · approaches · decisions · open questions · next step)",
        ],
        "when_to_use": [
            "Khi nhận một yêu cầu chưa rõ phạm vi và muốn tư duy cùng AI",
            "Trước khi gõ /morkit:propose hoặc /morkit:init",
            "Khi cần khảo sát mã nguồn / kiến trúc hiện tại trước khi đụng vào",
        ],
        "example_args": "tìm hiểu giúp tôi repo Notion-clone bao gồm các nhánh của nó",
        "example_note": "Agent vào explore mode: đọc inputs, mở thread tự do, vẽ ASCII diagram khi cần. Cuối phiên agent confirm rồi tự lưu design log để feed sang STEP 2 (function list) hoặc /morkit:propose.",
    },
    "skills.writing-plans": {
        "lede": "Khi đã có yêu cầu rõ ràng, dùng skill này để viết kế hoạch nhiều bước trước khi đụng code.",
        "details": [
            "Chuyển <strong>spec/design</strong> thành plan thực thi đánh số từng bước",
            "Mỗi bước có <strong>acceptance criteria</strong> và thứ tự phụ thuộc rõ ràng",
            "Plan lưu lại để <code>executing-plans</code> hoặc <code>subagent-driven-development</code> chạy sau",
            "Tách hẳn pha thiết kế và pha thực thi — bạn duyệt plan trước, code mới chạy",
        ],
        "when_to_use": [
            "Sau khi brainstorming đã chốt phương án",
            "Khi đã có yêu cầu cụ thể và cần chia nhỏ thành các bước",
        ],
        "example_args": "(tự lấy ngữ cảnh từ phiên brainstorming trước đó)",
        "example_note": "Kết quả là một file plan có các bước đánh số, mỗi bước kèm tiêu chí xác minh đã làm xong.",
    },
    "skills.executing-plans": {
        "lede": "Chạy plan từng bước trong một phiên làm việc riêng, có điểm dừng để bạn xem lại giữa chừng.",
        "details": [
            "Nạp plan, chạy <strong>lần lượt</strong> từng bước trong session riêng",
            "Dừng ở các <strong>checkpoint</strong> quan trọng để bạn xác nhận",
            "Bị chặn cho tới khi checklist có <code>Overall Decision: OK</code>",
            "Đối lập với <code>subagent-driven-development</code>: chậm hơn nhưng kiểm soát chặt hơn",
        ],
        "when_to_use": [
            "Khi plan đã viết xong và checklist review đã được duyệt OK",
            "Khi muốn chạy có kiểm soát, dừng để confirm ở mỗi mốc quan trọng",
        ],
        "example_args": "(tự nạp plan đã viết)",
        "example_note": "Bị chặn cho đến khi human duyệt checklist. Khi chạy, dừng ở các checkpoint để bạn xác nhận trước khi đi tiếp.",
    },
    "skills.subagent-driven-development": {
        "lede": "Khi plan có nhiều việc độc lập, spawn nhiều subagent chạy song song thay vì làm tuần tự.",
        "details": [
            "Nhận diện các bước <strong>độc lập</strong> trong plan (không chia sẻ state)",
            "Dispatch mỗi bước cho một subagent riêng, chạy đồng thời",
            "Tổng hợp kết quả từ các subagent thành output cuối",
            "Vẫn tuân thủ plan-review-gate giống <code>executing-plans</code>",
            "Nhanh hơn đáng kể với plan rộng — đổi lại kiểm soát ít chi tiết hơn",
        ],
        "when_to_use": [
            "Khi plan chứa các bước không phụ thuộc lẫn nhau",
            "Khi muốn đi nhanh hơn so với chạy tuần tự",
        ],
        "example_args": "(tự nạp plan)",
        "example_note": "Mỗi subagent đảm nhận một task. Vẫn bị chặn bởi gate review giống executing-plans.",
    },
    "skills.test-driven-development": {
        "lede": "Bắt buộc viết test trước, code sau. Quy trình Red → Green → Refactor.",
        "details": [
            "<strong>Red:</strong> viết test fail trước",
            "<strong>Green:</strong> viết code tối thiểu để test pass",
            "<strong>Refactor:</strong> dọn code, giữ test vẫn pass",
            "Không cho viết code production khi chưa có test fail",
            "Đây là rigid skill — không bỏ qua discipline kể cả khi 'task đơn giản'",
        ],
        "when_to_use": [
            "Khi triển khai bất kỳ tính năng hoặc bản sửa lỗi nào",
            "Trước khi viết code production",
        ],
        "example_args": "(gọi trước khi bắt tay code)",
        "example_note": "Viết test fail trước, rồi viết code tối thiểu để test pass, cuối cùng refactor cho gọn.",
    },
    "skills.systematic-debugging": {
        "lede": "Khi gặp lỗi, debug có hệ thống thay vì đoán mò. Tái hiện lỗi trước, sửa sau.",
        "details": [
            "Quy trình 5 bước bắt buộc:",
            "<ol><li>Tái hiện lỗi</li><li>Thu hẹp phạm vi</li><li>Đặt giả thuyết</li><li>Xác minh giả thuyết</li><li>Fix</li></ol>",
            "Cấm đoán mò — mỗi bước phải có <strong>evidence</strong> cụ thể (output, log, trace)",
            "Cấm fix khi chưa biết root cause",
        ],
        "when_to_use": [
            "Khi gặp bug, test thất bại hoặc hành vi bất thường",
            "Trước khi đề xuất bất kỳ bản sửa nào",
        ],
        "example_args": "(gọi khi gặp lỗi)",
        "example_note": "Tái hiện lỗi → thu hẹp phạm vi → đặt giả thuyết → xác minh → sửa. Không đoán mò.",
    },
    "skills.dispatching-parallel-agents": {
        "lede": "Khi có từ 2 việc độc lập trở lên, spawn nhiều agent chạy song song để tiết kiệm thời gian.",
        "details": [
            "Xác định task có thể chạy song song (không chia sẻ state, không phụ thuộc tuần tự)",
            "Spawn nhiều <code>Agent</code> tool call trong cùng một message với <code>run_in_background: true</code>",
            "Tổng hợp kết quả từ các agent lại",
            "Hợp với <strong>research nhiều hướng</strong> hoặc làm nhiều file độc lập cùng lúc",
        ],
        "when_to_use": [
            "Khi có 2 hoặc nhiều việc không phụ thuộc lẫn nhau",
            "Khi cần khảo sát nhiều khía cạnh cùng lúc",
        ],
        "example_args": "(gọi khi có nhiều việc song song)",
        "example_note": "Các agent chạy đồng thời, sau đó tổng hợp kết quả. Phù hợp với nghiên cứu nhiều hướng cùng lúc.",
    },
    "skills.using-git-worktrees": {
        "lede": "Tạo worktree riêng cho feature mới, không ảnh hưởng đến workspace hiện tại.",
        "details": [
            "Tạo git worktree ở thư mục riêng dựa trên branch hiện tại hoặc branch mới",
            "Có <strong>smart directory selection</strong>: không tạo trong thư mục đã có code",
            "Tránh xung đột khi đang dở việc trong workspace chính",
            "Hợp khi muốn thử một hướng khác mà không cần <code>git stash</code>",
        ],
        "when_to_use": [
            "Khi bắt đầu một feature cần làm cách ly khỏi workspace hiện tại",
            "Trước khi chạy plan thực thi có thể đụng nhiều file",
        ],
        "example_args": "(gọi trước khi cut branch)",
        "example_note": "Tạo worktree ở thư mục riêng, có kiểm tra an toàn sẵn để không xung đột với branch hiện tại.",
    },
    "skills.finishing-a-development-branch": {
        "lede": "Khi feature đã xong và test pass, skill gợi ý các lựa chọn đóng branch (merge, mở PR, hoặc bỏ).",
        "details": [
            "Phân tích trạng thái branch: commits ahead, tests, CI status, conflict với main",
            "Đưa ra 3 lựa chọn có cấu trúc:",
            "<ul><li><strong>Squash merge</strong> thẳng</li><li>Mở <strong>PR</strong> review trước khi merge</li><li><strong>Bỏ branch</strong> nếu thử nghiệm không thành</li></ul>",
            "Không tự action — chỉ đề xuất, bạn quyết định và execute",
        ],
        "when_to_use": [
            "Khi đã code xong, test pass hết",
            "Khi cần quyết định bước đóng nhánh",
        ],
        "example_args": "(gọi khi đã làm xong feature)",
        "example_note": "Đưa ra các lựa chọn: squash merge, mở PR thường, hoặc bỏ branch. Skill không tự action — chỉ đề xuất.",
    },
    "skills.verification-before-completion": {
        "lede": "Trước khi nói \"xong rồi\" hoặc commit, bắt buộc chạy lệnh kiểm tra thật và xem output thật.",
        "details": [
            "Nguyên tắc: <strong>evidence before assertions</strong>",
            "Cấm claim feature đã xong / bug đã fix / test đã pass nếu chưa có bằng chứng",
            "Bắt buộc chạy: build, test, lint, smoke run — và copy output thật ra",
            "Quan trọng trong AI-assisted dev để tránh báo cáo hồ đồ",
        ],
        "when_to_use": [
            "Trước khi báo cáo \"đã làm xong\" hay \"đã sửa rồi\"",
            "Trước khi commit hoặc mở PR",
        ],
        "example_args": "(gọi trước khi commit)",
        "example_note": "Bằng chứng có trước lời khẳng định. Phải có output thật mới được nói thành công.",
    },
    "skills.requesting-code-review": {
        "lede": "Khi feature đã xong, dùng skill này để chuẩn bị xin review một cách có hệ thống.",
        "details": [
            "Checklist trước khi mở PR:",
            "<ul><li>Build pass</li><li>Test pass</li><li>Tự rà soát code</li><li>PR description rõ ràng (summary + test plan)</li><li>Tag đúng người review</li></ul>",
            "Có thể chain với <code>/morkit:deep-review</code> để tự review chuyên sâu trước",
            "Mục tiêu: PR vào reviewer ở trạng thái sạch nhất có thể",
        ],
        "when_to_use": [
            "Sau khi đã làm xong một task hoặc một feature lớn",
            "Trước khi merge",
        ],
        "example_args": "(gọi khi feature đã xong)",
        "example_note": "Tự kiểm tra trước xem code đã đạt yêu cầu chưa. Có thể chạy /morkit:deep-review nội bộ trước khi gửi cho người.",
    },
    "skills.receiving-code-review": {
        "lede": "Khi nhận góp ý review, skill này giúp bạn hiểu rõ trước khi sửa — không đồng ý theo phản xạ.",
        "details": [
            "Phải <strong>hiểu rõ</strong> từng góp ý trước khi action",
            "<strong>Verify</strong> giả định reviewer đặt — đôi khi reviewer cũng nhầm",
            "<strong>Push back</strong> có lý nếu góp ý sai, không 'agree + fix' theo phản xạ",
            "Hợp khi bạn không chắc một suggestion có đúng không",
        ],
        "when_to_use": [
            "Khi đọc các comment review trên PR",
            "Đặc biệt khi feedback chưa rõ hoặc nghe có vẻ chưa hợp lý",
        ],
        "example_args": "(gọi khi đọc PR comments)",
        "example_note": "Bắt buộc hiểu rõ từng góp ý trước khi thực hiện. Không đồng ý lấy lệ.",
    },
    "skills.writing-skills": {
        "lede": "Khi cần tạo skill mới hoặc sửa skill cũ, dùng skill này để đảm bảo viết đúng chuẩn.",
        "details": [
            "Hướng dẫn cấu trúc file <code>SKILL.md</code>:",
            "<ul><li>YAML frontmatter (<code>name</code> + <code>description</code>)</li><li>Trigger \"Use when...\"</li><li>Workflow / checklist</li><li>Red flags</li><li>Examples thực tế</li></ul>",
            "Có verify step: test skill chạy được trong session thật trước khi commit",
            "Tránh skill bị invoke sai do description mơ hồ",
        ],
        "when_to_use": [
            "Khi viết file SKILL.md mới",
            "Khi sửa skill có sẵn",
            "Trước khi đưa skill vào sử dụng thực tế",
        ],
        "example_args": "(gọi khi soạn SKILL.md)",
        "example_note": "Đảm bảo frontmatter đúng định dạng, nội dung rõ ràng, có ví dụ đầy đủ và đã thử chạy thật.",
    },

    "commands.brainstorming": {
        "lede": "Vào explore mode — agent là thinking partner free-form, không workflow cứng, không bao giờ viết code. Shortcut gọi skill brainstorming.",
        "when_to_use": [
            "Khi nhận yêu cầu chưa rõ phạm vi và muốn tư duy cùng AI",
            "Trước khi gõ /morkit:propose hoặc /morkit:init",
            "Khi cần khảo sát mã nguồn / kiến trúc trước khi đụng vào",
        ],
        "example_args": "tìm hiểu giúp tôi repo Notion-clone bao gồm các nhánh của nó",
        "example_note": "Command alias gọi thẳng skill brainstorming. Cuối phiên agent lưu design log vào morkit/output/specs/YYYY-MM-DD-<topic>-design.md để feed bước tiếp (propose, init, function list…).",
    },
    "commands.write-plan": {
        "lede": "Command cũ — đã được thay bằng skill morkit:writing-plans.",
        "deprecated": True,
        "when_to_use": [
            "Đừng dùng nữa — dùng skill morkit:writing-plans thay thế",
        ],
        "example_args": "",
        "example_note": "Sẽ bị gỡ ở bản major tiếp theo.",
    },
    "commands.execute-plan": {
        "lede": "Command cũ — đã được thay bằng skill morkit:executing-plans.",
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
        "lede": "Review code chuyên sâu bằng 5 agent AI chạy song song (rủi ro, bảo mật, pattern, kiểm thử, quy ước).",
        "details": [
            "Dispatch 5 specialist subagent chạy song song:",
            "<ul><li><strong>Risk analyst</strong> — đánh giá rủi ro thay đổi</li><li><strong>Security auditor</strong> — vuln, secret leak, OWASP</li><li><strong>Pattern reviewer</strong> — anti-pattern, code smell</li><li><strong>Test reviewer</strong> — độ phủ, edge case</li><li><strong>Convention checker</strong> — CLAUDE.md, lint, style</li></ul>",
            "Tổng hợp thành một báo cáo Markdown dạng bảng",
            "Tôn trọng <code>CLAUDE.md</code> của project làm source of truth cao nhất",
        ],
        "when_to_use": [
            "Khi cần review chất lượng cao một PR hoặc git diff",
            "Trước khi merge một feature lớn",
        ],
        "example_args": "PR#123",
        "example_note": "Kết quả là một báo cáo dạng bảng Markdown gồm các phát hiện về rủi ro, bảo mật, pattern, độ phủ test và quy ước code.",
    },
    "commands.deep-review": {
        "lede": "Command chạy review chuyên sâu trên PR hoặc git diff, kết quả là báo cáo Markdown dạng bảng.",
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
        "details": [
            "Gọi 7 sub-skill theo thứ tự ít xung đột nhất: SRS, API, DB, system architecture, code standards, codebase summary, design guidelines",
            "3 chế độ chính:",
            "<ul><li><code>init</code> — tạo mới từ ProjectModel JSON</li><li><code>update</code> — áp dụng change/plan có sẵn</li><li><code>sync</code> — quét codebase và đề xuất cập nhật</li></ul>",
            "Theo các chuẩn: <strong>BrSE ITO Japan</strong> (SRS), <strong>arc42-lite</strong> (kiến trúc), <strong>Conventional Commits</strong> + <strong>MADR</strong> (guidelines)",
        ],
        "when_to_use": [
            "Khi cần sinh nguyên bộ tài liệu (SRS, API, DB, kiến trúc…) một lần",
            "Khi muốn các sub-skill phối hợp với nhau, ít xung đột nhất có thể",
        ],
        "example_args": "(gọi qua /morkit:init hoặc /morkit:update-doc)",
        "example_note": "Theo các chuẩn quen thuộc: BrSE ITO Japan cho SRS, arc42-lite cho kiến trúc, MADR cho ADR.",
    },
    "skills.generate-srs": {
        "lede": "Sinh hoặc cập nhật tài liệu yêu cầu phần mềm (SRS) theo chuẩn BrSE cho ITO Japan offshore.",
        "details": [
            "Render template SRS <strong>13 section + 2 phụ lục</strong>:",
            "<ul><li>Doc Control</li><li>Overview</li><li>Business Flow (kèm UC detail)</li><li>FR detail</li><li>Business Rules</li><li>Roles &amp; Permissions</li><li>NFR theo IPA-6 (kèm Security/PII)</li><li>Data Items với retention</li><li>External Interfaces</li><li>Reports</li><li>Acceptance / UAT</li><li>Traceability</li><li>Open Q&amp;A</li><li>Constraints / Assumptions / Risks (phụ lục)</li><li>Screen Index + Glossary (phụ lục)</li></ul>",
            "2 chế độ: <code>init</code> sinh từ ProjectModel JSON; <code>update</code> apply Delta và giữ phần bạn sửa tay",
        ],
        "when_to_use": [
            "Khi dự án cần SRS theo chuẩn của khách Nhật",
            "Khi yêu cầu thay đổi và cần làm mới SRS",
        ],
        "example_args": "(gọi qua /morkit:init hoặc /morkit:update-doc)",
        "example_note": "Gồm 13 mục lớn và 2 phụ lục: Doc Control, tổng quan, luồng nghiệp vụ, FR/NFR, quyền, dữ liệu, UAT, traceability...",
    },
    "skills.generate-api-docs": {
        "lede": "Sinh hoặc cập nhật tài liệu REST API.",
        "details": [
            "Render <code>api-docs.md</code> mô tả endpoint, request, response, error code",
            "3 chế độ:",
            "<ul><li><code>init</code> — sinh từ ProjectModel</li><li><code>update</code> — áp dụng Delta có sẵn</li><li><code>sync</code> — pipeline 2 bước: <strong>propose → apply</strong>, có checkbox để bạn tick chọn</li></ul>",
            "Chế độ sync quét REST route trong codebase, xuất file <code>sync-proposal.md</code>",
        ],
        "when_to_use": [
            "Khi cần tài liệu mô tả endpoint, request, response",
            "Khi route trong mã nguồn đã đổi và muốn đồng bộ lại tài liệu",
        ],
        "example_args": "(gọi qua /morkit:init / /morkit:update-doc / /morkit:sync)",
        "example_note": "Chế độ init sinh từ ProjectModel; update áp dụng thay đổi; sync quét mã và đề xuất nội dung cần cập nhật.",
    },
    "skills.generate-db-design": {
        "lede": "Sinh hoặc cập nhật tài liệu thiết kế database, có sơ đồ ERD bằng Mermaid.",
        "details": [
            "Render <code>database-design.md</code> gồm: mô tả bảng, cột, quan hệ, index",
            "Nhúng sơ đồ <strong>ERD</strong> vẽ bằng Mermaid",
            "3 chế độ: <code>init</code> / <code>update</code> / <code>sync</code>",
            "Sync quét ORM model (TypeORM, Prisma, SQLAlchemy...) và đề xuất <strong>Thêm / Sửa / Bỏ</strong> theo bảng",
        ],
        "when_to_use": [
            "Khi cần tài liệu mô tả schema DB",
            "Khi muốn đồng bộ tài liệu với ORM model trong mã nguồn",
        ],
        "example_args": "(gọi qua /morkit:init / /morkit:update-doc / /morkit:sync)",
        "example_note": "Sinh file database-design.md kèm ERD vẽ bằng Mermaid. Chế độ sync quét ORM và đề xuất Thêm/Sửa/Bỏ.",
    },
    "skills.generate-system-architecture": {
        "lede": "Sinh hoặc cập nhật tài liệu kiến trúc hệ thống theo arc42-lite, kèm sơ đồ thành phần bằng Mermaid.",
        "details": [
            "Render <code>system-architecture.md</code> theo <strong>arc42-lite 8 section</strong>:",
            "<ul><li>Introduction</li><li>Constraints</li><li>Context</li><li>Solution Strategy</li><li>Building Blocks</li><li>Runtime</li><li>Deployment</li><li>Crosscutting</li></ul>",
            "Nhúng sơ đồ component bằng Mermaid",
            "Sync quét services, packages, Dockerfile, k8s manifest và import graph để đề xuất Component cần Thêm / Bỏ",
        ],
        "when_to_use": [
            "Khi cần tài liệu kiến trúc cho dự án",
            "Khi muốn nhúng sơ đồ component vẽ bằng Mermaid",
        ],
        "example_args": "(gọi qua /morkit:init / /morkit:update-doc / /morkit:sync)",
        "example_note": "Gồm 8 mục theo chuẩn arc42-lite. Sync quét services, packages, Docker, k8s và đồ thị import.",
    },
    "skills.generate-code-standards": {
        "lede": "Sinh hoặc cập nhật tài liệu quy ước code (Conventional Commits + cấu hình lint/format).",
        "details": [
            "Render <code>code-standards.md</code> từ ProjectModel",
            "Auto-extract rule từ ESLint, Prettier, Ruff, EditorConfig... đang có trong repo",
            "Phân loại theo scope: <strong>LNT</strong> (lint) / <strong>NAM</strong> (naming) / <strong>CMT</strong> (commit) / <strong>FMT</strong> (format)",
            "Sync đề xuất Thêm / Bỏ rule khi cấu hình đổi",
            "Nếu repo đã có <code>CONTRIBUTING.md</code>, link sang thay vì duplicate",
        ],
        "when_to_use": [
            "Khi dự án cần một tài liệu thống nhất về quy ước code",
            "Khi muốn rút quy ước từ các file cấu hình lint/format đang có",
        ],
        "example_args": "(gọi qua /morkit:init / /morkit:update-doc / /morkit:sync)",
        "example_note": "Nếu đã có CONTRIBUTING.md, sẽ link sang chứ không nhân đôi nội dung.",
    },
    "skills.generate-codebase-summary": {
        "lede": "Sinh hoặc cập nhật tài liệu tổng quan mã nguồn dạng README: tech stack, cấu trúc, gói, entry point.",
        "details": [
            "Render <code>codebase-summary.md</code> dạng README-style overview gồm:",
            "<ul><li>Tech stack</li><li>Repo layout (file tree gọn)</li><li>Packages chính</li><li>Entry points</li><li>LOC theo ngôn ngữ</li></ul>",
            "Sync quét file tree + manifest (<code>package.json</code>, <code>pyproject.toml</code>, <code>go.mod</code>...) và đề xuất Thêm / Bỏ",
            "Hợp khi <strong>onboard người mới</strong> — nắm dự án trong 5 phút",
        ],
        "when_to_use": [
            "Khi cần một bản tổng quan dự án dành cho người mới onboard",
            "Khi muốn ai đó hiểu nhanh dự án mà không cần đọc hết code",
        ],
        "example_args": "(gọi qua /morkit:init / /morkit:update-doc / /morkit:sync)",
        "example_note": "Liệt kê công nghệ, bố cục thư mục, các package, entry point và số dòng code theo ngôn ngữ.",
    },
    "skills.generate-design-guidelines": {
        "lede": "Sinh hoặc cập nhật tài liệu Design Principles, Patterns và các ADR (MADR format).",
        "details": [
            "Render <code>design-guidelines.md</code> gồm 3 phần:",
            "<ul><li><strong>Design Principles</strong></li><li><strong>Patterns</strong></li><li><strong>ADRs</strong> theo chuẩn MADR</li></ul>",
            "Khi <code>init</code>, mỗi ADR có file riêng tại <code>docs/adr/NNN-slug.md</code>",
            "Phân loại theo scope: <strong>DPR</strong> / <strong>PTN</strong> / <strong>ADR</strong>",
            "<em>Không hỗ trợ</em> chế độ sync — guidelines là quyết định của người, không auto-generate",
        ],
        "when_to_use": [
            "Khi cần một tài liệu thống nhất về nguyên tắc thiết kế",
            "Khi muốn ghi lại các quyết định kiến trúc theo MADR format",
        ],
        "example_args": "(gọi qua /morkit:init / /morkit:update-doc)",
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
    "commands.update-doc": {
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
            "Khi /morkit:init hoặc /morkit:update-doc báo lỗi cài đặt",
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
        "details": [
            "Claude <strong>tự invoke</strong> ở đầu mọi phiên làm việc với morkit",
            "Chạy trước khi trả lời bất kỳ câu hỏi nào (kể cả câu hỏi làm rõ)",
            "Establish cách Claude tìm và gọi các skill khác qua Skill tool",
            "Đảm bảo các overlay (như <code>plan-review-gate</code>) hoạt động đúng",
            "Không gọi tay — chỉ là cơ chế nền",
        ],
        "when_to_use": [
            "Tự chạy mỗi khi bắt đầu một phiên mới — bạn không cần gọi tay",
            "Khi cần Claude hiểu cách điều phối các skill khác trong morkit",
        ],
        "example_args": "(tự gọi)",
        "example_note": "Bắt buộc chạy ở đầu mỗi phiên. Đây là điều kiện để các skill khác hoạt động đúng.",
    },
}
