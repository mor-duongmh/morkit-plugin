#!/usr/bin/env python3
"""Build morkit docs site (no runtime deps; stdlib only).

Reads:
  - plugins/morkit/skills/<name>/SKILL.md   (frontmatter: name, description)
  - plugins/morkit/commands/<name>.md       (frontmatter: description)

Writes:
  - docs/skills/<name>.html      (26 pages)
  - docs/commands/<name>.html    (15 pages)

Idempotent — safe to run multiple times. Overwrites existing files.
Run from repo root:
    python3 docs/_scaffolder/build.py
"""

from __future__ import annotations
import re
import sys
from pathlib import Path

SCAFFOLD_DIR = Path(__file__).resolve().parent
DOCS_DIR     = SCAFFOLD_DIR.parent
REPO_ROOT    = DOCS_DIR.parent
SKILLS_DIR   = REPO_ROOT / "plugins" / "morkit" / "skills"
COMMANDS_DIR = REPO_ROOT / "plugins" / "morkit" / "commands"

sys.path.insert(0, str(SCAFFOLD_DIR))
import content as C            # noqa: E402
import templates as T          # noqa: E402


# ---------------------------------------------------------------- parsing
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.S)


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    out = {}
    block = m.group(1)
    # Naive single-line key: value parser (good enough for {name, description})
    for line in block.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        out[key.strip()] = val
    return out


def read_skill(slug: str) -> dict:
    p = SKILLS_DIR / slug / "SKILL.md"
    if not p.exists():
        return {"name": slug, "description": ""}
    fm = parse_frontmatter(p.read_text(encoding="utf-8"))
    return {"name": fm.get("name", slug), "description": fm.get("description", "")}


def read_command(slug: str) -> dict:
    p = COMMANDS_DIR / f"{slug}.md"
    if not p.exists():
        return {"name": slug, "description": ""}
    fm = parse_frontmatter(p.read_text(encoding="utf-8"))
    # commands typically don't have `name:` in frontmatter — use slug
    return {"name": fm.get("name", slug), "description": fm.get("description", "")}


# ---------------------------------------------------------------- helpers
def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )


def is_deprecated(desc: str, curated: dict) -> bool:
    if curated.get("deprecated"):
        return True
    return desc.strip().lower().startswith("deprecated")


def related_for(kind: str, slug: str) -> list[tuple[str, str, str]]:
    """Return up to 4 related items as (href, title, sub) tuples."""
    group = C.group_of(kind, slug)
    out: list[tuple[str, str, str]] = []
    if group == "misc":
        return out

    kind_vn = {"skills": "skill", "commands": "command"}
    items = C.GROUPS[group]
    # Same-kind siblings first (exclude self)
    for sib in items.get(kind, []):
        if sib == slug:
            continue
        href = f"../{kind}/{sib}.html"
        out.append((href, f"/morkit:{sib}" if kind == "commands" else sib, f"{C.GROUP_LABELS[group]} · {kind_vn[kind]}"))
    # Cross-kind siblings if we have room
    cross_kind = "skills" if kind == "commands" else "commands"
    for sib in items.get(cross_kind, []):
        if len(out) >= 4:
            break
        href = f"../{cross_kind}/{sib}.html"
        out.append((href, f"/morkit:{sib}" if cross_kind == "commands" else sib, f"{C.GROUP_LABELS[group]} · {kind_vn[cross_kind]}"))
    return out[:6]


def fallback_when_to_use(description: str) -> list[str]:
    """Heuristic fallback if no curated bullets supplied."""
    desc = description.strip()
    if not desc:
        return ["Tham khảo mô tả ở phần 'Để làm gì' phía trên."]
    # Try to split on common cue phrases
    parts = re.split(r"(?:Use when|Triggered by|Run once|Run when)\s*", desc, flags=re.I)
    if len(parts) > 1:
        cue = parts[1].split(".")[0].strip()
        if cue:
            return [f"Khi {cue[0].lower()}{cue[1:]}." if cue and cue[0].isupper() else f"Khi {cue}."]
    return ["Tham khảo mô tả ở phần 'Để làm gì' phía trên."]


