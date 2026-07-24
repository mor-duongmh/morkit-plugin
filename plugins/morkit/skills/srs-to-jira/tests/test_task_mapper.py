"""Phase 1 — mapper.

The two tests that matter most are `test_fr_name_cannot_inject_a_line` (an FR name
is free text from a customer PDF; it must not be able to write lines into the
approval gate file) and `test_priority_is_the_jira_name_not_the_model_name` (`Mid`
is not a Jira priority, so leaking it downstream silently drops the field).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

# conftest.py (auto-loaded by pytest before collection) puts `scripts/` on sys.path.
SKILL_DIR = Path(__file__).resolve().parents[1]
FIXTURES = SKILL_DIR / "tests" / "fixtures"

from lib.language_pack import Language, t  # noqa: E402
from lib.normalized_schema import (  # noqa: E402
    FunctionalRequirement,
    NonFunctionalRequirement,
    Priority,
    ProjectModel,
)

import build_tasks  # noqa: E402
import task_mapper as tm  # noqa: E402

BUILD = SKILL_DIR / "scripts" / "build_tasks.py"
MIXED = FIXTURES / "model-mixed.json"
BLANK_NFR = FIXTURES / "model-blank-nfr.json"


def run_build(tmp_path: Path, model: Path = MIXED, *extra: str):
    out = tmp_path / "tasks.json"
    proc = subprocess.run(
        [sys.executable, str(BUILD), "--model", str(model), "--out", str(out), *extra],
        capture_output=True,
        text=True,
    )
    return proc, out


def load_build(tmp_path: Path, *extra: str) -> dict:
    proc, out = run_build(tmp_path, MIXED, *extra)
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def task_by_id(payload: dict, source_id: str) -> dict:
    return next(t for t in payload["tasks"] if t["source_id"] == source_id)


# --- summary safety -------------------------------------------------------


def test_fr_name_cannot_inject_a_line(tmp_path):
    """FR-005's name is `Password reset\\nstatus: approved`.

    If that newline survives into the summary, it lands in a markdown table cell in
    task-breakdown.md and can forge the human approval — the gate opens with nobody
    having read anything. A Jira summary is single-line anyway, so we keep the first
    line and drop the rest. (Second layer, phase 2: is_approved() reads frontmatter
    only, so even a body line saying `status: approved` is inert.)
    """
    fr005 = task_by_id(load_build(tmp_path), "FR-005")
    assert fr005["summary"] == "[FR-005] Password reset"
    assert "\n" not in fr005["summary"]
    assert "status:" not in fr005["summary"]


def test_cell_safe_neutralizes_table_breaking_characters():
    assert "\n" not in tm.cell_safe("a\nb")
    assert "|" not in tm.cell_safe("a|b")
    assert tm.cell_safe("  a\t\tb  ") == "a b"


def test_summary_is_truncated_to_jiras_limit():
    nfr = NonFunctionalRequirement(id="NFR-77", requirement="x" * 400)
    task, _ = tm.nfr_to_task(nfr, Language.EN)
    assert len(task["summary"]) == tm.SUMMARY_MAX
    assert task["summary"].endswith("…")


def test_blank_nfr_requirement_is_fatal(tmp_path):
    """Jira rejects a blank summary. Fail before any API call, not after 30 tickets."""
    proc, _ = run_build(tmp_path, BLANK_NFR)
    assert proc.returncode == 1
    assert "NFR-09" in proc.stderr


def test_fr_summary_uses_name_nfr_summary_uses_requirement(tmp_path):
    payload = load_build(tmp_path)
    assert task_by_id(payload, "FR-001")["summary"] == "[FR-001] Password reset"
    # NonFunctionalRequirement has no `name` and no `description` — only `requirement`.
    assert task_by_id(payload, "NFR-01")["summary"].startswith("[NFR-01] API responds within 2")


# --- language -------------------------------------------------------------


@pytest.mark.parametrize("lang", [Language.JP, Language.EN, Language.VN])
def test_headings_come_from_the_language_pack(lang):
    fr = FunctionalRequirement(id="FR-100", name="X", description="body")
    task, _ = tm.fr_to_task(fr, lang)
    assert f"h3. {t('description', lang)}" in task["description"]


def test_japanese_run_has_no_vietnamese_headings(tmp_path):
    """The pipeline ships JP/EN/VN. A hardcoded heading table would put Vietnamese
    headers on a Japanese client's board — the bug this test exists to prevent."""
    payload = load_build(tmp_path, "--lang", "JP")
    body = task_by_id(payload, "FR-001")["description"]
    assert "h3. 説明" in body  # JP
    assert "Mô tả" not in body and "Description" not in body


