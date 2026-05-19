"""Render system-architecture.md from a ProjectModel JSON.

Generates `docs/system-architecture.md` (arc42-lite, 8 sections) with embedded
Mermaid component diagram. Per-Component H3 anchors (`### CMP-NNN`) so the
diff engine can patch sections individually.

CLI:
    render_system_architecture.py --project-model {path}.json --language EN \
        --output docs/system-architecture.md
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))
sys.path.insert(0, str(_THIS_DIR))

from generate_mermaid_arch import generate_arch_diagram  # noqa: E402
from lib.normalized_schema import (  # noqa: E402
    Component,
    Interaction,
    Language,
    Layer,
    ProjectModel,
    QualityGoal,
    load_project_model,
)


def _h(level: int, text: str) -> str:
    return f"{'#' * level} {text}\n\n"


def _safe(v, default: str = "_TBD_") -> str:
    return str(v) if v not in (None, "", []) else default


def _render_meta(model: ProjectModel, lang: Language) -> str:
    today = date.today().isoformat()
    title = (
        "システムアーキテクチャ" if lang == Language.JP
        else "System Architecture" if lang == Language.EN
        else "Kiến trúc hệ thống"
    )
    return (
        f"# {title} — {model.meta.project_name}\n\n"
        f"| Field | Value |\n|---|---|\n"
        f"| Project | {model.meta.project_name} |\n"
        f"| Version | {model.meta.version} |\n"
        f"| Date | {today} |\n"
        f"| Standard | arc42 (lightweight, 8 sections) |\n"
        f"| Language | {lang.value} |\n\n"
        "> Sections 9-12 of arc42 are intentionally omitted — covered by\n"
        "> `design-guidelines.md` (ADR), `srs.md` (NFR / Risk), and the SRS Glossary.\n\n"
    )


def _render_intro(model: ProjectModel, qgs: list[QualityGoal]) -> str:
    out = _h(2, "1. Introduction & Goals")
    intro = model.overview.purpose or model.overview.background
    out += (intro or "_TBD_") + "\n\n"
    out += _h(3, "1.1 Requirements Overview")
    out += "Top-level functional context — see `srs.md § 3` for detailed FRs.\n\n"
    out += _h(3, "1.2 Quality Goals")
    if qgs:
        out += "| ID | Goal | Priority | Description |\n|---|---|---|---|\n"
        for qg in qgs:
            out += f"| {qg.id} | {qg.name} | {qg.priority.value} | {_safe(qg.description)} |\n"
        out += "\n"
    else:
        out += "| QG-001 | _TBD_ | Mid | _TBD_ |\n\n"
    out += _h(3, "1.3 Stakeholders")
    out += "See `srs.md § 1.5`.\n\n"
    return out


def _render_constraints() -> str:
    out = _h(2, "2. Architecture Constraints")
    out += "| Type | Constraint | Rationale |\n|---|---|---|\n"
    out += "| Technical | _TBD_ | _TBD_ |\n"
    out += "| Organizational | _TBD_ | _TBD_ |\n"
    out += "| Conventions | _TBD_ | _TBD_ |\n\n"
    return out


def _render_context(model: ProjectModel) -> str:
    out = _h(2, "3. Context & Scope")
    out += "External actors / systems — detailed external interfaces in `srs.md § 8`.\n\n"
    name = model.meta.project_name or "System"
    out += "```mermaid\nflowchart LR\n"
    out += "    User([User])\n"
    out += f"    System[/{name}/]\n"
    if model.external_interfaces:
        for i, ei in enumerate(model.external_interfaces, 1):
            ext_id = f"Ext{i}"
            label = (ei.name or ei.id).replace('"', "'")
            out += f'    {ext_id}{{"{label}"}}\n'
            out += f"    System --> {ext_id}\n"
    else:
        out += "    Ext1{{External System}}\n"
        out += "    System --> Ext1\n"
    out += "    User --> System\n"
    out += "```\n\n"
    return out


def _render_strategy(model: ProjectModel) -> str:
    out = _h(2, "4. Solution Strategy")
    out += (
        "Top-level technology / pattern choices. Decisions with deeper rationale "
        "belong in `design-guidelines.md § 3 (ADRs)`.\n\n"
    )
    techs = sorted({t for c in model.components for t in c.tech})
    out += f"- **Tech stack:** {', '.join(techs) if techs else '_TBD_'}\n"
    out += "- **Top-level patterns:** _TBD_\n"
    out += "- **Organizational approach:** _TBD_\n\n"
    return out


def _render_building_blocks(
    components: list[Component], layers: list[Layer], interactions: list[Interaction]
) -> str:
    out = _h(2, "5. Building Block View")
    out += "<!-- ARCH-DIAGRAM-START -->\n"
    if components:
        out += generate_arch_diagram(components, layers, interactions) + "\n"
    else:
        out += "```mermaid\nflowchart LR\n    Placeholder[No components yet]\n```\n"
    out += "<!-- ARCH-DIAGRAM-END -->\n\n"

    # Components summary table
    out += _h(3, "5.1 Components")
    if components:
        out += "| ID | Name | Kind | Tech | Depends on |\n|---|---|---|---|---|\n"
        for c in components:
            techs = ", ".join(c.tech) or "-"
            deps = ", ".join(c.depends_on) or "-"
            out += f"| {c.id} | {c.name} | {c.kind} | {techs} | {deps} |\n"
        out += "\n"
    else:
        out += "| CMP-001 | _TBD_ | service | _TBD_ | - |\n\n"

    # Per-component detail (H3 anchors for diff engine)
    for c in components:
        out += _h(3, f"{c.id}: {c.name}")
        out += f"- **Kind:** {c.kind}\n"
        if c.path:
            out += f"- **Path:** `{c.path}`\n"
        if c.tech:
            out += f"- **Tech:** {', '.join(c.tech)}\n"
        if c.responsibility:
            out += f"- **Responsibility:** {c.responsibility}\n"
        if c.depends_on:
            out += f"- **Depends on:** {', '.join(c.depends_on)}\n"
        out += "\n"

    # Layers summary table
    out += _h(3, "5.2 Layers")
    if layers:
        out += "| ID | Name | Components |\n|---|---|---|\n"
        for lay in layers:
            cmps = ", ".join(lay.component_ids) or "-"
            out += f"| {lay.id} | {lay.name} | {cmps} |\n"
        out += "\n"
    else:
        out += "| LAY-001 | _TBD_ | - |\n\n"
    return out


def _render_runtime(interactions: list[Interaction]) -> str:
    out = _h(2, "6. Runtime View")
    out += (
        "Key flows between Components. Sequence diagrams deferred until a `Flow` "
        "entity is added; the table below is authoritative.\n\n"
    )
    if interactions:
        out += "| ID | From | To | Protocol | Description |\n|---|---|---|---|---|\n"
        for inx in interactions:
            out += (
                f"| {inx.id} | {inx.from_id} | {inx.to_id} | {inx.protocol} | "
                f"{_safe(inx.description)} |\n"
            )
        out += "\n"
    else:
        out += "| INX-001 | CMP-001 | CMP-002 | http | _TBD_ |\n\n"
    return out


def _render_deployment(components: list[Component]) -> str:
    out = _h(2, "7. Deployment View")
    out += "Where components run (VM / container / serverless / k8s namespace).\n\n"
    out += "| Component | Environment | Notes |\n|---|---|---|\n"
    if components:
        for c in components:
            out += f"| {c.id} ({c.name}) | _TBD_ | _TBD_ |\n"
    else:
        out += "| CMP-001 | _TBD_ | _TBD_ |\n"
    out += "\n"
    return out


def _render_crosscutting() -> str:
    out = _h(2, "8. Crosscutting Concepts")
    out += "Topics that apply across multiple Components.\n\n"
    out += "- **Authentication & Authorization:** see `srs.md § 5`\n"
    out += "- **Logging & Observability:** _TBD_\n"
    out += "- **Error handling:** _TBD_\n"
    out += "- **Configuration & Secrets:** _TBD_\n"
    out += "- **Internationalization:** _TBD_\n\n"
    return out


def _render_revision_history() -> str:
    return (
        "## Revision History\n\n"
        "| Version | Date | Author | Changes |\n"
        "|---|---|---|---|\n"
        f"| 1.0 | {date.today().isoformat()} | morkit (auto) | Initial generation |\n"
    )


def render_system_architecture(model: ProjectModel, lang: Language) -> str:
    parts = [
        _render_meta(model, lang),
        _render_intro(model, model.quality_goals),
        _render_constraints(),
        _render_context(model),
        _render_strategy(model),
        _render_building_blocks(model.components, model.layers, model.interactions),
        _render_runtime(model.interactions),
        _render_deployment(model.components),
        _render_crosscutting(),
        _render_revision_history(),
    ]
    return "".join(parts)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--project-model", required=True)
    p.add_argument("--language", default="EN", choices=["JP", "EN", "VN"])
    p.add_argument("--output", required=True)
    args = p.parse_args()

    model = load_project_model(args.project_model)
    text = render_system_architecture(model, Language(args.language))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Rendered system architecture -> {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
