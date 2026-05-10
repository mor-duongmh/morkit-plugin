"""Markdown AST wrapper using markdown-it-py.

Parses SRS / API / DB markdown into {section_id -> Block} keyed by anchor IDs
(FR-001, NFR-001, SCREEN-001, DATA-001, INT-001, TBL-001, IDX-001, REL-001,
ENDPOINT-XXX, ERR-XXX, UC-XXX, ENUM-XXX). Sections are bounded by
heading-with-ID start and the next same-or-higher-level heading-with-ID.

Public API:
    parse_doc(md_text) -> dict[str, Block]
    serialize_blocks(blocks, section_order) -> str
    extract_section_id(heading_text) -> str | None
    Block: dataclass

Round-trip property: text → parse_doc → serialize_blocks should be
byte-identical when section_order matches discovered order and each block's
body_md is preserved verbatim.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from markdown_it import MarkdownIt

# Section ID detection: heading containing FR-001 / SCREEN-001 / etc.
# Accepts patterns like:  "### FR-001: User Login"  or  "#### SCREEN-002 OAuth Callback"
_ID_PATTERN = re.compile(
    r"\b(FR|NFR|SCREEN|DATA|INT|TBL|IDX|REL|ENDPOINT|ERR|UC|ENUM|WEBHOOK)-([A-Z0-9_-]+)\b"
)
# Endpoint heading like "GET /users/{id}" -> ENDPOINT-GET-users-by-id
_ENDPOINT_PATTERN = re.compile(r"^\s*(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/\S+)")


@dataclass
class Block:
    """Represents one section in a markdown doc, anchored by stable ID."""

    id: str
    heading_level: int
    heading_text: str
    body_md: str = ""
    line_start: int = 0
    line_end: int = 0
    parent_section: str | None = None


def _slugify_path(path: str) -> str:
    """Convert API path to slug fragment.

    /users -> users
    /users/{id} -> users-by-id
    /users/{userId} -> users-by-userid
    /users/{id}/posts -> users-by-id-posts
    """
    parts: list[str] = []
    for seg in path.strip("/").split("/"):
        if not seg:
            continue
        if seg.startswith("{") and seg.endswith("}"):
            parts.append("by-" + seg[1:-1].lower())
        elif seg.startswith(":"):
            parts.append("by-" + seg[1:].lower())
        else:
            parts.append(seg.lower())
    return "-".join(p.replace("_", "-") for p in parts)


def extract_section_id(heading_text: str) -> str | None:
    """Extract canonical section ID from heading text.

    Examples:
      "### FR-001: User Login" -> "FR-001"
      "#### SCREEN-002 OAuth Callback" -> "SCREEN-002"
      "### POST /users" -> "ENDPOINT-POST-users"
      "### GET /users/{id}" -> "ENDPOINT-GET-users-by-id"
    """
    text = heading_text.strip().lstrip("#").strip()

    m = _ID_PATTERN.search(text)
    if m:
        prefix, suffix = m.group(1), m.group(2)
        return f"{prefix}-{suffix}"

    m2 = _ENDPOINT_PATTERN.match(text)
    if m2:
        method, path = m2.group(1), m2.group(2)
        return f"ENDPOINT-{method}-{_slugify_path(path)}"

    return None


def parse_doc(md_text: str) -> dict[str, Block]:
    """Parse markdown into {section_id -> Block}.

    Block boundaries: a section starts at a heading containing an ID anchor and
    extends until the next heading at the same or shallower level that also has
    an ID anchor (or end of doc).
    """
    md = MarkdownIt("commonmark", {"html": False})
    tokens = md.parse(md_text)
    lines = md_text.splitlines(keepends=True)

    # Collect heading positions: (token_idx, line, level, text, section_id)
    heading_positions: list[tuple[int, int, int, str, str | None]] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == "heading_open" and tok.map:
            level = int(tok.tag[1])  # h1 -> 1, h2 -> 2
            inline = tokens[i + 1]
            heading_text = inline.content if inline.type == "inline" else ""
            section_id = extract_section_id(heading_text)
            heading_positions.append((i, tok.map[0], level, heading_text, section_id))
        i += 1

    # Build blocks for headings that have an ID
    blocks: dict[str, Block] = {}
    for idx, (_tok_i, line_start, level, heading_text, section_id) in enumerate(heading_positions):
        if section_id is None:
            continue
        # Find next boundary: next heading with section_id at same-or-higher level
        line_end = len(lines)
        for next_line_start, next_level, _next_text, next_id in (
            (h[1], h[2], h[3], h[4]) for h in heading_positions[idx + 1 :]
        ):
            if next_id is not None and next_level <= level:
                line_end = next_line_start
                break
        body_md = "".join(lines[line_start:line_end])
        blocks[section_id] = Block(
            id=section_id,
            heading_level=level,
            heading_text=heading_text,
            body_md=body_md,
            line_start=line_start,
            line_end=line_end,
        )
    return blocks


def serialize_blocks(
    blocks: dict[str, Block], section_order: list[str], preamble: str = "", postamble: str = ""
) -> str:
    """Render blocks back to markdown.

    `section_order` defines order of section IDs. `preamble` is text before the
    first tracked section (e.g. doc title + meta table); `postamble` is text
    after the last (e.g. footer / appendices not tracked by ID).
    """
    parts: list[str] = []
    if preamble:
        parts.append(preamble if preamble.endswith("\n") else preamble + "\n")
    for sid in section_order:
        block = blocks.get(sid)
        if block is None:
            continue
        body = block.body_md
        if body and not body.endswith("\n"):
            body = body + "\n"
        parts.append(body)
    if postamble:
        parts.append(postamble)
    return "".join(parts)


def split_preamble_postamble(md_text: str, blocks: dict[str, Block]) -> tuple[str, str]:
    """Return (preamble, postamble) — text before first tracked block / after last.

    Helps preserve doc-level content (title, intro, appendices) when round-tripping.
    """
    if not blocks:
        return md_text, ""
    lines = md_text.splitlines(keepends=True)
    first_start = min(b.line_start for b in blocks.values())
    last_end = max(b.line_end for b in blocks.values())
    preamble = "".join(lines[:first_start])
    postamble = "".join(lines[last_end:])
    return preamble, postamble
