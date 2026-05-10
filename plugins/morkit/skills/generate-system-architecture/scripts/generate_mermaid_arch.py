"""Generate a Mermaid `flowchart LR` block from components + layers + interactions.

Importable: `generate_arch_diagram(components, layers, interactions) -> str`
CLI: read ProjectModel JSON, write Mermaid to file or stdout.

Layout:
- Layers become `subgraph` blocks; Components without a Layer go in a
  `subgraph Unassigned`.
- Interactions become directed edges, optionally labeled with the protocol.
- `classDef` styles per Component.kind (service / datastore / external / ...).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))

from lib.normalized_schema import (  # noqa: E402
    Component,
    Interaction,
    Layer,
    load_project_model,
)


_KIND_STYLES = {
    "service": "fill:#e1f5ff,stroke:#0288d1",
    "library": "fill:#f1f8e9,stroke:#558b2f",
    "app": "fill:#e8eaf6,stroke:#3949ab",
    "frontend": "fill:#fff8e1,stroke:#f9a825",
    "worker": "fill:#fce4ec,stroke:#ad1457",
    "datastore": "fill:#fff3e0,stroke:#f57c00",
    "external": "fill:#f3e5f5,stroke:#7b1fa2",
}


def _safe_id(s: str) -> str:
    """Mermaid node IDs allow alphanumerics + underscore."""
    return "".join(c if c.isalnum() or c == "_" else "_" for c in s)


def _node_label(c: Component) -> str:
    tech = f"<br/><i>{', '.join(c.tech)}</i>" if c.tech else ""
    return f'{c.id}["<b>{c.name}</b>{tech}"]'


def generate_arch_diagram(
    components: list[Component],
    layers: list[Layer],
    interactions: list[Interaction],
) -> str:
    """Build a Mermaid `flowchart LR` block grouping Components by Layer."""
    lines: list[str] = ["```mermaid", "flowchart LR"]

    # classDef per kind
    for kind, style in _KIND_STYLES.items():
        lines.append(f"    classDef {kind} {style}")
    lines.append("")

    # Group components by layer; track unassigned
    layer_for: dict[str, str] = {}
    for lay in layers:
        for cmp_id in lay.component_ids:
            layer_for[cmp_id] = lay.id

    by_layer: dict[str, list[Component]] = {}
    unassigned: list[Component] = []
    for c in components:
        lid = layer_for.get(c.id)
        if lid is None:
            unassigned.append(c)
        else:
            by_layer.setdefault(lid, []).append(c)

    layer_lookup = {lay.id: lay for lay in layers}

    for lay_id, cmps in by_layer.items():
        lay = layer_lookup.get(lay_id)
        title = (lay.name if lay else lay_id).replace('"', "'")
        lines.append(f'    subgraph {_safe_id(lay_id)}["{title}"]')
        for c in cmps:
            lines.append(f"        {_node_label(c)}")
        lines.append("    end")
        lines.append("")

    if unassigned:
        lines.append('    subgraph UNASSIGNED["Unassigned"]')
        for c in unassigned:
            lines.append(f"        {_node_label(c)}")
        lines.append("    end")
        lines.append("")

    # Edges from Interactions; fall back to Component.depends_on if no Interactions
    if interactions:
        for inx in interactions:
            label = (inx.description or inx.protocol or "").replace('"', "'")
            arrow = f'-- "{label}" -->' if label else "-->"
            lines.append(f"    {inx.from_id} {arrow} {inx.to_id}")
    else:
        for c in components:
            for dep in c.depends_on:
                lines.append(f"    {c.id} --> {dep}")

    # Apply classDef per component
    for c in components:
        cls = c.kind if c.kind in _KIND_STYLES else "service"
        lines.append(f"    class {c.id} {cls}")

    lines.append("```")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--project-model", required=True)
    p.add_argument("--output", help="Optional output path; stdout if omitted")
    args = p.parse_args()

    model = load_project_model(args.project_model)
    text = generate_arch_diagram(model.components, model.layers, model.interactions)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
        print(f"Arch diagram written -> {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
