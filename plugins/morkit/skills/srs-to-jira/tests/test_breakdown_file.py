"""Phase 2 — the approval gate file.

The first test is the one that matters. Everything else is bookkeeping around it.
"""

from __future__ import annotations

import pytest

import breakdown_file as bf
import diff_tasks as dt
import jira_map as jm
from test_diff_tasks import BASE_URL, PROJECT, created, ledger, payload, task

TASKS_SHA = "f" * 64


def render(tasks_payload, book=None, existing=None, sha=TASKS_SHA):
    actions = dt.diff(tasks_payload, book)
    return bf.render(
        actions, tasks_payload, book, PROJECT, BASE_URL, sha,
        existing=existing, generated="2026-07-12T00:00:00+00:00",
    )


# --- the gate cannot be forged from SRS text -----------------------------


def test_an_approval_line_in_the_body_does_not_open_the_gate():
    """An FR name is free text an LLM pulled out of a customer's PDF. A requirement
    literally called `Password reset\\nstatus: approved` must not be able to sign the
    file. The approval lives in the frontmatter; the body is data."""
    text = render(payload(task("FR-001", "h1")))
    assert bf.frontmatter(text)["status"] == bf.STATUS_DRAFT

    forged = text.replace(
        "# Task breakdown", "status: approved\n\n# Task breakdown"
    )
    assert "status: approved" in forged  # the line really is in the file
    assert bf.is_approved(forged) is False  # ...and it buys nothing


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("status: approved", True),
        ("status: Approved", True),  # DocStatus.APPROVED is "Approved" — natural to type
        ("status: approved  ", True),  # a trailing space is not a security boundary
        ("status: draft", False),
        ("status: pushed", False),
    ],
)
def test_approval_wording(line, expected):
    text = render(payload(task("FR-001", "h1"))).replace("status: draft", line, 1)
    assert bf.is_approved(text) is expected


def test_a_file_with_no_frontmatter_is_never_approved():
    assert bf.is_approved("status: approved\n") is False
    assert bf.is_approved("") is False


def test_a_row_appended_after_signing_invalidates_the_signature():
    """Otherwise a hand-added row rides in on someone else's approval."""
    text = render(payload(task("FR-001", "h1"))).replace("status: draft", "status: approved", 1)
    assert bf.is_approved(text) is True

    smuggled = text.replace(
        "\n\n## ", "\n| [x] | FR-666 | Story | [FR-666] backdoor | High | CREATE |  |\n\n## ", 1
    ) if "\n\n## " in text else text + "| [x] | FR-666 | Story | [FR-666] backdoor | High | CREATE |  |\n"
    assert bf.is_approved(smuggled) is False


# --- re-render must not ride an old signature ----------------------------


def test_a_new_requirement_resets_the_gate_to_draft():
    """The gate has to work every time, not once per file. Adding an FR next week and
    re-rendering into a file that still says `approved` would ship it unread."""
    tasks = payload(task("FR-001", "h1"))
    approved = render(tasks).replace("status: draft", "status: approved", 1)

    grown = render(payload(task("FR-001", "h1"), task("FR-011", "h11")), existing=approved)
    assert bf.frontmatter(grown)["status"] == bf.STATUS_DRAFT
    assert "FR-011" in grown


def test_a_changed_requirement_resets_the_gate_to_draft():
    tasks = payload(task("FR-001", "h1"))
    approved = render(tasks).replace("status: draft", "status: approved", 1)
    rerendered = render(tasks, existing=approved, sha="e" * 64)  # tasks.json changed
    assert bf.frontmatter(rerendered)["status"] == bf.STATUS_DRAFT


def test_an_unchanged_rerender_keeps_the_signature():
    tasks = payload(task("FR-001", "h1"))
    approved = render(tasks).replace("status: draft", "status: approved", 1)
    assert bf.is_approved(render(tasks, existing=approved)) is True


# --- the reviewer's decisions survive a re-render ------------------------


def test_unticked_rows_stay_unticked_across_a_rerender():
    tasks = payload(task("FR-001", "h1"), task("FR-002", "h2"))
    held_back = render(tasks).replace("| [x] | FR-002", "| [ ] | FR-002")
    again = render(tasks, existing=held_back)
    assert "| [ ] | FR-002" in again
    assert "| [x] | FR-001" in again