# ---------------------------------------------------------------- render
def render_one(kind: str, slug: str) -> str:
    """kind: 'skills' | 'commands'"""
    if kind == "skills":
        meta = read_skill(slug)
    else:
        meta = read_command(slug)

    curated = C.CURATED.get(f"{kind}.{slug}", {})
    name = meta["name"] or slug
    description = meta["description"]
    lede = curated.get("lede") or description or f"{name}"
    details = curated.get("details", "")

    deprecated = is_deprecated(description, curated)

    group = C.group_of(kind, slug)
    group_label = C.GROUP_LABELS.get(group, "Khác")

    when_bullets = curated.get("when_to_use") or fallback_when_to_use(description)

    invocation = f"/morkit:{slug}"
    args = curated.get("example_args", "")
    example_note = curated.get("example_note",
                               "Đây là ví dụ minh hoạ — tham khảo SKILL.md để xem cú pháp đầy đủ.")

    related = related_for(kind, slug)
    cards_html = "\n".join(
        f"    {T.related_card_html(href, html_escape(title), html_escape(sub))}"
        for href, title, sub in related
    ) or '    <p class="lede" style="font-size:13px;">(Không có item liên quan trong cùng nhóm.)</p>'

    # `kind` in templates is singular ("skill" / "command")
    page_kind = "skill" if kind == "skills" else "command"
    return T.detail_page(
        kind=page_kind,
        slug=slug,
        name=name,
        lede=html_escape(lede),
        details=details,  # raw HTML allowed (contains <code> spans)
        group_label=group_label,
        deprecated=deprecated,
        when_bullets=[html_escape(b) for b in when_bullets],
        invocation=invocation,
        args=html_escape(args),
        example_note=html_escape(example_note),
        related_cards_html=cards_html,
    )


