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

    items = C.GROUPS[group]
    # Same-kind siblings first (exclude self)
    for sib in items.get(kind, []):
        if sib == slug:
            continue
        href = f"../{kind}/{sib}.html"
        out.append((href, f"/morkit:{sib}" if kind == "commands" else sib, f"{C.GROUP_LABELS[group]} · {kind[:-1]}"))
    # Cross-kind siblings if we have room
    cross_kind = "skills" if kind == "commands" else "commands"
    for sib in items.get(cross_kind, []):
        if len(out) >= 4:
            break
        href = f"../{cross_kind}/{sib}.html"
        out.append((href, f"/morkit:{sib}" if cross_kind == "commands" else sib, f"{C.GROUP_LABELS[group]} · {cross_kind[:-1]}"))
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
         "Scaffold proposal/design/tasks + review-checklist gate"),
        ("Plan &amp; build",
         ", ".join(link_skill(s) for s in [
            "brainstorming", "writing-plans", "executing-plans",
            "subagent-driven-development", "test-driven-development",
            "systematic-debugging", "dispatching-parallel-agents",
            "using-git-worktrees", "finishing-a-development-branch",
            "verification-before-completion",
            "requesting-code-review", "receiving-code-review",
            "writing-skills",
         ]),
         "Brainstorm, viết plan, thực thi plan, TDD, debug, review"),
        ("Code review",
         ", ".join(link_cmd(s) for s in ["deep-review", "deep-review-doctor", "deep-review-post"]),
         "Review code bằng 5 chuyên gia AI song song"),
        ("Doc generation",
         ", ".join(link_cmd(s) for s in ["setup", "init", "update", "sync", "apply-sync", "doctor"]),
         "Sinh SRS + API + DB doc cho ITO Japan offshore"),
    ]
    groups_table_rows = "\n".join(
        f"      <tr><td><strong>{g}</strong></td><td>{items}</td><td>{desc}</td></tr>"
        for g, items, desc in groups_rows
    )

    # Section 3 — Slash commands (15 dòng, link tới detail)
    cmd_rows = [
        ("propose [mô tả]",        "Sinh đầy đủ proposal + design + tasks + review-checklist"),
        ("review [tên]",           "Tạo lại review-checklist từ Google Doc"),
        ("archive [tên]",          "Đóng change sau merge"),
        ("brainstorm",             "<span class=\"tag deprecated\">Deprecated</span> Dùng skill <code>brainstorming</code>"),
        ("write-plan",             "<span class=\"tag deprecated\">Deprecated</span> Dùng skill <code>writing-plans</code>"),
        ("execute-plan",           "<span class=\"tag deprecated\">Deprecated</span> Dùng skill <code>executing-plans</code>"),
        ("deep-review [target]",   "Review trên git diff hoặc PR (5 specialists song song)"),
        ("deep-review-doctor",     "Health-check Deep Review installation"),
        ("deep-review-post",       "Post report làm PR comment"),
        ("setup",                  "Bootstrap Python venv (~30-60s, 1 lần)"),
        ("init",                   "Sinh fresh SRS + API + DB từ ProjectModel JSON"),
        ("update",                 "Apply change/plan vào doc"),
        ("sync",                   "Scan codebase, đề xuất update"),
        ("apply-sync",             "Apply đề xuất từ sync"),
        ("doctor",                 "Health-check docs-hero install"),
    ]
    cmd_table_rows = "\n".join(
        f'      <tr><td><a href="commands/{slug.split()[0]}.html"><code>/morkit:{slug}</code></a></td><td>{purpose}</td></tr>'
        for slug, purpose in cmd_rows
    )

    sections = f"""<h2>1. Cài đặt</h2>
  <p>Yêu cầu: <a href="https://docs.anthropic.com/claude/docs/claude-code" target="_blank" rel="noopener">Claude Code</a> và Node.js ≥ 18.</p>
  <pre><code>/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install morkit@mor-duongmh</code></pre>
  <p class="lede" style="font-size:14px;">Cài xong là dùng được luôn — không cần setup gì thêm trong từng project.</p>

  <h2>2. morkit có những gì?</h2>
  <p>Một plugin chứa 4 nhóm chức năng dưới namespace <code>/morkit:*</code>:</p>
  <table>
    <thead><tr><th>Nhóm</th><th>Bao gồm</th><th>Để làm gì</th></tr></thead>
    <tbody>
{groups_table_rows}
    </tbody>
  </table>
  <p class="lede" style="font-size:14px;">Tổng cộng: <strong>22 skills + 9 specialist agents + 15 slash commands</strong> đều có prefix <code>/morkit:</code>.</p>

  <h2>3. Slash command đầy đủ</h2>
  <p>Bấm vào tên command để xem chi tiết, cách dùng và ví dụ.</p>
  <table>
    <thead><tr><th>Command</th><th>Việc</th></tr></thead>
    <tbody>
{cmd_table_rows}
    </tbody>
  </table>

  <h2>4. Plan review gate (chốt chặn human-in-the-loop)</h2>
  <p>Sau {link_cmd('propose')}, plugin sinh <code>morkit/output/spec/&lt;tên&gt;/review-checklist.md</code>
  từ <a href="https://docs.google.com/document/d/184wY2N2WOUExmZrClvHCfcRCnSQsJYvav6gc6JwL6xc" target="_blank" rel="noopener">Google Doc canonical của Mor</a>.</p>

  <p>Auto-detect variant (BE/FE × Feature/BugFix/Refactor). Override:</p>
  <pre><code>/morkit:review --variant FE-BugFix
/morkit:review --refresh</code></pre>

  <p>Bạn mở file, tick từng mục, sửa dòng cuối:</p>
  <pre><code>- Overall Decision: PENDING
+ Overall Decision: OK</code></pre>

  <p>→ {link_skill('executing-plans')} mở khoá.</p>

  <div class="note">
    <strong>Hai lớp bảo vệ song song</strong> (defense-in-depth):
    <ol>
      <li><strong>PreToolUse hook</strong> — Claude Code chặn tool call ngay từ harness</li>
      <li><strong>Skill content</strong> — mỗi skill tự kiểm tra ở Step 0 trước khi làm việc</li>
    </ol>
  </div>

  <h2>5. Companion tools (Context7 + RTK)</h2>
  <p>Hai tool nâng chất lượng research và giảm token. Plugin xử lý lịch sự — không cài silent.</p>
  <table>
    <thead><tr><th>Tool</th><th>Vai trò</th><th>Cách cài</th></tr></thead>
    <tbody>
      <tr>
        <td><a href="https://github.com/upstash/context7" target="_blank" rel="noopener">Context7</a></td>
        <td>Trả docs/API version-specific cho library, agent không cần đoán</td>
        <td><strong>Lazy</strong> — plugin tự <code>npx -y ctx7</code> khi cần. MCP optional.</td>
      </tr>
      <tr>
        <td><a href="https://github.com/rtk-ai/rtk" target="_blank" rel="noopener">RTK</a></td>
        <td>Nén output bash, giảm 60-90% token</td>
        <td><strong>Hỏi 1 lần</strong> session đầu — bạn chọn Yes/Skip/Don't ask again.</td>
      </tr>
    </tbody>
  </table>
  <p class="lede" style="font-size:14px;">🎯 Context7 đã active trong 6 brainstorm/execute skills + 3 spec-workflow skill —
  agent sẽ tự gọi Context7 thay vì đoán API.</p>

  <p>Cài RTK thủ công:</p>
  <pre><code>curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
rtk init -g</code></pre>

  <p>Cài Context7 dạng MCP (full features):</p>
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

    # Overview
    (DOCS_DIR / "index.html").write_text(render_overview(), encoding="utf-8")
    written += 1

    print(f"Wrote {written} files. ({len(skill_slugs)} skills + {len(command_slugs)} commands + 1 overview)")
    print(f"  → {out_skills.relative_to(REPO_ROOT)}/")
    print(f"  → {out_commands.relative_to(REPO_ROOT)}/")
    print(f"  → docs/index.html")


if __name__ == "__main__":
    main()