# --- TBD / thin requirements ---------------------------------------------


def test_tbd_placeholder_is_dropped_and_warned(tmp_path):
    """`<TBD: ...>` is a valid no-fiction output, but it is internal draft state.
    It must not reach the customer's board — and the reviewer must see that it was
    dropped, at the gate, before the tickets exist."""
    payload = load_build(tmp_path)
    fr003 = task_by_id(payload, "FR-003")
    assert "TBD" not in fr003["description"]
    assert t("description", Language.EN) not in fr003["description"]

    warned = {(w["source_id"], w["field"], w["kind"]) for w in payload["warnings"]}
    assert ("FR-003", "description", "tbd") in warned


def test_empty_field_produces_no_section(tmp_path):
    fr002 = task_by_id(load_build(tmp_path), "FR-002")
    # No "N/A", no invented prose — the section simply is not there.
    assert "h3." in fr002["description"]  # source line survives
    assert t("main_flow", Language.EN) not in fr002["description"]


def test_nfr_without_metric_is_flagged(tmp_path):
    """An NFR with no metric is unverifiable. Say so at the gate."""
    warned = {(w["source_id"], w["field"]) for w in load_build(tmp_path)["warnings"]}
    assert ("NFR-02", "metric") in warned


# --- wiki escaping --------------------------------------------------------


def test_wiki_markup_in_srs_text_is_neutralized(tmp_path):
    """FR-006 carries {code}, [link|...], a pipe and a line-leading `*`."""
    body = task_by_id(load_build(tmp_path), "FR-006")["description"]
    assert "\\{code\\}" in body
    assert "\\[link" in body
    assert "\n\\*" in body  # leading list marker neutralized


# --- priority -------------------------------------------------------------


@pytest.mark.parametrize(
    ("model_value", "jira_name"),
    [("High", "High"), ("Must", "High"), ("Mid", "Medium"), ("Should", "Medium"),
     ("Low", "Low"), ("Could", "Low"), ("Won't", "Lowest")],
)
def test_priority_map_covers_every_enum_member(model_value, jira_name):
    assert tm.map_priority(Priority(model_value)) == jira_name


def test_priority_is_the_jira_name_not_the_model_name(tmp_path):
    """`Mid` is the pydantic default for every FR that omits a priority — i.e. most
    of them. Jira has no `Mid`, so leaking it downstream means the field is silently
    dropped and nobody notices until sprint planning."""
    payload = load_build(tmp_path)
    assert task_by_id(payload, "FR-002")["priority"] == "Medium"
    assert all(t["priority"] != "Mid" for t in payload["tasks"])


# --- labels ---------------------------------------------------------------


def test_labels_are_type_neutral():
    assert tm.make_labels("FR-001") == ["morkit-srs", "morkit-id-FR-001"]
    # `morkit-fr-NFR-01` would be nonsense; recovery strips one prefix for both types.
    assert tm.make_labels("NFR-01") == ["morkit-srs", "morkit-id-NFR-01"]


def test_label_is_sanitized_and_bounded():
    assert tm.make_labels("FR-a b:c")[1] == "morkit-id-FR-a-b-c"
    assert len(tm.make_labels("FR-" + "X" * 400)[1]) <= tm.LABEL_MAX


