"""Scan a codebase for high-level Components → feeds system-architecture doc.

Detection sources (combined):
    1. Top-level dir conventions: `apps/*`, `services/*`, `packages/*`,
       `cmd/*` (Go), `crates/*` (Rust), `libs/*`
    2. Container manifests: `Dockerfile`, `docker-compose.yml`, `k8s/*.yaml`
       (each `services:` entry → service Component; `image:` infers tech)
    3. Reuse `parse_codebase_routes.scan_routes` — directories owning HTTP
       endpoints become `service` Components (tech inferred from framework)
    4. Reuse `parse_codebase_models.scan_models` — directories with ORM
       models become `datastore` Components (tech = engine)
    5. Coarse `depends_on` edges: directory-level imports
       (any file in `services/A/**` importing `services/B/**` → A → B)

Output: list of `ComponentDef` dicts saved as JSON.

CLI:
    parse_codebase_arch.py --paths "." --output arch.json

Public API:
    scan_components(paths, ignore=None) -> list[dict]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

_DEFAULT_IGNORES = {
    ".git", "node_modules", "dist", "build", ".next", ".venv",
    "__pycache__", "vendor", "target", ".turbo", ".cache", "out",
}

# Top-level dir conventions that imply a Component each
_COMPONENT_PARENT_DIRS = ("apps", "services", "packages", "cmd", "crates", "libs")

# Heuristic regex for cross-Component imports (per language)
_IMPORT_PATTERNS = {
    "py": re.compile(r"^\s*(?:from|import)\s+([a-zA-Z0-9_.]+)", re.MULTILINE),
    "js": re.compile(r"""(?:from|require\()\s*['"]([^'"]+)['"]""", re.MULTILINE),
    "ts": re.compile(r"""(?:from|require\()\s*['"]([^'"]+)['"]""", re.MULTILINE),
    "go": re.compile(r"""^\s*\"([^\"]+)\"""", re.MULTILINE),
    "rs": re.compile(r"^\s*use\s+([a-zA-Z0-9_:]+)", re.MULTILINE),
}

_LANG_BY_EXT = {
    ".py": "py", ".pyi": "py",
    ".js": "js", ".jsx": "js", ".mjs": "js", ".cjs": "js",
    ".ts": "ts", ".tsx": "ts",
    ".go": "go",
    ".rs": "rs",
}


@dataclass
class ComponentDef:
    """One Component detected from the codebase."""

    id: str  # CMP-<slug>
    name: str
    kind: str = "service"  # service | library | app | frontend | worker | datastore | external
    path: str = ""  # repo-relative dir
    tech: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)  # other CMP IDs
    detection_source: str = "dir-convention"  # dir-convention | docker | k8s | routes | models


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _is_ignored(p: Path, ignore: set[str]) -> bool:
    return any(part in ignore for part in p.parts)


def _detect_dir_components(root: Path, ignore: set[str]) -> dict[str, ComponentDef]:
    """Top-level dir conventions → one Component per immediate child of apps/, services/, etc."""
    out: dict[str, ComponentDef] = {}
    for parent in _COMPONENT_PARENT_DIRS:
        parent_dir = root / parent
        if not parent_dir.is_dir():
            continue
        kind = "frontend" if parent == "apps" else (
            "library" if parent in ("packages", "libs", "crates") else "service"
        )
        for child in sorted(parent_dir.iterdir()):
            if not child.is_dir() or _is_ignored(child, ignore):
                continue
            slug = _slug(child.name)
            cid = f"CMP-{slug}"
            if cid in out:
                continue
            out[cid] = ComponentDef(
                id=cid,
                name=child.name,
                kind=kind,
                path=str(child.relative_to(root)),
                detection_source="dir-convention",
            )
    return out


