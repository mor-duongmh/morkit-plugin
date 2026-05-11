"""HTML templates for morkit docs site.

All CSS is inlined per file (user decision — keeps each page self-contained,
no shared asset coupling). Theme toggle is ~15 LOC of inline JS, no runtime
deps required.
"""

# Single shared CSS block — copied inline into every generated page.
CSS = r"""
:root {
  --bg: #fbf8f2; --bg-elev: #ffffff; --bg-subtle: #f0ece2; --bg-window: #ebe7dd;
  --fg: #1a1a1a; --fg-muted: #5a5a55; --fg-subtle: #908a7e;
  --border: #e5dfd0; --border-strong: #c8c0ad;
  --accent: #b04a2f; --accent-fg: #ffffff;
  --code-bg: #faf6ec; --code-fg: #1a1a1a;
  --code-key: #b04a2f; --code-str: #5b7a3a; --code-com: #908a7e;
  --shadow-1: 0 1px 2px rgba(0,0,0,.04);
  --shadow-2: 0 4px 12px rgba(0,0,0,.06);
}
[data-theme="dark"] {
  --bg: #101010; --bg-elev: #161616; --bg-subtle: #1c1c1c; --bg-window: #0a0a0a;
  --fg: #ffffff; --fg-muted: #a8a29e; --fg-subtle: #75716c;
  --border: #2b2b2b; --border-strong: #3a3a3a;
  --accent: #ff8b5a; --accent-fg: #101010;
  --code-bg: #0d0d0d; --code-fg: #ffffff;
  --code-key: #ff8b5a; --code-str: #a3c982; --code-com: #75716c;
  --shadow-1: 0 1px 2px rgba(0,0,0,.4);
  --shadow-2: 0 4px 12px rgba(0,0,0,.5);
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  background: var(--bg); color: var(--fg);
  font-family: "Geist", "Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  font-size: 15px; line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
.mono, pre, code {
  font-family: "Geist Mono", "JetBrains Mono", "Fira Code", "SF Mono", Menlo, Consolas, monospace;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.page { max-width: 880px; margin: 0 auto; padding: 32px 20px 80px; }
.crumbs {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 28px;
  font-size: 13px; color: var(--fg-muted);
}
.crumbs a { color: var(--fg-muted); }
.crumbs a:hover { color: var(--accent); }
.crumbs .path { font-family: "Geist Mono", monospace; }
.toggle {
  background: var(--bg-elev); color: var(--fg);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 4px 10px; font-size: 12px; cursor: pointer;
}
.toggle:hover { border-color: var(--border-strong); }
h1 {
  font-size: 32px; line-height: 1.2; margin: 0 0 8px;
  font-weight: 700; letter-spacing: -0.01em;
}
h2 {
  font-size: 18px; margin: 36px 0 12px;
  font-weight: 600;
  padding-bottom: 8px; border-bottom: 1px solid var(--border);
}
h3 {
  font-size: 12px; margin: 24px 0 8px;
  font-weight: 600; color: var(--fg-muted);
  text-transform: uppercase; letter-spacing: 0.06em;
}
.lede {
  font-size: 16px; color: var(--fg-muted); margin: 0 0 12px;
  line-height: 1.55;
}
.tag {
  display: inline-block; font-size: 11px; padding: 2px 8px;
  border: 1px solid var(--border-strong); border-radius: 999px;
  color: var(--fg-muted);
  margin-right: 6px;
  text-transform: uppercase; letter-spacing: 0.04em;
}
.tag.deprecated { color: var(--accent); border-color: var(--accent); }
ul, ol { padding-left: 22px; }
li { margin: 4px 0; }
ul.duties { padding-left: 0; list-style: none; }
ul.duties > li {
  position: relative; padding: 8px 12px 8px 28px;
  border-left: 2px solid var(--border);
  margin: 0 0 4px 0;
}
ul.duties > li::before {
  content: "›"; position: absolute; left: 10px; top: 8px;
  color: var(--accent); font-weight: 600;
}
/* When a duty-bullet only contains a nested <ul>, hide its chevron+border so
   the nested items visually attach to the previous bullet above. */
ul.duties > li:has(> ul:only-child) {
  border-left: 0; padding: 0 0 4px 28px; margin-top: -8px;
}
ul.duties > li:has(> ul:only-child)::before { content: none; }
ul.duties ul { margin: 4px 0 2px 0; padding-left: 18px; list-style: disc; }
ul.duties ul li {
  margin: 3px 0; padding: 0; border: 0;
  color: var(--fg-muted);
}
ul.duties ul li::before { content: none; }
ul.duties ul li code { font-size: 0.88em; }
pre {
  background: var(--code-bg); color: var(--code-fg);
  padding: 14px 16px; border-radius: 8px;
  overflow-x: auto; font-size: 13px; line-height: 1.55;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-1);
}
code { background: var(--code-bg); padding: 1px 5px; border-radius: 4px; font-size: 0.9em; }
pre code { background: transparent; padding: 0; }
.window {
  background: var(--bg-window); border: 1px solid var(--border);
  border-radius: 10px; overflow: hidden;
  box-shadow: var(--shadow-2);
  margin: 12px 0 16px;
}
.window-bar {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 12px; background: var(--bg-subtle);
  border-bottom: 1px solid var(--border);
}
.dot { width: 11px; height: 11px; border-radius: 50%; background: var(--border-strong); }
.dot.r { background: #ff5f56; } .dot.y { background: #ffbd2e; } .dot.g { background: #27c93f; }
.window-title {
  margin-left: 8px; font-size: 12px; color: var(--fg-subtle);
  font-family: "Geist Mono", monospace;
}
.window pre { margin: 0; border: 0; border-radius: 0; box-shadow: none; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }
th, td {
  text-align: left; padding: 8px 10px;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
th { font-weight: 600; color: var(--fg-muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }
td code { font-size: 12px; }
.related-grid {
  display: grid; gap: 8px;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  margin-top: 8px;
}
.related-card {
  display: block; padding: 10px 12px;
  border: 1px solid var(--border); border-radius: 8px;
  background: var(--bg-elev); color: var(--fg);
  font-size: 13px;
}
.related-card:hover { border-color: var(--accent); text-decoration: none; }
.related-card .ttl { font-weight: 600; }
.related-card .sub { color: var(--fg-muted); font-size: 11px; margin-top: 2px; }
.footer {
  margin-top: 56px; padding-top: 20px;
  border-top: 1px solid var(--border);
  font-size: 13px; color: var(--fg-muted);
  display: flex; gap: 18px; flex-wrap: wrap;
}
.footer a { color: var(--fg-muted); }
.footer a:hover { color: var(--accent); }
.note {
  background: var(--bg-subtle); border-left: 3px solid var(--accent);
  padding: 10px 14px; border-radius: 0 6px 6px 0;
  font-size: 14px; color: var(--fg-muted);
  margin: 12px 0;
}
"""