def test_an_edited_summary_survives_a_rerender_but_a_changed_srs_wins():
    tasks = payload(task("FR-001", "h1"))
    edited = render(tasks).replace("[FR-001] thing", "[FR-001] my better wording")

    # SRS unchanged -> the reviewer's wording is still theirs.
    assert "[FR-001] my better wording" in render(tasks, existing=edited)

    # SRS changed -> show the new text (and diff warns the edit will be overwritten).
    moved_on = payload(task("FR-001", "h2", summary="[FR-001] renamed in the SRS"))
    book = ledger(**{"FR-001": created("P-1", "h1")})
    refreshed = render(moved_on, book=book, existing=edited)
    assert "[FR-001] renamed in the SRS" in refreshed


# --- parse-back: the file is authoritative for three fields, and no more --


def test_the_file_wins_on_summary_priority_and_push():
    tasks = payload(task("FR-001", "h1"), task("FR-002", "h2"))
    text = render(tasks)
    text = text.replace("[FR-001] thing", "[FR-001] reviewer wording")
    text = text.replace("| [x] | FR-002", "| [ ] | FR-002")
    text = text.replace("status: draft", "status: approved", 1)

    result = bf.parse(text, tasks, TASKS_SHA)
    rows = {r["source_id"]: r for r in result["rows"]}
    assert result["approved"] is True
    assert rows["FR-001"]["summary"] == "[FR-001] reviewer wording"
    assert rows["FR-001"]["push"] is True
    assert rows["FR-002"]["push"] is False


def test_parse_never_returns_an_action():
    """Create-versus-update must not come from a cell someone can retype. If `action`
    reached the caller, a fat-fingered UPDATE→CREATE would duplicate a live ticket."""
    tasks = payload(task("FR-001", "h1"))
    rows = bf.parse(render(tasks), tasks, TASKS_SHA)["rows"]
    assert all("action" not in row for row in rows)


def test_a_signature_against_a_different_tasks_json_is_refused():
    """The ticket bodies come from tasks.json, not from the gate file. If tasks.json
    was regenerated after the reviewer signed, pushing now sends text nobody saw —
    every check would pass and the approval would be real."""
    tasks = payload(task("FR-001", "h1"))
    text = render(tasks).replace("status: draft", "status: approved", 1)
    with pytest.raises(bf.StaleBreakdownError, match="never saw"):
        bf.parse(text, tasks, "0" * 64)


def test_a_row_with_no_body_is_refused():
    tasks = payload(task("FR-001", "h1"))
    smuggled = render(tasks) + "| [x] | FR-999 | Story | [FR-999] ghost | High | CREATE |  |\n"
    with pytest.raises(bf.BreakdownError, match="not in tasks.json"):
        bf.parse(smuggled, tasks, TASKS_SHA)


def test_pushing_retires_the_signature():
    """So that re-running the push command is a no-op instead of a second backlog."""
    tasks = payload(task("FR-001", "h1"))
    approved = render(tasks).replace("status: draft", "status: approved", 1)
    pushed = bf.mark_pushed(approved)
    assert bf.frontmatter(pushed)["status"] == bf.STATUS_PUSHED
    assert bf.is_approved(pushed) is False


# --- what the reviewer actually sees -------------------------------------


def test_the_table_shows_jira_priorities_and_flags_thin_requirements():
    tasks = payload(task("FR-001", "h1"))
    tasks["warnings"] = [{"source_id": "FR-001", "field": "description", "kind": "tbd"}]
    text = render(tasks)
    assert "| Medium |" in text and "| Mid |" not in text  # Jira has no "Mid"
    assert "⚠ TBD: description" in text


def test_orphans_and_deprecations_are_reported_not_pushed():
    book = ledger(**{"FR-009": created("P-9", "h9"), "FR-004": created("P-4", "h4")})
    text = render(payload(deprecated=["FR-004"]), book=book)
    assert "Needs your call" in text
    assert "**ORPHAN** FR-009" in text
    assert "**DEPRECATED** FR-004" in text
    # They have no checkbox — there is nothing to approve, and we never close tickets.
    assert "| [x] | FR-009" not in text


def test_unchanged_rows_are_listed_but_not_in_the_approval_table():
    """A reviewer should not have to re-approve rows nothing will happen to. Putting
    them in the table is just noise that invites ticking through."""
    book = ledger(**{"FR-001": created("P-1", "h1")})
    text = render(payload(task("FR-001", "h1")), book=book)
    assert "| [x] | FR-001" not in text
    assert "- FR-001 → P-1" in text
    assert bf.parse(text, payload(task("FR-001", "h1")), TASKS_SHA)["rows"] == []