def render_overview() -> str:
    """Render docs/index.html — 5 sections (Cài đặt / Morkit có gì / Slash
    commands / Plan review gate / Companion tools). No "Workflow điển hình",
    no License (user decisions)."""

    # Section 2 — Morkit có gì (4 nhóm bảng, link tới detail)
    def link_skill(slug):
        return f'<a href="skills/{slug}.html"><code>{slug}</code></a>'
    def link_cmd(slug):
        return f'<a href="commands/{slug}.html"><code>/morkit:{slug}</code></a>'

    groups_rows = [
        ("Spec workflow",
         ", ".join(link_cmd(s) for s in ["propose", "review", "archive"]),
         "Tự sinh proposal, design, tasks và checklist để bạn duyệt trước khi cho code chạy."),
        ("Plan &amp; build",
         # Most-used 6 skill — 7 skill phụ trợ khác (dispatching-parallel-agents,
         # using-git-worktrees, finishing-a-development-branch,
         # verification-before-completion, requesting-code-review,
         # receiving-code-review, writing-skills) vẫn có trang detail nhưng
         # không hiện trong overview để tránh nhiễu cho người mới.
         ", ".join(link_skill(s) for s in [
            "brainstorming", "writing-plans", "executing-plans",
            "subagent-driven-development", "test-driven-development",
            "systematic-debugging",
         ]),
         "Suy nghĩ ý tưởng, viết plan, chạy plan từng bước, viết test trước, debug có hệ thống."),
        ("Code review",
         ", ".join(link_cmd(s) for s in ["deep-review", "deep-review-doctor", "deep-review-post"]),
         "Review code chuyên sâu bằng 5 agent AI chạy song song."),
        ("Doc generation",
         link_cmd("docs"),
         "Sinh bộ tài liệu dự án tối ưu cho AI agent: taxonomy + mỏ neo, file nhỏ liên kết chéo (LLM-driven, không Python)."),
    ]
    groups_table_rows = "\n".join(
        f"      <tr><td><strong>{g}</strong></td><td>{items}</td><td>{desc}</td></tr>"
        for g, items, desc in groups_rows
    )

    # Section 3 — Danh sách /morkit:* theo 4 nhóm (giống README).
    # Mỗi row: (kind, slug, purpose). kind ∈ {"command", "skill"} — quyết định
    # link đi tới commands/<slug>.html hay skills/<slug>.html. User cuối gọi cả
    # 2 bằng cú pháp /morkit:<slug> giống nhau, không cần phân biệt.
    #
    # Plan & build nội bộ là skill — người dùng gọi /morkit:<name> như command.
    # Có 1 command brainstorming (alias gọi skill cùng tên); 2 command cũ
    # write-plan/execute-plan vẫn deprecated (chỉ in deprecation warning).
    sub_sections = [
        ("Spec workflow", [
            ("command", "propose [mô tả]", "Sinh đầy đủ proposal, design, tasks và checklist trong một lần chạy."),
            ("command", "review [tên]",    "Tạo hoặc làm mới checklist duyệt thiết kế cho một change."),
            ("command", "archive [tên]",   "Đóng một change folder sau khi đã merge và deploy ổn."),
        ]),
        ("Plan & build", [
            ("skill", "brainstorming",               "Suy nghĩ ý tưởng và đọc codebase, không code."),
            ("skill", "writing-plans",               "Viết plan nhiều bước từ ý tưởng đã chốt."),
            ("skill", "executing-plans",             "Chạy plan từng bước (bị review-gate chặn cho tới khi human duyệt)."),
            ("skill", "subagent-driven-development", "Chạy plan song song bằng nhiều subagent — nhanh hơn executing tuần tự."),
            ("skill", "test-driven-development",     "TDD discipline — viết test trước, code sau, refactor cuối."),
            ("skill", "systematic-debugging",        "Debug 5 bước có hệ thống — không đoán mò."),
        ]),
        ("Code review", [
            ("command", "deep-review [target]", "Review chuyên sâu trên PR hoặc git diff (5 agent AI chạy song song)."),
            ("command", "deep-review-doctor",   "Kiểm tra cài đặt Deep Review đã đủ điều kiện chạy chưa."),
            ("command", "deep-review-post",     "Post báo cáo review lên PR làm comment."),
        ]),
        ("Doc generation", [
            ("command", "docs", "Sinh/cập nhật bộ tài liệu dự án tối ưu cho AI agent. Chế độ: init | update | summarize (LLM-driven, không Python)."),
        ]),
    ]

    def render_sub_section(label, rows):
        body = "\n".join(
            f'      <tr><td><a href="{kind}s/{slug.split()[0]}.html"><code>/morkit:{slug}</code></a></td><td>{purpose}</td></tr>'
            for kind, slug, purpose in rows
        )
        return f"""  <h3>{label}</h3>
  <table>
    <thead><tr><th>Command</th><th>Để làm gì</th></tr></thead>
    <tbody>
{body}
    </tbody>
  </table>"""

    section3_blocks = "\n\n".join(render_sub_section(label, rows) for label, rows in sub_sections)

    sections = f"""<h2>1. Cài đặt</h2>
  <p>Cần có: <a href="https://docs.anthropic.com/claude/docs/claude-code" target="_blank" rel="noopener">Claude Code</a> và Node.js từ 18 trở lên.</p>
  <pre><code>/plugin add marketplace github:mor-duongmh/morkit-plugin
/plugin install morkit@mor-duongmh</code></pre>
  <p class="lede" style="font-size:14px;">Cài xong là dùng được luôn — không cần làm gì thêm trong từng dự án.</p>

  <h2>2. morkit có những gì?</h2>
  <p>Một plugin gói 4 nhóm chức năng, tất cả gọi qua tiền tố <code>/morkit:*</code>:</p>
  <table>
    <thead><tr><th>Nhóm</th><th>Bao gồm</th><th>Để làm gì</th></tr></thead>
    <tbody>
{groups_table_rows}
    </tbody>
  </table>
  <p class="lede" style="font-size:14px;">Tổng cộng <strong>19 skill + 8 agent chuyên trách + 10 slash command</strong>, tất cả đều có tiền tố <code>/morkit:</code>.</p>

  <h2>3. Danh sách command</h2>
  <p>Bấm vào tên command để xem giải thích chi tiết, cách gọi và ví dụ.</p>

{section3_blocks}

  <h2>4. Companion tools (Context7 + RTK)</h2>
  <p>Hai công cụ giúp agent trả lời chính xác hơn và tiết kiệm token. Plugin không cài lặng lẽ — sẽ hỏi bạn trước.</p>
  <table>
    <thead><tr><th>Công cụ</th><th>Vai trò</th><th>Cách cài</th></tr></thead>
    <tbody>
      <tr>
        <td><a href="https://github.com/upstash/context7" target="_blank" rel="noopener">Context7</a></td>
        <td>Trả về tài liệu/API đúng phiên bản cho thư viện, agent không phải đoán.</td>
        <td>Cài lười — plugin tự gọi <code>npx -y ctx7</code> khi cần.</td>
      </tr>
      <tr>
        <td><a href="https://github.com/rtk-ai/rtk" target="_blank" rel="noopener">RTK</a></td>
        <td>Nén output của lệnh bash, giảm 60-90% token.</td>
        <td>Hỏi 1 lần ở phiên đầu — bạn chọn Cài / Bỏ qua / Đừng hỏi lại.</td>
      </tr>
    </tbody>
  </table>
  <p class="lede" style="font-size:14px;">Context7 đã được bật sẵn trong 6 skill nhóm Lên kế hoạch và 3 skill nhóm Viết spec —
  agent sẽ tự gọi Context7 thay vì đoán API.</p>

  <p>Cài RTK thủ công:</p>
  <pre><code>curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
rtk init -g</code></pre>

  <p>Cài Context7 dạng MCP (đầy đủ tính năng):</p>
  <pre><code>npx -y ctx7 setup</code></pre>
"""
    return T.overview_page(sections_html=sections)