THEME_JS = r"""
<script>
(function(){
  var saved = localStorage.getItem('morkit-theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  function toggle(){
    var cur = document.documentElement.getAttribute('data-theme') || 'dark';
    var next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('morkit-theme', next);
  }
  document.addEventListener('DOMContentLoaded', function(){
    var btn = document.getElementById('themeBtn');
    if (btn) btn.addEventListener('click', toggle);
  });
})();
</script>
"""

AUTOGEN_HEADER = (
    "<!-- AUTOGENERATED by docs/_scaffolder/build.py. "
    "Edit docs/_scaffolder/content.py or templates.py, not this file. -->\n"
)


def page_shell(title, breadcrumb_html, body_html):
    return f"""<!doctype html>
<html lang="vi" data-theme="dark">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<main class="page">
  <div class="crumbs">
    {breadcrumb_html}
    <button id="themeBtn" class="toggle" type="button">☾ Vesper / Paper</button>
  </div>
  {body_html}
  <div class="footer">
    <a href="../index.html">← Về tổng quan</a>
    <a href="../docs.html">Use cases</a>
    <a href="https://github.com/mor-duongmh/claude-plugins" target="_blank" rel="noopener">GitHub</a>
  </div>
</main>
{THEME_JS}
</body>
</html>
"""


