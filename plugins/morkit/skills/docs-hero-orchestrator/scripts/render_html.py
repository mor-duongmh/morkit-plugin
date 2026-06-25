#!/usr/bin/env python3
"""Render a Markdown doc (e.g. docs/srs.md) into a branded, self-contained
`srs.html` using the shared Mor theme. Presentation only — never edits the
source Markdown.

CLI:
    render_html.py --input docs/srs.md --output docs/srs.html [--title "..."] [--lang VN]

Exit codes:
    0  success
    1  input missing / read error
    2  bad usage
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Resolve sibling lib (works both as script and when imported by tests).
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.html_theme import (  # noqa: E402
    Heading,
    build_nav,
    colorize_badges,
    slugify,
    wrap_document,
)

# Language code (pipeline) -> HTML lang attribute.
_LANG_MAP = {"VN": "vi", "EN": "en", "JP": "ja"}


def render_html(md_text: str, title: str | None = None, lang: str = "vi") -> str:
    """Convert Markdown text to the full branded HTML document string."""
    from markdown_it import MarkdownIt

    # commonmark base + GFM tables (render_srs emits pipe tables heavily).
    md = MarkdownIt("commonmark", {"html": True}).enable("table")
    tokens = md.parse(md_text)

    headings: list[Heading] = []
    first_h1: str | None = None
    for i, tok in enumerate(tokens):
        if tok.type != "heading_open":
            continue
        level = int(tok.tag[1:])
        inline = tokens[i + 1] if i + 1 < len(tokens) else None
        text = (inline.content if inline else "").strip()
        slug = slugify(text)
        tok.attrSet("id", slug)
        headings.append(Heading(level, text, slug))
        if level == 1 and first_h1 is None:
            first_h1 = text

    body_html = md.renderer.render(tokens, md.options, {})
    body_html = colorize_badges(body_html)
    nav_html = build_nav(headings)

    doc_title = title or first_h1 or "Document"
    return wrap_document(doc_title, body_html, nav_html, lang=lang)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--input", required=True, help="Source Markdown file")
    p.add_argument("--output", required=True, help="Destination HTML file")
    p.add_argument("--title", default=None, help="Document title (default: first H1)")
    p.add_argument("--lang", default="VN", choices=["JP", "EN", "VN", "vi", "en", "ja"],
                   help="Language code (pipeline JP/EN/VN or html code)")
    args = p.parse_args(argv)

    src = Path(args.input)
    if not src.is_file():
        sys.stderr.write(f"✗ Input not found: {src}\n")
        return 1
    try:
        md_text = src.read_text(encoding="utf-8")
    except OSError as exc:
        sys.stderr.write(f"✗ Cannot read {src}: {exc}\n")
        return 1

    lang = _LANG_MAP.get(args.lang, args.lang)
    html = render_html(md_text, title=args.title, lang=lang)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    sys.stdout.write(f"✓ Wrote {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
