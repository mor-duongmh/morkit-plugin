"""Shared Mor HTML theme — wraps rendered Markdown into a branded, self-contained
SRS document with sidebar navigation, scrollspy, and severity color-coding.

Brand tokens are sourced from the Mor slide template (cover): blue #016DD0,
navy #0E1A4B, gold #F5AE18. Presentation only — never alters doc content.

Public API:
    slugify(text) -> str
    Heading(level, text, slug)                 # namedtuple
    build_nav(headings) -> str                 # <nav> from H2 entries
    colorize_badges(html) -> str               # cell-scoped status/priority badges
    wrap_document(title, body_html, nav_html, lang="vi") -> str
"""
from __future__ import annotations

import base64
import re
import unicodedata
from collections import namedtuple
from pathlib import Path

Heading = namedtuple("Heading", "level text slug")

# Bundled Mor logo (scripts/assets/). Embedded as a data URI so srs.html stays
# self-contained. Swap the asset file to rebrand — no code change needed.
_ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
_LOGO_FILE = _ASSET_DIR / "mor-logo.webp"
_LOGO_MIME = "image/webp"


def _logo_data_uri() -> str | None:
    """Base64 data URI for the bundled logo, or None if the asset is missing."""
    try:
        raw = _LOGO_FILE.read_bytes()
    except OSError:
        return None
    return f"data:{_LOGO_MIME};base64," + base64.b64encode(raw).decode("ascii")

# --------------------------------------------------------------------------- #
# Slugify
# --------------------------------------------------------------------------- #


def slugify(text: str) -> str:
    """Stable, ASCII-folded slug. Used for BOTH heading ids and nav hrefs so they
    always agree. Vietnamese diacritics are folded (Tổng → tong)."""
    # Fold diacritics: NFKD then drop combining marks; map đ/Đ explicitly.
    text = text.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return ascii_text or "section"


# --------------------------------------------------------------------------- #
# Navigation
# --------------------------------------------------------------------------- #

_LEADING_NUM = re.compile(r"^\s*([0-9]+|[A-Z])[.):]?\s+")


def _nav_number(text: str) -> str:
    """Extract a leading section number/letter for the chip (e.g. '7. Foo' -> '7',
    'Appendix A: ...' -> 'A'). Falls back to a bullet."""
    m = _LEADING_NUM.match(text)
    if m:
        return m.group(1)
    m2 = re.search(r"\bAppendix\s+([A-Z])\b", text)
    if m2:
        return m2.group(1)
    return "•"


def build_nav(headings) -> str:
    """Build the sidebar nav from H2 headings only, preserving order."""
    items = []
    for h in headings:
        if h.level != 2:
            continue
        num = _nav_number(h.text)
        label = _LEADING_NUM.sub("", h.text).strip() or h.text
        items.append(
            f'<a href="#{h.slug}"><span class="num">{num}</span> {label}</a>'
        )
    return '<nav class="nav" id="nav">\n' + "\n".join(items) + "\n</nav>"


# --------------------------------------------------------------------------- #
# Severity / status badges (cell-scoped — never touches prose)
# --------------------------------------------------------------------------- #

# emoji impl-status strings emitted by render_srs.py -> badge class
_STATUS_BADGES = {
    "⬜ Not Started": "neutral",
    "🟡 In Progress": "med",
    "🟢 Done": "ok",
    "🔵 Verified": "info",
    "🔴 Blocked": "danger",
}
# whole-cell priority / severity words -> badge class
_WORD_BADGES = {
    "MUST": "must", "HIGH": "high",
    "SHOULD": "should", "MEDIUM": "med", "MED": "med",
    "COULD": "could", "LOW": "low",
    "WON'T": "neutral", "WONT": "neutral",
    "PASS": "ok", "FAIL": "danger", "OPEN": "med", "CLOSED": "ok",
}

_TD_RE = re.compile(r"<td>(.*?)</td>", re.DOTALL)


def _badge(text: str, cls: str) -> str:
    return f'<span class="badge {cls}">{text}</span>'


def colorize_badges(html: str) -> str:
    """Wrap recognised status/priority tokens that occupy a WHOLE table cell with a
    coloured badge span. Prose is left untouched."""

    def repl(m: "re.Match[str]") -> str:
        inner = m.group(1)
        key = inner.strip()
        if key in _STATUS_BADGES:
            return f"<td>{_badge(key, _STATUS_BADGES[key])}</td>"
        if key.upper() in _WORD_BADGES:
            return f"<td>{_badge(key, _WORD_BADGES[key.upper()])}</td>"
        return m.group(0)

    return _TD_RE.sub(repl, html)


# --------------------------------------------------------------------------- #
# Theme CSS / JS (self-contained)
# --------------------------------------------------------------------------- #

