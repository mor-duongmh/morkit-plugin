"""Sequential ID allocator for entity IDs (FR-NNN, SCREEN-NNN, etc.).

When a parser detects a new entity without an existing ID, this allocator
returns the next available 3-digit zero-padded ID for that prefix.

Public API:
    IdAllocator(existing_ids).next(prefix) -> str
    parse_id(id_str) -> (prefix, number) | None
"""
from __future__ import annotations

import re
from collections import defaultdict

_ID_PATTERN = re.compile(r"^([A-Z]+)-(\d+)$")


def parse_id(id_str: str) -> tuple[str, int] | None:
    """Parse 'FR-007' -> ('FR', 7). Returns None if not numeric format."""
    m = _ID_PATTERN.match(id_str)
    if not m:
        return None
    return m.group(1), int(m.group(2))


class IdAllocator:
    """Allocates next available ID per prefix.

    Tracks max number used per prefix (e.g. FR -> 12 means FR-012 was last).
    Next call to .next("FR") returns "FR-013".
    """

    def __init__(self, existing_ids: list[str] | None = None) -> None:
        self._max_by_prefix: dict[str, int] = defaultdict(int)
        if existing_ids:
            for sid in existing_ids:
                parsed = parse_id(sid)
                if parsed is None:
                    continue
                prefix, num = parsed
                if num > self._max_by_prefix[prefix]:
                    self._max_by_prefix[prefix] = num

    def next(self, prefix: str, pad: int = 3) -> str:
        """Allocate and return next ID for prefix. Bumps internal counter."""
        next_num = self._max_by_prefix[prefix] + 1
        self._max_by_prefix[prefix] = next_num
        return f"{prefix}-{next_num:0{pad}d}"

    def peek(self, prefix: str, pad: int = 3) -> str:
        """Return the next ID without bumping the counter."""
        next_num = self._max_by_prefix[prefix] + 1
        return f"{prefix}-{next_num:0{pad}d}"

    def reserve(self, id_str: str) -> None:
        """Mark an ID as used (e.g. when explicit ID provided in source)."""
        parsed = parse_id(id_str)
        if parsed is None:
            return
        prefix, num = parsed
        if num > self._max_by_prefix[prefix]:
            self._max_by_prefix[prefix] = num