def main():
    out_skills = DOCS_DIR / "skills"
    out_commands = DOCS_DIR / "commands"
    out_skills.mkdir(parents=True, exist_ok=True)
    out_commands.mkdir(parents=True, exist_ok=True)

    # Discover slugs from filesystem (source of truth)
    skill_slugs = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir())
    command_slugs = sorted(p.stem for p in COMMANDS_DIR.glob("*.md"))

    written = 0
    for slug in skill_slugs:
        html = render_one("skills", slug)
        (out_skills / f"{slug}.html").write_text(html, encoding="utf-8")
        written += 1
    for slug in command_slugs:
        html = render_one("commands", slug)
        (out_commands / f"{slug}.html").write_text(html, encoding="utf-8")
        written += 1

    # NOTE: docs/index.html is the hand-maintained "v2 landing" (promoted from the
    # old docs-v2.html). build.py NO LONGER overwrites it — doing so would clobber
    # the hand-crafted hub. render_overview() is kept for reference but not called.

    # Cleanup orphans: HTML files in out dirs whose source .md no longer exists
    orphans = []
    for p in out_skills.glob("*.html"):
        if p.stem not in skill_slugs:
            orphans.append(p)
    for p in out_commands.glob("*.html"):
        if p.stem not in command_slugs:
            orphans.append(p)
    for p in orphans:
        p.unlink()

    print(f"Wrote {written} files. ({len(skill_slugs)} skills + {len(command_slugs)} commands)")
    if orphans:
        print(f"Cleaned {len(orphans)} orphan(s): {[str(p.relative_to(REPO_ROOT)) for p in orphans]}")
    print(f"  → {out_skills.relative_to(REPO_ROOT)}/")
    print(f"  → {out_commands.relative_to(REPO_ROOT)}/")
    print(f"  (index.html left untouched — hand-maintained v2 landing)")


if __name__ == "__main__":
    main()