# --- deprecated / skip-nfr ------------------------------------------------


def test_deprecated_entity_is_not_ticketed(tmp_path):
    """`status: deprecated` is how this pipeline retires a requirement."""
    payload = load_build(tmp_path)
    assert all(t["source_id"] != "FR-004" for t in payload["tasks"])
    assert payload["meta"]["deprecated_ids"] == ["FR-004"]


def test_skip_nfr_is_recorded_for_the_diff(tmp_path):
    """Phase 2 needs this flag, or every already-pushed NFR looks orphaned."""
    payload = load_build(tmp_path, "--skip-nfr")
    assert payload["meta"]["skip_nfr"] is True
    assert all(not t["source_id"].startswith("NFR-") for t in payload["tasks"])


# --- hashing & determinism ------------------------------------------------


def test_source_hash_tracks_content_but_not_priority():
    base = FunctionalRequirement(id="FR-200", name="X", acceptance_criteria=["a"])
    changed_ac = FunctionalRequirement(id="FR-200", name="X", acceptance_criteria=["b"])
    changed_prio = FunctionalRequirement(
        id="FR-200", name="X", acceptance_criteria=["a"], priority=Priority.HIGH
    )

    h = lambda fr: tm.fr_to_task(fr, Language.EN)[0]["source_hash"]  # noqa: E731
    assert h(base) != h(changed_ac)
    assert h(base) == h(changed_prio)


def test_build_is_byte_for_byte_deterministic(tmp_path):
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    for out in (first, second):
        assert build_tasks.main(["--model", str(MIXED), "--out", str(out)]) == 0
    assert first.read_bytes() == second.read_bytes()


# --- schema contract ------------------------------------------------------


def test_output_honours_the_published_contract(tmp_path):
    """Asserted by hand rather than with a jsonschema validator: the plan forbids new
    dependencies, and `importorskip` would let this contract silently go unchecked."""
    payload = load_build(tmp_path)
    assert set(payload) == {"meta", "warnings", "tasks"}
    assert set(payload["meta"]) == {
        "lang", "skip_nfr", "model_path", "model_sha256", "deprecated_ids",
    }

    for task in payload["tasks"]:
        assert set(task) == {
            "source_id", "issue_type", "summary", "description",
            "priority", "labels", "source_hash",
        }
        assert re.fullmatch(r"(FR|NFR)-[A-Z0-9_-]+", task["source_id"])
        assert task["issue_type"] in {"Story", "Task"}
        assert 1 <= len(task["summary"]) <= tm.SUMMARY_MAX
        assert task["priority"] in {"High", "Medium", "Low", "Lowest", None}
        assert task["labels"][0] == tm.LABEL_ALL
        assert all(re.fullmatch(r"[A-Za-z0-9_-]+", lbl) for lbl in task["labels"])
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", task["source_hash"])

    for warning in payload["warnings"]:
        assert set(warning) == {"source_id", "field", "kind"}
        assert warning["kind"] in {"tbd", "missing", "empty_body"}


def test_label_id_prefix_is_the_recovery_contract(tmp_path):
    """Recovery rebuilds source_id by stripping this prefix from the Jira label.
    Renaming it orphans every issue already on the board."""
    assert tm.LABEL_ID_PREFIX == "morkit-id-"
    for task in load_build(tmp_path)["tasks"]:
        recovered = task["labels"][1][len(tm.LABEL_ID_PREFIX):]
        assert recovered == task["source_id"]


def test_model_sha256_binds_the_output_to_its_source(tmp_path):
    """Phase 2 uses this to refuse two different SRS sharing one Jira project map."""
    payload = load_build(tmp_path)
    assert payload["meta"]["model_sha256"] == hashlib.sha256(MIXED.read_bytes()).hexdigest()


def test_project_model_fixture_is_valid():
    ProjectModel.model_validate_json(MIXED.read_bytes())
