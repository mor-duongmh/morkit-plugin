"""Map ProjectModel FR/NFR entities to Jira task payloads (Server/DC, wiki markup).

Pure functions — no I/O, no network. `build_tasks.py` owns the CLI and file writes.

Three decisions worth stating, because each one is a trap someone will re-fall into:

1. Headings come from `language_pack.t()`, never from a table in this file. The
   pipeline ships JP/EN/VN docs, so a hardcoded heading table puts Vietnamese
   headers on a Japanese client's board.

2. `<TBD: ...>` is a *valid* build-project-model output (the no-fiction convention
   says an unknown fact becomes a TBD marker, not an invented value). It is data,
   not junk — but it is internal draft state and must never reach a customer's
   board. So it counts as empty here and surfaces as a warning at the approval gate.

3. `summary` is escaped for a markdown table cell, not just for Jira. It lands in
   `task-breakdown.md`, whose frontmatter carries the human approval. A newline in
   an FR name (free text, extracted from a customer PDF by an LLM) would otherwise
   inject arbitrary lines into that file.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

_ORCH_SCRIPTS = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_SCRIPTS))

from lib.language_pack import t  # noqa: E402
from lib.normalized_schema import (  # noqa: E402
    FunctionalRequirement,
    NonFunctionalRequirement,
    Priority,
)

SUMMARY_MAX = 255  # Jira system field limit
LABEL_MAX = 255
LABEL_ALL = "morkit-srs"  # every issue this skill creates
LABEL_ID_PREFIX = "morkit-id-"  # type-neutral: FR-001 and NFR-01 both fit

# SRS section a reader can open to see the full requirement.
SRS_SECTION = {"FR": "§3.2", "NFR": "§6.1"}

_TBD = re.compile(r"^<TBD:?.*>$", re.IGNORECASE | re.DOTALL)
_LABEL_ILLEGAL = re.compile(r"[^A-Za-z0-9_-]")
_LABEL_RUNS = re.compile(r"-{2,}")
# Line-leading tokens Jira reads as structure (lists, headings, quotes).
_WIKI_LINE_LEAD = re.compile(r"^(\s*)([*#\-+]|h[1-6]\.|bq\.)", re.MULTILINE)

_PRIORITY_MAP = {
    Priority.HIGH: "High",
    Priority.MUST: "High",
    Priority.MID: "Medium",
    Priority.SHOULD: "Medium",
    Priority.LOW: "Low",
    Priority.COULD: "Low",
    Priority.WONT: "Lowest",
}


class MappingError(ValueError):
    """An entity cannot become a Jira issue (e.g. no usable summary)."""


def is_tbd(value: object) -> bool:
    """True for a `<TBD: ...>` placeholder. Such a value is treated as absent."""
    return isinstance(value, str) and bool(_TBD.match(value.strip()))


def clean(value: object) -> str | None:
    """Normalize a field to text, or None when it is empty / a TBD placeholder."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or is_tbd(text):
        return None
    return text


def cell_safe(text: str) -> str:
    """Make text safe for a markdown table cell in the approval gate file.

    Newlines are the dangerous one: the gate file's approval lives in its
    frontmatter, and a newline here could write new lines into the body.
    """
    flattened = re.sub(r"[\r\n\t]+", " ", text).replace("|", "/")
    return re.sub(r"\s{2,}", " ", flattened).strip()


def wiki_escape(text: str) -> str:
    """Neutralize Jira wiki markup in text taken verbatim from the SRS.

    `{` opens macros ({code}, {color}, ...), `[` opens links, `|` breaks tables,
    and a line-leading `*`/`#`/`-`/`h2.` turns prose into structure.
    """
    escaped = re.sub(r"([{}\[\]|])", r"\\\1", text)
    return _WIKI_LINE_LEAD.sub(r"\1\\\2", escaped)


def make_labels(source_id: str) -> list[str]:
    """`FR-001` -> ['morkit-srs', 'morkit-id-FR-001'].

    Jira forbids spaces in labels; hyphens are safe on both Cloud and Server/DC.
    IDs are already regex-constrained upstream (`^FR-[A-Z0-9_-]+$`), so this
    sanitize is defense in depth, not the primary guard.
    """
    slug = _LABEL_RUNS.sub("-", _LABEL_ILLEGAL.sub("-", source_id)).strip("-")
    return [LABEL_ALL, (LABEL_ID_PREFIX + slug)[:LABEL_MAX]]


def map_priority(priority: Priority | str | None) -> str | None:
    """ProjectModel priority -> Jira priority name. Unknown -> None (field omitted).

    The mapping happens here, once. Downstream files carry the *Jira* name, so
    `Mid` never reaches a payload — Jira has no such priority and would drop it.
    """
    if priority is None:
        return None
    try:
        return _PRIORITY_MAP[Priority(priority)]
    except (ValueError, KeyError):
        return None