THEME_CSS = """
:root{
  --mor-blue:#016DD0; --mor-navy:#0E1A4B; --mor-gold:#F5AE18;
  --blue-50:#E8F1FC; --blue-100:#CFE2FA; --blue-200:#9CC4F2; --blue-700:#0A437D;
  --gold-50:#FEF6E0; --gold-100:#FCE9B4;
  --ink:#16202E; --muted:#5B6B82; --faint:#8696AB;
  --line:#DCE4EE; --bg:#FFFFFF; --soft:#F4F8FD;
  --ok:#2E9E5B; --ok-soft:#E6F4EC; --warn:#C2850A; --warn-soft:#FEF6E0;
  --danger:#D64545; --danger-soft:#FBE9E9; --info:#016DD0; --info-soft:#E8F1FC;
  --neutral:#5B6B82; --neutral-soft:#EEF2F7;
  --sidebar-w:300px;
  --font:'Be Vietnam Pro','Hiragino Sans','Noto Sans JP','Segoe UI',system-ui,-apple-system,sans-serif;
  --mono:'JetBrains Mono','SF Mono',Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:var(--font);color:var(--ink);background:var(--soft);font-size:15px;line-height:1.7;-webkit-font-smoothing:antialiased}
#progress{position:fixed;top:0;left:0;height:3px;width:0;z-index:60;background:linear-gradient(90deg,var(--mor-blue),var(--mor-gold));transition:width .1s linear}
.shell{display:flex;min-height:100vh}
.sidebar{position:sticky;top:0;align-self:flex-start;width:var(--sidebar-w);height:100vh;background:linear-gradient(180deg,var(--mor-navy),#0A1438);color:#cdd7ea;display:flex;flex-direction:column;flex:0 0 var(--sidebar-w);z-index:40}
.brand{padding:18px 20px 14px;border-bottom:1px solid rgba(255,255,255,.08);display:flex;align-items:center;gap:11px}
.brand .logo{width:36px;height:36px;border-radius:9px;flex:0 0 36px;background:linear-gradient(135deg,var(--mor-blue),#2580DD);display:grid;place-items:center;font-weight:800;color:#fff;font-size:13px;box-shadow:0 4px 12px rgba(1,109,208,.4)}
.brand .bt{font-weight:700;color:#fff;font-size:14.5px;line-height:1.2}
.brand .bs{font-size:11px;color:#7f8fb0;letter-spacing:.3px}
.brand.brand-stacked{flex-direction:column;align-items:flex-start;gap:9px;padding:20px 20px 15px}
.brand-logo{max-width:185px;max-height:40px;height:auto;display:block;filter:brightness(0) invert(1);opacity:.96}
.brand-stacked .bt{font-size:12.5px;color:#9fb0cf;font-weight:500;text-align:left;letter-spacing:.2px}
.search{padding:12px 16px 6px}
.search input{width:100%;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);color:#fff;border-radius:8px;padding:8px 11px;font-size:13px;font-family:inherit;outline:none}
.search input::placeholder{color:#7f8fb0}
.search input:focus{border-color:var(--mor-blue);background:rgba(1,109,208,.14)}
.nav{flex:1;overflow-y:auto;padding:6px 10px 24px}
.nav::-webkit-scrollbar{width:8px}.nav::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:8px}
.nav a{display:flex;align-items:center;gap:10px;text-decoration:none;color:#aebbd4;padding:7px 12px;border-radius:8px;font-size:13.5px;position:relative;transition:background .12s,color .12s}
.nav a .num{font-size:11px;font-weight:600;min-width:20px;color:#6f80a4;font-family:var(--mono)}
.nav a:hover{background:rgba(255,255,255,.06);color:#fff}
.nav a.active{background:rgba(1,109,208,.18);color:#fff;font-weight:600}
.nav a.active .num{color:var(--mor-gold)}
.nav a.active::before{content:"";position:absolute;left:0;top:7px;bottom:7px;width:3px;border-radius:0 3px 3px 0;background:var(--mor-gold)}
.nav a.hidden{display:none}
.main{flex:1;min-width:0;display:flex;flex-direction:column}
.topbar{position:sticky;top:0;z-index:30;background:rgba(255,255,255,.85);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);padding:11px 34px;display:flex;align-items:center;gap:12px;font-size:13px;color:var(--muted)}
.topbar .crumb b{color:var(--ink)}
.content{max-width:920px;width:100%;margin:0 auto;padding:30px 40px 90px}
.content h1{font-size:28px;color:var(--mor-navy);border-bottom:3px solid var(--mor-blue);padding-bottom:14px;margin:0 0 6px}
.content h2{font-size:21px;color:var(--mor-navy);border-bottom:2px solid var(--line);padding-bottom:6px;margin-top:38px;scroll-margin-top:64px}
.content h3{font-size:16.5px;color:var(--blue-700);margin-top:24px;scroll-margin-top:64px}
.content h4{font-size:14.5px;color:#34465e}
.content a{color:var(--mor-blue);text-decoration:none}
.content a:hover{text-decoration:underline}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:13px}
th,td{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:var(--mor-navy);color:#fff;font-weight:600}
tr:nth-child(even) td{background:var(--soft)}
tr:hover td{background:var(--blue-50)}
code{background:var(--blue-50);color:var(--blue-700);padding:1px 5px;border-radius:4px;font-family:var(--mono);font-size:12.5px}
pre{background:var(--mor-navy);color:#dbe6f3;padding:14px 16px;border-radius:8px;overflow:auto;font-size:12.5px}
pre code{background:none;color:inherit;padding:0}
blockquote{border-left:4px solid var(--mor-gold);background:var(--gold-50);margin:14px 0;padding:10px 16px;color:#6b561f;border-radius:0 6px 6px 0}
hr{border:0;border-top:1px solid var(--line);margin:28px 0}
.badge{display:inline-flex;align-items:center;gap:5px;border-radius:20px;padding:2px 11px;font-size:11.5px;font-weight:600;white-space:nowrap}
.badge.must,.badge.high,.badge.danger{background:var(--danger-soft);color:var(--danger)}
.badge.should,.badge.med{background:var(--warn-soft);color:var(--warn)}
.badge.could,.badge.low,.badge.ok{background:var(--ok-soft);color:var(--ok)}
.badge.info{background:var(--info-soft);color:var(--blue-700)}
.badge.neutral{background:var(--neutral-soft);color:var(--neutral)}
#totop{position:fixed;right:26px;bottom:26px;width:44px;height:44px;border-radius:50%;border:none;background:var(--mor-blue);color:#fff;font-size:18px;cursor:pointer;box-shadow:0 8px 22px rgba(1,109,208,.4);opacity:0;pointer-events:none;transition:opacity .2s,transform .2s;z-index:50}
#totop.show{opacity:1;pointer-events:auto}
#totop:hover{transform:translateY(-3px)}
@media (max-width:860px){.sidebar{display:none}.content{padding:20px}}
@media print{
  #progress,.sidebar,.topbar,#totop{display:none !important}
  body{background:#fff;font-size:11.5px}
  .content{max-width:none;padding:0}
  th{background:var(--mor-navy) !important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  tr:nth-child(even) td{background:#f0f4f9 !important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  table,pre,blockquote{page-break-inside:avoid}
  h2,h3,h4{page-break-after:avoid}
  @page{margin:16mm 14mm}
}
"""