def _detect_docker_components(root: Path, components: dict[str, ComponentDef]) -> None:
    """docker-compose services → Components (skip if dir-convention already added)."""
    candidates = list(root.glob("docker-compose*.y*ml")) + list(root.glob("compose*.y*ml"))
    for compose_path in candidates:
        try:
            text = compose_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Conservative regex: lines like "  service-name:" under "services:"
        in_services = False
        for line in text.splitlines():
            stripped = line.rstrip()
            if stripped.startswith("services:"):
                in_services = True
                continue
            if in_services:
                # Top-level key (no leading space) ends the services block
                if stripped and not line.startswith((" ", "\t")):
                    in_services = False
                    continue
                m = re.match(r"^\s{2}([a-zA-Z0-9_-]+):\s*$", line)
                if m:
                    name = m.group(1)
                    cid = f"CMP-{_slug(name)}"
                    if cid not in components:
                        components[cid] = ComponentDef(
                            id=cid,
                            name=name,
                            kind="service",
                            path=str(compose_path.relative_to(root)),
                            detection_source="docker",
                        )


def _detect_route_components(
    root: Path, paths: list[str], components: dict[str, ComponentDef]
) -> None:
    """Inject tech for Components that own HTTP endpoints."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from parse_codebase_routes import scan_routes
    except ImportError:
        log.debug("parse_codebase_routes unavailable; skipping route attribution")
        return

    routes = scan_routes(paths)
    for r in routes:
        # Walk up the file path until we hit a known Component dir
        rfile = Path(r.file)
        for cid, cmp in components.items():
            if not cmp.path:
                continue
            try:
                rfile.relative_to(cmp.path)
            except ValueError:
                continue
            if r.framework and r.framework not in cmp.tech:
                cmp.tech.append(r.framework)
            break


def _detect_model_components(
    root: Path, paths: list[str], components: dict[str, ComponentDef]
) -> None:
    """Add datastore Components per ORM engine detected (one per engine)."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from parse_codebase_models import scan_models
    except ImportError:
        log.debug("parse_codebase_models unavailable; skipping datastore attribution")
        return

    tables = scan_models(paths)
    engines = sorted({t.framework for t in tables if t.framework})
    for engine in engines:
        cid = f"CMP-{_slug(engine)}"
        if cid in components:
            continue
        components[cid] = ComponentDef(
            id=cid,
            name=engine,
            kind="datastore",
            path="",
            tech=[engine],
            detection_source="models",
        )


def _build_dependency_edges(
    root: Path, components: dict[str, ComponentDef], ignore: set[str]
) -> None:
    """Coarse directory-level imports.

    For each Component with a `path`, scan source files; if any import string
    contains another Component's basename, add the edge.
    """
    by_basename: dict[str, str] = {}
    for cid, cmp in components.items():
        if cmp.path:
            by_basename[Path(cmp.path).name.lower()] = cid

    for cid, cmp in components.items():
        if not cmp.path:
            continue
        cmp_dir = root / cmp.path
        if not cmp_dir.is_dir():
            continue
        seen_deps: set[str] = set()
        for f in cmp_dir.rglob("*"):
            if not f.is_file() or _is_ignored(f, ignore):
                continue
            ext = f.suffix.lower()
            lang = _LANG_BY_EXT.get(ext)
            if lang is None:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in _IMPORT_PATTERNS[lang].finditer(text):
                imp = m.group(1).lower()
                for base, dep_cid in by_basename.items():
                    if dep_cid == cid:
                        continue
                    if base in imp:
                        seen_deps.add(dep_cid)
        cmp.depends_on = sorted(seen_deps)


def scan_components(
    paths: list[str], ignore: set[str] | None = None
) -> list[ComponentDef]:
    """Scan one or more roots; return merged Component list."""
    ignore_set = ignore or _DEFAULT_IGNORES
    out: dict[str, ComponentDef] = {}
    for raw in paths:
        root = Path(raw).resolve()
        if not root.is_dir():
            log.warning("not a directory, skipping: %s", root)
            continue
        out.update(_detect_dir_components(root, ignore_set))
        _detect_docker_components(root, out)
        _detect_route_components(root, [raw], out)
        _detect_model_components(root, [raw], out)
        _build_dependency_edges(root, out, ignore_set)
    return sorted(out.values(), key=lambda c: c.id)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--paths", required=True, help="Comma-separated repo roots")
    p.add_argument("--output", required=True, help="JSON output file")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    paths = [s.strip() for s in args.paths.split(",") if s.strip()]
    components = scan_components(paths)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps([asdict(c) for c in components], indent=2), encoding="utf-8"
    )
    print(f"Detected {len(components)} components -> {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
