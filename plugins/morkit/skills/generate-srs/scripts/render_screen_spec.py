"""Render a per-screen markdown spec from a Screen entity in ProjectModel.

Output goes into `docs/screen-specs/{screen_id}-{slug}.md`.

CLI:
    render-screen-spec.py --project-model {path}.json --screen-id SCREEN-001
                          --language JP --output docs/screen-specs/SCREEN-001-login.md
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))

from lib.language_pack import Language, t  # noqa: E402
from lib.normalized_schema import Screen, load_project_model  # noqa: E402

KIND_EMOJI = {
    "input": "🔵",
    "button": "🟠",
    "label": "⚪",
    "output": "⚪",
    "table": "🟢",
    "chart": "🟢",
    "link": "🟣",
}


def render_screen_spec(screen: Screen, lang: Language) -> str:
    out: list[str] = []
    today = date.today().isoformat()

    # Header
    out.append(f"# {screen.id}: {screen.name}\n\n")
    out.append("| Field | Value |\n|---|---|\n")
    out.append(f"| Screen ID | {screen.id} |\n")
    out.append(f"| Slug | {screen.slug} |\n")
    out.append(f"| Role | {screen.role} |\n")
    if screen.url_path:
        out.append(f"| URL | `{screen.url_path}` |\n")
    if screen.related_fr:
        out.append(f"| Related FR | {', '.join(screen.related_fr)} |\n")
    if screen.parent_screen:
        out.append(f"| Parent | {screen.parent_screen} |\n")
    out.append(f"| Priority | {screen.priority.value} |\n")
    out.append(f"| Generated | {today} |\n\n")

    # Layout / mockup
    out.append(f"## 1. {t('layout', lang)}\n\n")
    if screen.mockup and screen.mockup.annotated_path:
        rel = Path(screen.mockup.annotated_path).name
        out.append(f"![{screen.id}](../assets/screens/{rel})\n\n")
        if screen.mockup.path:
            out.append(f"> Original mockup: `{screen.mockup.path}`\n")
        out.append(
            "> Numbers on the image correspond to the `#` column in the tables below.\n"
            "> Color code: 🔵 input | 🟠 button | ⚪ label/output | 🟢 table/chart | 🟣 link\n\n"
        )
    elif screen.mockup and screen.mockup.url:
        out.append(f"Figma: {screen.mockup.url}\n\n")
    elif screen.mockup and screen.mockup.layout_ascii:
        out.append("```\n" + screen.mockup.layout_ascii + "\n```\n\n")
    else:
        out.append("_Mockup not provided. Add image to `assets/screens/{id}-{slug}.png` and re-run._\n\n")

    if screen.mockup and screen.mockup.description:
        out.append(f"### {t('layout', lang)} Description\n\n{screen.mockup.description}\n\n")

    # Items grouped by kind
    inputs = [it for it in screen.items if it.kind == "input"]
    outputs = [it for it in screen.items if it.kind in {"label", "output", "table", "chart"}]
    actions = [it for it in screen.items if it.kind in {"button", "link"}]

    if inputs:
        out.append(f"## 2. {t('input_items', lang)} 🔵\n\n")
        out.append("| # | Label | Type | Required | Validation | Error | Notes |\n")
        out.append("|---|---|---|---|---|---|---|\n")
        for it in inputs:
            req = "Y" if it.required else "N" if it.required is False else "-"
            out.append(
                f"| {it.number} | {it.label} | {it.type or '-'} | {req} | "
                f"{it.validation or '-'} | {it.error_code or '-'} | {it.notes or '-'} |\n"
            )
        out.append("\n")

    if outputs:
        out.append(f"## 3. {t('output_items', lang)} ⚪\n\n")
        out.append("| # | Label | Kind | Source | Notes |\n|---|---|---|---|---|\n")
        for it in outputs:
            out.append(f"| {it.number} | {it.label} | {it.kind} | {it.api_call or '-'} | {it.notes or '-'} |\n")
        out.append("\n")

    if actions:
        out.append(f"## 4. {t('actions', lang)} 🟠\n\n")
        out.append("| # | Label | Kind | API Call | Notes |\n|---|---|---|---|---|\n")
        for it in actions:
            out.append(f"| {it.number} | {it.label} | {it.kind} | {it.api_call or '-'} | {it.notes or '-'} |\n")
        out.append("\n")

    # Transitions
    if screen.transitions:
        out.append(f"## 5. {t('transitions', lang)}\n\n")
        out.append("```mermaid\nflowchart LR\n")
        for tr in screen.transitions:
            label = f'"{tr.trigger}"' if tr.trigger else ""
            out.append(f"    {tr.from_screen} -->|{label}| {tr.to_screen}\n")
        out.append("```\n\n")
        out.append("| Trigger | From | To | Condition |\n|---|---|---|---|\n")
        for tr in screen.transitions:
            out.append(f"| {tr.trigger} | {tr.from_screen} | {tr.to_screen} | {tr.condition or '-'} |\n")
        out.append("\n")

    # Business logic
    if screen.business_logic:
        out.append(f"## 6. {t('business_logic', lang)}\n\n")
        for section, steps in screen.business_logic.items():
            if not steps:
                continue
            out.append(f"### {section}\n\n")
            for i, step in enumerate(steps, 1):
                out.append(f"{i}. {step}\n")
            out.append("\n")

    # Test considerations
    if screen.test_considerations:
        out.append(f"## 7. {t('test_considerations', lang)}\n\n")
        for tc in screen.test_considerations:
            out.append(f"- [ ] {tc}\n")
        out.append("\n")

    # Related links
    out.append(f"## 8. {t('related_files', lang)}\n\n")
    out.append("- [SRS](../srs.md)\n")
    out.append("- [API Docs](../api-docs.md)\n")
    out.append("- [Database Design](../database-design.md)\n")

    return "".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--project-model", required=True)
    p.add_argument("--screen-id", required=True)
    p.add_argument("--language", default="EN", choices=["JP", "EN", "VN"])
    p.add_argument("--output", required=True)
    args = p.parse_args()

    model = load_project_model(args.project_model)
    screen = next((s for s in model.screens if s.id == args.screen_id), None)
    if screen is None:
        print(f"Screen {args.screen_id} not found in model", file=sys.stderr)
        return 2

    text = render_screen_spec(screen, Language(args.language))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Rendered {args.screen_id} -> {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
