"""Move deprecated section blocks to Appendix Z.

Public API:
    move_to_appendix_z(blocks, section_order, section_id, marker, reason) -> tuple
"""
from __future__ import annotations

from datetime import date

from lib.markdown_ast import Block

APPENDIX_Z_HEADING = "## Appendix Z: Deprecated Items / 廃止項目"
APPENDIX_Z_INTRO = (
    "> Items moved here when marked DEPRECATE. Kept for traceability, not deleted."
)


def move_to_appendix_z(
    blocks: dict[str, Block],
    section_order: list[str],
    section_id: str,
    marker: str,
    reason: str,
) -> tuple[dict[str, Block], list[str]]:
    """Move section_id block from its current position into Appendix Z.

    Returns (updated_blocks, updated_section_order). Idempotent: if section_id
    already in Appendix Z (id starts with APPENDIX-Z-), no-op.
    """
    if section_id not in blocks:
        return blocks, section_order

    block = blocks[section_id]
    today = date.today().isoformat()

    # Wrap original heading text with marker
    original_heading = block.heading_text
    new_heading = f"{section_id} {marker}: {original_heading}"
    deprecation_note = (
        f"> **Reason:** {reason}\n"
        f"> **Deprecated at:** {today}\n"
        f"> **Original ID:** {section_id}\n\n---\n\n"
    )

    # Build deprecated block — heading downgraded to ### inside Appendix Z
    deprecated_body = (
        f"### {new_heading}\n\n"
        + deprecation_note
        + _strip_first_heading(block.body_md)
    )

    # New section ID inside Appendix Z (avoid collision if user re-adds same ID later)
    new_section_id = f"DEPRECATED-{section_id}"
    new_block = Block(
        id=new_section_id,
        heading_level=3,
        heading_text=new_heading,
        body_md=deprecated_body,
        line_start=0,
        line_end=0,
        parent_section="Appendix Z",
    )

    new_blocks = dict(blocks)
    del new_blocks[section_id]
    new_blocks[new_section_id] = new_block

    new_order = [sid for sid in section_order if sid != section_id]
    new_order.append(new_section_id)
    return new_blocks, new_order


def _strip_first_heading(md: str) -> str:
    """Drop the first heading line (we replaced it with new heading)."""
    lines = md.splitlines(keepends=True)
    out: list[str] = []
    skipped_first = False
    for line in lines:
        if not skipped_first and line.lstrip().startswith("#"):
            skipped_first = True
            continue
        out.append(line)
    return "".join(out).lstrip("\n")


def appendix_z_preamble() -> str:
    """Return the Appendix Z section header (rendered once if any deprecated items exist)."""
    return f"\n\n{APPENDIX_Z_HEADING}\n\n{APPENDIX_Z_INTRO}\n\n"
