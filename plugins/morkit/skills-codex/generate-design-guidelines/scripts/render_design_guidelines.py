"""Render design-guidelines.md (+ per-ADR stubs) from a ProjectModel JSON.

Generates `docs/design-guidelines.md` with §1 Principles, §2 Patterns, §3
ADRs (MADR fields inline), §4 Anti-patterns, §5 Review Checklist. Also
writes one stub `docs/adr/{id}-{slug}.md` per ADR (mirrors how SRS emits
per-screen specs).

CLI:
    render_design_guidelines.py --project-model {path}.json --language EN \
        --output docs/design-guidelines.md \
        [--adr-dir docs/adr]
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))

from lib.normalized_schema import (  # noqa: E402
    ADR,
    DesignPrinciple,
    Language,
    PatternGuideline,
    ProjectModel,
    load_project_model,
)


def _h(level: int, text: str) -> str:
    return f"{'#' * level} {text}\n\n"


def _safe(v, default: str = "_TBD_") -> str:
    return str(v) if v not in (None, "", []) else default


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "untitled"


def _title(lang: Language) -> str:
    if lang == Language.JP:
        return "設計ガイドライン"
    if lang == Language.VN:
        return "Hướng dẫn thiết kế"
    return "Design Guidelines"


def _render_meta(model: ProjectModel, lang: Language) -> str:
    today = date.today().isoformat()
    return (
        f"# {_title(lang)} — {model.meta.project_name}\n\n"
        f"| Field | Value |\n|---|---|\n"
        f"| Project | {model.meta.project_name} |\n"
        f"| Version | {model.meta.version} |\n"
        f"| Date | {today} |\n"
        f"| Standards | MADR (ADRs) |\n"
        f"| Language | {lang.value} |\n\n"
        "> This document is **manual** — there is no codebase sync. Add / edit "
        "entries in the ProjectModel JSON, then re-run `/morkit:init` "
        "(or `/morkit:update-doc`) to regenerate.\n\n"
    )


def _render_principles(items: list[DesignPrinciple]) -> str:
    out = _h(2, "1. Design Principles")
    out += "High-level principles the team agrees to follow.\n\n"
    out += "| ID | Name | Statement |\n|---|---|---|\n"
    if not items:
        out += "| DPR-001 | _TBD_ | _TBD_ |\n\n"
        return out
    for dp in items:
        out += f"| {dp.id} | {dp.name} | {_safe(dp.statement)} |\n"
    out += "\n"
    # Per-principle detail with rationale + examples
    for dp in items:
        if not (dp.rationale or dp.examples):
            continue
        out += _h(3, f"{dp.id}: {dp.name}")
        if dp.rationale:
            out += f"**Rationale.** {dp.rationale}\n\n"
        if dp.examples:
            out += "**Examples:**\n"
            for ex in dp.examples:
                out += f"- {ex}\n"
            out += "\n"
    return out


def _render_patterns(items: list[PatternGuideline]) -> str:
    out = _h(2, "2. Patterns We Use / Avoid")
    out += "| ID | Name | Category | When to Use | When to Avoid |\n"
    out += "|---|---|---|---|---|\n"
    if not items:
        out += "| PTN-001 | _TBD_ | arch | _TBD_ | _TBD_ |\n\n"
        return out
    for pg in items:
        out += (
            f"| {pg.id} | {pg.name} | {pg.category} | "
            f"{_safe(pg.when_to_use)} | {_safe(pg.when_to_avoid)} |\n"
        )
    out += "\n"
    return out


def _render_adrs(items: list[ADR], adr_dir_rel: str) -> str:
    out = _h(2, "3. Architecture Decision Records (ADRs)")
    out += (
        "ADRs follow the [MADR](https://adr.github.io/madr/) template. Each "
        f"ADR also gets a per-decision stub at `{adr_dir_rel}/{{id}}-{{slug}}.md`.\n\n"
    )
    if not items:
        out += _h(3, "ADR-001: _TBD_")
        out += "| Field | Value |\n|---|---|\n| Status | proposed |\n\n"
        out += "#### Context\n_TBD_\n\n#### Decision\n_TBD_\n\n#### Consequences\n_TBD_\n\n"
        return out
    for adr in sorted(items, key=lambda a: a.id):
        out += _h(3, f"{adr.id}: {adr.title}")
        out += "| Field | Value |\n|---|---|\n"
        out += f"| Status | {adr.status} |\n"
        out += f"| Date | {_safe(adr.date)} |\n"
        if adr.superseded_by:
            out += f"| Superseded by | {adr.superseded_by} |\n"
        out += "\n"
        out += f"#### Context\n{_safe(adr.context)}\n\n"
        out += f"#### Decision\n{_safe(adr.decision)}\n\n"
        out += f"#### Consequences\n{_safe(adr.consequences)}\n\n"
    return out


def _render_anti_patterns() -> str:
    out = _h(2, "4. Anti-patterns")
    out += "Patterns the team has explicitly chosen NOT to use.\n\n- _TBD_\n\n"
    return out


def _render_review_checklist() -> str:
    out = _h(2, "5. Review Checklist")
    out += "Quick checklist for code reviewers.\n\n"
    out += (
        "- [ ] Follows the design principles in §1\n"
        "- [ ] Uses an approved pattern from §2 (or justifies a new one in PR description)\n"
        "- [ ] No anti-patterns from §4\n"
        "- [ ] If introducing an architectural change → new ADR added in §3\n\n"
    )
    return out


def _render_revision_history() -> str:
    return (
        "## Revision History\n\n"
        "| Version | Date | Author | Changes |\n"
        "|---|---|---|---|\n"
        f"| 1.0 | {date.today().isoformat()} | morkit (auto) | Initial generation |\n"
    )


def render_design_guidelines(
    model: ProjectModel, lang: Language, adr_dir_rel: str
) -> str:
    parts = [
        _render_meta(model, lang),
        _render_principles(model.design_principles),
        _render_patterns(model.pattern_guidelines),
        _render_adrs(model.adrs, adr_dir_rel),
        _render_anti_patterns(),
        _render_review_checklist(),
        _render_revision_history(),
    ]
    return "".join(parts)


def render_adr_stub(adr: ADR, lang: Language) -> str:
    """One per-decision stub (MADR-style) for docs/adr/{id}-{slug}.md."""
    out = f"# {adr.id}: {adr.title}\n\n"
    out += "| Field | Value |\n|---|---|\n"
    out += f"| Status | {adr.status} |\n"
    out += f"| Date | {_safe(adr.date)} |\n"
    if adr.superseded_by:
        out += f"| Superseded by | {adr.superseded_by} |\n"
    out += "\n"
    out += f"## Context\n{_safe(adr.context)}\n\n"
    out += f"## Decision\n{_safe(adr.decision)}\n\n"
    out += f"## Consequences\n{_safe(adr.consequences)}\n\n"
    out += f"<!-- Generated by morkit on {date.today().isoformat()}. "
    out += f"Authoritative copy lives in design-guidelines.md §3 — keep both in sync. -->\n"
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--project-model", required=True)
    p.add_argument("--language", default="EN", choices=["JP", "EN", "VN"])
    p.add_argument("--output", required=True)
    p.add_argument(
        "--adr-dir",
        help="Directory for per-ADR stubs (default: <output-parent>/adr)",
    )
    args = p.parse_args()

    model = load_project_model(args.project_model)
    out_path = Path(args.output)
    adr_dir = Path(args.adr_dir) if args.adr_dir else out_path.parent / "adr"
    adr_dir_rel = adr_dir.name if adr_dir.parent == out_path.parent else str(adr_dir)

    text = render_design_guidelines(model, Language(args.language), adr_dir_rel)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Rendered design guidelines -> {args.output}", file=sys.stderr)

    # Per-ADR stubs
    if model.adrs:
        adr_dir.mkdir(parents=True, exist_ok=True)
        for adr in model.adrs:
            stub_path = adr_dir / f"{adr.id}-{_slug(adr.title)}.md"
            stub_path.write_text(
                render_adr_stub(adr, Language(args.language)), encoding="utf-8"
            )
        print(
            f"Wrote {len(model.adrs)} ADR stubs -> {adr_dir}/", file=sys.stderr
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
