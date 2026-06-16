"""Tests for lib/markdown_ast.py."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib.markdown_ast import (  # noqa: E402
    extract_section_id,
    parse_doc,
    serialize_blocks,
    split_preamble_postamble,
)


# --- extract_section_id ---


def test_extract_fr_id():
    assert extract_section_id("### FR-001: User Login") == "FR-001"


def test_extract_screen_id_no_colon():
    assert extract_section_id("#### SCREEN-002 OAuth Callback") == "SCREEN-002"


def test_extract_endpoint_get():
    assert extract_section_id("### GET /users") == "ENDPOINT-GET-users"


def test_extract_endpoint_with_path_param():
    assert extract_section_id("### GET /users/{id}") == "ENDPOINT-GET-users-by-id"


def test_extract_endpoint_post_nested():
    sid = extract_section_id("#### POST /users/{id}/posts")
    assert sid is not None
    assert sid.startswith("ENDPOINT-POST-")


def test_extract_table_id():
    assert extract_section_id("### TBL-001: users") == "TBL-001"


def test_extract_no_id_returns_none():
    assert extract_section_id("### Just a regular heading") is None


def test_extract_strips_hash_marks():
    assert extract_section_id("##### FR-099") == "FR-099"


# --- parse_doc ---

SAMPLE_DOC = """# SRS Document

Some preamble.

## 3. Functional Requirements

### FR-001: Login
Description for FR-001.

Some text.

### FR-002: Logout
Description for FR-002.

#### Sub-section without ID

Should be part of FR-002 because no anchor.

## 4. NFR

### NFR-001: Performance
Response < 500ms.

## Appendix

Free text after last tracked section.
"""


def test_parse_doc_finds_all_anchored_sections():
    blocks = parse_doc(SAMPLE_DOC)
    assert set(blocks.keys()) == {"FR-001", "FR-002", "NFR-001"}


def test_parse_doc_block_includes_heading():
    blocks = parse_doc(SAMPLE_DOC)
    assert "FR-001: Login" in blocks["FR-001"].body_md


def test_parse_doc_block_extends_until_next_anchored_heading():
    blocks = parse_doc(SAMPLE_DOC)
    # FR-002 should include the sub-section without ID
    body = blocks["FR-002"].body_md
    assert "Sub-section without ID" in body
    # But should NOT include NFR-001
    assert "NFR-001" not in body


def test_parse_doc_heading_level():
    blocks = parse_doc(SAMPLE_DOC)
    assert blocks["FR-001"].heading_level == 3
    assert blocks["NFR-001"].heading_level == 3


def test_parse_doc_empty_returns_empty():
    assert parse_doc("") == {}


def test_parse_doc_no_anchors_returns_empty():
    assert parse_doc("# Title\n\nJust text, no IDs.") == {}


# --- serialize + round-trip ---


def test_round_trip_preserves_sections():
    blocks = parse_doc(SAMPLE_DOC)
    preamble, postamble = split_preamble_postamble(SAMPLE_DOC, blocks)
    section_order = ["FR-001", "FR-002", "NFR-001"]
    rebuilt = serialize_blocks(blocks, section_order, preamble, postamble)

    # Round-trip should preserve key content
    assert "FR-001: Login" in rebuilt
    assert "FR-002: Logout" in rebuilt
    assert "NFR-001: Performance" in rebuilt
    assert "Some preamble." in rebuilt
    assert "Free text after last tracked section." in rebuilt


def test_round_trip_byte_identical_via_block_concatenation():
    """If we concatenate preamble + all block bodies + postamble, should match input."""
    blocks = parse_doc(SAMPLE_DOC)
    preamble, postamble = split_preamble_postamble(SAMPLE_DOC, blocks)
    section_order = sorted(blocks.keys())  # FR-001, FR-002, NFR-001
    rebuilt = serialize_blocks(blocks, section_order, preamble, postamble)
    assert rebuilt == SAMPLE_DOC


def test_serialize_skips_unknown_section_ids_silently():
    blocks = parse_doc(SAMPLE_DOC)
    rebuilt = serialize_blocks(blocks, ["FR-001", "FR-DOES-NOT-EXIST", "FR-002"], "", "")
    assert "FR-001: Login" in rebuilt
    assert "FR-002: Logout" in rebuilt


def test_split_preamble_postamble_with_empty_blocks():
    pre, post = split_preamble_postamble("Just text.", {})
    assert pre == "Just text."
    assert post == ""