def detail_page(*, kind, slug, name, lede, details, group_label, deprecated,
                when_bullets, invocation, args, example_note, related_cards_html):
    """Render a skill or command detail page.

    `kind` controls section order:
      - skill   →  Nhiệm vụ · Khi nào dùng · Ví dụ · Xem thêm
      - command →  Cách gọi · Khi nào dùng · Ví dụ · Xem thêm
    """
    tag_html = ""
    if deprecated:
        tag_html += '<span class="tag deprecated">Đã thay thế</span>'
    tag_html += f'<span class="tag">{group_label}</span>'
    kind_label = "Skill" if kind == "skill" else "Command"
    tag_html += f'<span class="tag">{kind_label}</span>'

    when_html = "\n".join(f"  <li>{b}</li>" for b in when_bullets)

    cmd_args = f" {args}" if args else ""
    example_html = f"""<div class="window">
    <div class="window-bar">
      <span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
      <span class="window-title">claude-code · morkit</span>
    </div>
    <pre><code>$ {invocation}{cmd_args}</code></pre>
  </div>
  <p class="lede" style="font-size:14px;">{example_note}</p>"""

    if kind == "command":
        first_block = f"""<h2>1. Cách gọi</h2>
  <pre><code>{invocation} [tham số]</code></pre>
  <p class="lede" style="font-size:14px;">Gõ trực tiếp trong Claude Code.</p>
"""
    else:
        # Skill — show "Nhiệm vụ" as bullet list (more scannable than paragraph)
        if details:
            details_html = "\n".join(f"    <li>{b}</li>" for b in details)
            first_block = f"""<h2>1. Nhiệm vụ</h2>
  <ul class="duties">
{details_html}
  </ul>
"""
        else:
            first_block = ""

    when_idx = 2 if (kind == "command" or details) else 1
    example_idx = when_idx + 1
    related_idx = example_idx + 1

    body = f"""<div style="margin-bottom: 10px;">{tag_html}</div>
  <h1>{name}</h1>
  <p class="lede">{lede}</p>

  {first_block}
  <h2>{when_idx}. Khi nào dùng</h2>
  <ul>
{when_html}
  </ul>

  <h2>{example_idx}. Ví dụ</h2>
  {example_html}

  <h2>{related_idx}. Xem thêm</h2>
  <div class="related-grid">
{related_cards_html}
  </div>
"""

    kind_label_vn = "skill" if kind == "skill" else "command"
    crumbs_path = f'morkit › <a href="../index.html">tổng quan</a> › {kind_label_vn} › <span class="path">{slug}</span>'
    breadcrumb_html = f'<div>{crumbs_path}</div>'

    title = f"morkit › {kind_label_vn} › {slug}"
    return AUTOGEN_HEADER + page_shell(title, breadcrumb_html, body)


def related_card_html(href, title, sub):
    return f'<a class="related-card" href="{href}"><div class="ttl">{title}</div><div class="sub">{sub}</div></a>'


def overview_page(*, sections_html):
    """Render the top-level docs/index.html overview.

    `sections_html` is the full inner body (5 sections, ready-rendered).
    """
    breadcrumb_html = '<div>morkit › <span class="path">tổng quan</span></div>'
    body = f"""<h1>morkit</h1>
  <p class="lede">Plugin <code>morkit</code> của Mor — gói toàn bộ công cụ vào một chỗ:
  viết spec, lên kế hoạch và chạy, review code, sinh tài liệu.
  Tất cả gọi qua cùng một tiền tố <code>/morkit:*</code>.</p>

{sections_html}
"""
    # Override footer: from index we don't want a "← Tổng quan" link back to self.
    shell = f"""<!doctype html>
<html lang="vi" data-theme="dark">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>morkit — tổng quan</title>
<style>{CSS}</style>
</head>
<body>
<main class="page">
  <div class="crumbs">
    {breadcrumb_html}
    <button id="themeBtn" class="toggle" type="button">☾ Vesper / Paper</button>
  </div>
  {body}
  <div class="footer">
    <a href="docs.html">Use cases →</a>
    <a href="https://github.com/mor-duongmh/claude-plugins" target="_blank" rel="noopener">GitHub</a>
    <a href="https://github.com/mor-duongmh/claude-plugins/blob/main/README.md" target="_blank" rel="noopener">README</a>
  </div>
</main>
{THEME_JS}
</body>
</html>
"""
    return AUTOGEN_HEADER + shell