def source_hash(summary: str, description: str) -> str:
    """Hash of what a reader sees on the issue. Drives the CREATE/UPDATE/SKIP diff.

    Priority and labels are deliberately excluded: re-prioritizing a requirement
    should not rewrite its whole description on the next run.
    """
    digest = hashlib.sha256(f"{summary}\x00{description}".encode()).hexdigest()
    return f"sha256:{digest}"


def _summary(source_id: str, raw: str | None, field: str) -> str:
    """Build `[ID] text`, truncated to Jira's limit. Empty text is fatal."""
    text = clean(raw)
    if text is None:
        raise MappingError(
            f"{source_id}: cannot build a summary — `{field}` is empty or a TBD placeholder. "
            f"Jira rejects an issue with a blank summary; fill it in the SRS first."
        )
    prefix = f"[{source_id}] "
    body = cell_safe(text.splitlines()[0])
    budget = SUMMARY_MAX - len(prefix)
    if len(body) > budget:
        body = body[: budget - 1].rstrip() + "…"
    return prefix + body


def _section(heading_key: str, lang, body: str) -> str:
    return f"h3. {t(heading_key, lang)}\n{body}"


def _source_line(entity, kind: str, lang) -> str | None:
    """Provenance: where in the SRS, and which customer file it came from."""
    parts = [f"SRS {SRS_SECTION[kind]} {entity.id}"]
    src = getattr(entity, "source", None)
    if src is not None and getattr(src, "file_path", None):
        parts.append(src.file_path)
    return _section("source", lang, " · ".join(wiki_escape(p) for p in parts))


def _bullets(items: list[str], marker: str) -> str | None:
    """Render a list, dropping empty/TBD entries. All entries dropped -> no section."""
    kept = [c for c in (clean(i) for i in items) if c]
    if not kept:
        return None
    return "\n".join(f"{marker} {wiki_escape(i)}" for i in kept)


def _prose(value: object) -> str | None:
    """A single free-text field, escaped — or None when absent / TBD."""
    text = clean(value)
    return wiki_escape(text) if text else None


def _warn(warnings: list[dict], source_id: str, field: str, kind: str) -> None:
    warnings.append({"source_id": source_id, "field": field, "kind": kind})


def _note_tbd(warnings: list[dict], entity, field: str) -> None:
    """A TBD placeholder is dropped from the ticket but must be visible at the gate."""
    if is_tbd(getattr(entity, field, None)):
        _warn(warnings, entity.id, field, "tbd")


def fr_to_task(fr: FunctionalRequirement, lang) -> tuple[dict, list[dict]]:
    """FunctionalRequirement -> Jira Story payload + warnings for the approval gate."""
    warnings: list[dict] = []
    summary = _summary(fr.id, fr.name, "name")

    sections = []
    for key, value in (
        ("description", _prose(fr.description)),
        ("main_flow", _bullets(fr.main_flow, "#")),
        ("acceptance_criteria", _bullets(fr.acceptance_criteria, "*")),
        ("business_rules", _bullets(fr.business_rules, "*")),
        ("related_screens", _bullets(fr.related_screens, "*")),
        ("related_data", _bullets(fr.related_data, "*")),
        ("notes", _bullets(fr.notes, "*")),
    ):
        if value:
            sections.append(_section(key, lang, value))
    _note_tbd(warnings, fr, "description")

    src = _source_line(fr, "FR", lang)
    if src:
        sections.append(src)
    if not sections:
        _warn(warnings, fr.id, "*", "empty_body")

    return _task(fr.id, "Story", summary, "\n\n".join(sections), fr.priority), warnings


def nfr_to_task(nfr: NonFunctionalRequirement, lang) -> tuple[dict, list[dict]]:
    """NonFunctionalRequirement -> Jira Task payload + warnings.

    NFR has no `name` and no `description` — `requirement` is the only prose it
    carries, so it is both the summary source and the body.
    """
    warnings: list[dict] = []
    summary = _summary(nfr.id, nfr.requirement, "requirement")

    sections = []
    for key, raw in (
        ("requirement", nfr.requirement),
        ("category", nfr.category),
        ("metric", nfr.metric),
        ("measurement_condition", nfr.measurement_condition),
    ):
        value = _prose(raw)
        if value:
            sections.append(_section(key, lang, value))
        else:
            # An NFR without a metric is unverifiable — the gate should say so.
            _warn(warnings, nfr.id, key, "tbd" if is_tbd(raw) else "missing")

    src = _source_line(nfr, "NFR", lang)
    if src:
        sections.append(src)

    return _task(nfr.id, "Task", summary, "\n\n".join(sections), nfr.priority), warnings


def _task(source_id: str, issue_type: str, summary: str, description: str, priority) -> dict:
    return {
        "source_id": source_id,
        "issue_type": issue_type,
        "summary": summary,
        "description": description,
        "priority": map_priority(priority),
        "labels": make_labels(source_id),
        "source_hash": source_hash(summary, description),
    }
