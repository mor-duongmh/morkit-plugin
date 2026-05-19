"""Canonicalize markdown blocks for stable hashing.

Whitespace-trivial differences (CRLF vs LF, trailing spaces, blank-line collapsing)
should not trigger manual-edit detection. Semantic content changes should.

Public API:
    canonicalize(md_text) -> str         # Normalize for hashing
    compute_hash(md_text) -> str         # sha256 hex digest of canonical form
"""
from __future__ import annotations

import hashlib
import re

_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_TRAILING_WS = re.compile(r"[ \t]+$", re.MULTILINE)
_MULTI_BLANK = re.compile(r"\n{3,}")


def canonicalize(md_text: str) -> str:
    """Normalize markdown for hashing.

    Operations (order matters):
      1. Strip BOM if present.
      2. Normalize line endings: CRLF / CR -> LF.
      3. Strip HTML comments (treated as metadata, not content).
      4. Strip trailing whitespace per line.
      5. Collapse 3+ consecutive blank lines into 2 (keep paragraph breaks).
      6. Strip leading/trailing whitespace of entire block.

    Preserved: indentation inside code/table cells, list markers, table alignment.
    """
    if md_text.startswith("﻿"):
        md_text = md_text.lstrip("﻿")

    md_text = md_text.replace("\r\n", "\n").replace("\r", "\n")
    md_text = _HTML_COMMENT.sub("", md_text)
    md_text = _TRAILING_WS.sub("", md_text)
    md_text = _MULTI_BLANK.sub("\n\n", md_text)
    return md_text.strip()


def compute_hash(md_text: str) -> str:
    """Return sha256 hex digest of canonicalized text."""
    canonical = canonicalize(md_text)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
