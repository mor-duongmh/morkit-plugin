"""Pydantic models for diff engine: meta sidecar, manual edits, patch plans.

Public API:
    MetaSidecar       — `.docs-hero-meta.json` schema
    DocMeta           — per-doc metadata block
    ManualEditReport  — output of detect-manual-edits
    SectionStatus     — status of one section in manual edit detection
    PatchOp           — single patch operation
    PatchPlan         — list of ops + revision entry
    RevisionEntry     — revision history row
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

_BaseConfig = ConfigDict(extra="allow")


class _Base(BaseModel):
    model_config = _BaseConfig


# --- Meta sidecar (.docs-hero-meta.json) ---


class DocMeta(_Base):
    doc_version: str = "1.0"
    last_render: str = ""
    section_hashes: dict[str, str] = Field(default_factory=dict)
    section_order: list[str] = Field(default_factory=list)
    deprecated: list[str] = Field(default_factory=list)


class MetaSidecar(_Base):
    schema_version: str = "1.0"
    generated_at: str = ""
    generator: str = "docs-hero@1.0.0"
    docs: dict[str, DocMeta] = Field(default_factory=dict)


# --- Manual edit detection ---


class SectionStatus(_Base):
    section_id: str
    status: Literal["clean", "manual_edit", "untracked", "deleted_by_user"]
    expected_hash: Optional[str] = None
    current_hash: Optional[str] = None
    line_range: Optional[tuple[int, int]] = None


class ManualEditSummary(_Base):
    total_sections: int = 0
    clean: int = 0
    manual_edit: int = 0
    untracked: int = 0
    deleted_by_user: int = 0


class ManualEditReport(_Base):
    doc_path: str
    scan_at: str = ""
    summary: ManualEditSummary = Field(default_factory=ManualEditSummary)
    sections: list[SectionStatus] = Field(default_factory=list)


# --- Patch plan ---


class PatchOp(_Base):
    op: Literal["INSERT", "REPLACE", "MOVE_TO_APPENDIX", "SKIP"]
    section_id: str
    after_section: Optional[str] = None  # For INSERT positioning
    block_md: Optional[str] = None  # For INSERT/REPLACE
    old_hash: Optional[str] = None  # For REPLACE verification
    new_hash: Optional[str] = None
    marker: Optional[str] = None  # For DEPRECATE: "[DEPRECATED v1.0]"
    reason: Optional[str] = None
    proposed_change: Optional[dict] = None  # For SKIP: what was proposed


class RevisionEntry(_Base):
    version: str
    date: str
    author: str = "docs-hero (auto)"
    changes_summary: str = ""


class PatchPlan(_Base):
    doc_path: str
    current_version: str = "1.0"
    next_version: str = "1.1"
    ops: list[PatchOp] = Field(default_factory=list)
    revision_entry: Optional[RevisionEntry] = None
    conflicts: list[SectionStatus] = Field(default_factory=list)


# --- IO helpers ---


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_meta(path: str | Path) -> MetaSidecar:
    p = Path(path)
    if not p.exists():
        return MetaSidecar(generated_at=now_iso())
    return MetaSidecar.model_validate(json.loads(p.read_text(encoding="utf-8")))


def save_meta(meta: MetaSidecar, path: str | Path) -> None:
    Path(path).write_text(
        meta.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
    )


def load_manual_edit_report(path: str | Path) -> ManualEditReport:
    return ManualEditReport.model_validate(
        json.loads(Path(path).read_text(encoding="utf-8"))
    )


def save_manual_edit_report(report: ManualEditReport, path: str | Path) -> None:
    Path(path).write_text(
        report.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
    )


def load_patch_plan(path: str | Path) -> PatchPlan:
    return PatchPlan.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))


def save_patch_plan(plan: PatchPlan, path: str | Path) -> None:
    Path(path).write_text(
        plan.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
    )
