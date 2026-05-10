"""Parse an OpenSpec change folder into a normalized Delta.

Reads proposal.md + design.md + specs/*.md from
`openspec/changes/{change-name}/` and emits a Delta JSON with
ADD / UPDATE / DEPRECATE operations.

OpenSpec convention parsed:
    ## ADDED Requirements         -> ADD ops
    ## MODIFIED Requirements      -> UPDATE ops
    ## REMOVED Requirements       -> DEPRECATE ops
    ### Requirement: <name>       -> entity name
    #### Scenario: <name>         -> scenario (mapped to main_flow steps)

CLI:
    parse-openspec.py --openspec-dir openspec/ --change-name <name> --output delta.json

Public API (importable):
    parse_openspec_change(openspec_dir, change_name) -> Delta
    list_changes(openspec_dir) -> list[str]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.id_allocator import IdAllocator  # noqa: E402
from lib.normalized_schema import Change, Delta, save_delta  # noqa: E402

# Heading regexes
_SECTION_HEADER = re.compile(
    r"^##\s+(ADDED|MODIFIED|REMOVED)\s+Requirements?\s*$", re.IGNORECASE
)
_REQUIREMENT_HEADER = re.compile(r"^###\s+Requirement:\s*(.+?)\s*$", re.IGNORECASE)
_SCENARIO_HEADER = re.compile(r"^####\s+Scenario:\s*(.+?)\s*$", re.IGNORECASE)


def list_changes(openspec_dir: str | Path) -> list[str]:
    """Return list of change folder names under openspec/changes/."""
    changes_dir = Path(openspec_dir) / "changes"
    if not changes_dir.exists():
        return []
    return sorted(p.name for p in changes_dir.iterdir() if p.is_dir())


def parse_openspec_change(openspec_dir: str | Path, change_name: str) -> Delta:
    """Parse openspec/changes/{change_name}/ → Delta."""
    base = Path(openspec_dir) / "changes" / change_name
    if not base.exists():
        raise FileNotFoundError(f"OpenSpec change folder not found: {base}")

    # Track existing IDs to allocate new ones safely
    allocator = IdAllocator(existing_ids=[])
    changes: list[Change] = []
    reason_prefix = f"From OpenSpec change {change_name}"

    # Parse delta specs in specs/
    specs_dir = base / "specs"
    if specs_dir.exists():
        for spec_file in sorted(specs_dir.glob("*.md")):
            changes.extend(_parse_spec_file(spec_file, allocator, reason_prefix))

    return Delta(
        source_type="openspec",
        source_path=str(base),
        changes=changes,
    )


def _parse_spec_file(
    spec_path: Path, allocator: IdAllocator, reason_prefix: str
) -> list[Change]:
    """Parse one delta spec file → Change list."""
    text = spec_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    current_op: str | None = None  # "ADD" | "UPDATE" | "DEPRECATE"
    current_req_name: str | None = None
    current_req_body: list[str] = []
    current_scenarios: list[tuple[str, list[str]]] = []
    current_scenario_name: str | None = None
    current_scenario_steps: list[str] = []

    changes: list[Change] = []

    def flush_requirement() -> None:
        nonlocal current_req_name, current_req_body, current_scenarios
        if current_op is None or current_req_name is None:
            return
        flush_scenario()
        if current_op == "DEPRECATE":
            change_id = allocator.next("FR")
            changes.append(
                Change(
                    op="DEPRECATE",
                    entity_type="FR",
                    entity_id=change_id,
                    payload={"name": current_req_name},
                    reason=f"{reason_prefix}: removed requirement '{current_req_name}'",
                )
            )
        else:
            payload: dict = {
                "name": current_req_name,
                "description": "\n".join(current_req_body).strip(),
                "main_flow": _scenarios_to_main_flow(current_scenarios),
                "source": {
                    "origin": "openspec",
                    "file_path": str(spec_path),
                },
            }
            change_id = allocator.next("FR")
            payload["id"] = change_id
            changes.append(
                Change(
                    op=current_op,
                    entity_type="FR",
                    entity_id=change_id,
                    payload=payload,
                    reason=(
                        f"{reason_prefix}: added '{current_req_name}'"
                        if current_op == "ADD"
                        else f"{reason_prefix}: modified '{current_req_name}'"
                    ),
                )
            )
        current_req_name = None
        current_req_body = []
        current_scenarios = []

    def flush_scenario() -> None:
        nonlocal current_scenario_name, current_scenario_steps
        if current_scenario_name is not None:
            current_scenarios.append((current_scenario_name, current_scenario_steps))
        current_scenario_name = None
        current_scenario_steps = []

    for raw_line in lines:
        line = raw_line.rstrip()

        sec_match = _SECTION_HEADER.match(line)
        if sec_match:
            flush_requirement()
            label = sec_match.group(1).upper()
            current_op = {"ADDED": "ADD", "MODIFIED": "UPDATE", "REMOVED": "DEPRECATE"}[label]
            continue

        req_match = _REQUIREMENT_HEADER.match(line)
        if req_match and current_op is not None:
            flush_requirement()
            current_req_name = req_match.group(1).strip()
            continue

        scen_match = _SCENARIO_HEADER.match(line)
        if scen_match and current_req_name is not None:
            flush_scenario()
            current_scenario_name = scen_match.group(1).strip()
            continue

        # Body content
        if current_scenario_name is not None:
            stripped = line.strip()
            if stripped.startswith("-") or stripped.startswith("*"):
                current_scenario_steps.append(stripped.lstrip("-* ").strip())
            elif stripped:
                current_scenario_steps.append(stripped)
        elif current_req_name is not None:
            if line.strip():
                current_req_body.append(line)

    flush_requirement()
    return changes


def _scenarios_to_main_flow(scenarios: list[tuple[str, list[str]]]) -> list[str]:
    """Flatten Given/When/Then scenarios into main_flow steps."""
    flow: list[str] = []
    for name, steps in scenarios:
        if name:
            flow.append(f"[{name}]")
        flow.extend(steps)
    return flow


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--openspec-dir", required=True)
    p.add_argument("--change-name", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    delta = parse_openspec_change(args.openspec_dir, args.change_name)
    save_delta(delta, args.output)
    print(
        f"Parsed {args.change_name}: {len(delta.changes)} changes -> {args.output}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