THEME_JS = """
(function(){
  var prog=document.getElementById('progress');
  var totop=document.getElementById('totop');
  function onScroll(){
    var h=document.documentElement;
    var max=h.scrollHeight-h.clientHeight;
    if(prog) prog.style.width=(max>0?(h.scrollTop/max*100):0)+'%';
    if(totop) totop.classList.toggle('show',h.scrollTop>400);
  }
  addEventListener('scroll',onScroll); onScroll();
  if(totop) totop.onclick=function(){scrollTo({top:0,behavior:'smooth'});};

  var links=[].slice.call(document.querySelectorAll('.nav a'));
  var map={};
  links.forEach(function(a){var id=a.getAttribute('href').slice(1);var el=document.getElementById(id);if(el)map[id]=a;});
  var crumb=document.getElementById('crumb');
  if(window.IntersectionObserver){
    var obs=new IntersectionObserver(function(es){
      es.forEach(function(e){
        if(e.isIntersecting){
          var a=map[e.target.id]; if(!a) return;
          links.forEach(function(l){l.classList.remove('active');});
          a.classList.add('active');
          if(crumb) crumb.textContent=a.textContent.trim();
        }
      });
    },{rootMargin:'-50px 0px -70% 0px'});
    Object.keys(map).forEach(function(id){obs.observe(document.getElementById(id));});
  }
  var sb=document.getElementById('navsearch');
  if(sb) sb.addEventListener('input',function(e){
    var q=e.target.value.trim().toLowerCase();
    links.forEach(function(a){a.classList.toggle('hidden', q && a.textContent.toLowerCase().indexOf(q)<0);});
  });
})();
"""

_FONT_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800'
    "&family=JetBrains+Mono:wght@400;500&display=swap\" rel=\"stylesheet\">"
)


def _esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _brand_block(title: str) -> str:
    """Sidebar brand: bundled logo on a light panel when available, else text mark."""
    uri = _logo_data_uri()
    if uri:
        return (
            '<div class="brand brand-stacked">'
            f'<img class="brand-logo" src="{uri}" alt="Mor Software">'
            f'<div class="bt">{_esc(title)}</div></div>'
        )
    return (
        '<div class="brand"><div class="logo">Mor</div>'
        f'<div><div class="bt">{_esc(title)}</div><div class="bs">Mor Software</div></div></div>'
    )


def wrap_document(title: str, body_html: str, nav_html: str, lang: str = "vi") -> str:
    """Assemble the full, self-contained HTML document."""
    return f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{_esc(title)}</title>
{_FONT_LINK}
<style>{THEME_CSS}</style></head>
<body>
<div id="progress"></div>
<div class="shell">
  <aside class="sidebar">
    {_brand_block(title)}
    <div class="search"><input id="navsearch" placeholder="🔎  Lọc mục / nhảy tới phần…"></div>
    {nav_html}
  </aside>
  <div class="main">
    <div class="topbar"><span class="crumb">📄 <b id="crumb">{_esc(title)}</b></span></div>
    <div class="content">
{body_html}
    </div>
  </div>
</div>
<button id="totop" title="Lên đầu">⬆</button>
<script>{THEME_JS}</script>
</body></html>
"""
