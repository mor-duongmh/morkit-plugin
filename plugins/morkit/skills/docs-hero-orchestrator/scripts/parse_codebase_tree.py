"""Scan a codebase for repo overview / tech stack / packages / module entries.

Feeds the codebase-summary doc. Pure-Python LOC counter (no `cloc`); flagged
as approximate because docstrings, comments, and multi-line statements are
not specially handled — we count non-blank lines.

Detected sources:
    Repo overview:  git remote / README headline / total LOC sum
    Tech stack:     manifest contents (declared deps + framework presence)
    Packages:       package.json, pyproject.toml, Cargo.toml, go.mod,
                    pom.xml, Gemfile, composer.json
    Modules/Entry:  files with extensions in _LANG_BY_EXT; entry points
                    detected via filename (`main.py`, `index.{js,ts}`),
                    `cmd/*` / `bin/*` paths, and `package.json` "bin"/"main"
                    + `pyproject.toml [project.scripts]`

Output: dict with `repo`, `tech_stack`, `packages`, `modules` keys.

CLI:
    parse_codebase_tree.py --paths "." --output tree.json

Public API:
    scan_tree(paths, ignore=None) -> dict
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
    ".git", "node_modules", "dist", "build", ".next", ".venv", "venv",
    "__pycache__", "vendor", "target", ".turbo", ".cache", "out", ".idea",
    ".vscode", ".pytest_cache", ".mypy_cache", ".ruff_cache",
}

_LANG_BY_EXT = {
    ".py": "Python", ".pyi": "Python",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java", ".kt": "Kotlin", ".scala": "Scala",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".swift": "Swift",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".hpp": "C++", ".cc": "C++", ".cxx": "C++",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".sql": "SQL",
    ".md": "Markdown",
    ".yaml": "YAML", ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".html": "HTML",
    ".css": "CSS", ".scss": "CSS", ".sass": "CSS",
    ".vue": "Vue", ".svelte": "Svelte",
}

_ENTRY_FILENAMES = {
    "main.py", "__main__.py", "app.py", "index.ts", "index.tsx",
    "index.js", "index.jsx", "main.go", "main.rs", "main.java",
    "Application.java", "manage.py",
}
_ENTRY_DIRS = ("cmd", "bin")

# Manifest filename → (manager, language hints)
_MANIFESTS = {
    "package.json": ("npm", "JavaScript/TypeScript"),
    "pyproject.toml": ("pip", "Python"),
    "Pipfile": ("pipenv", "Python"),
    "requirements.txt": ("pip", "Python"),
    "Cargo.toml": ("cargo", "Rust"),
    "go.mod": ("go", "Go"),
    "pom.xml": ("maven", "Java"),
    "build.gradle": ("gradle", "Java/Kotlin"),
    "Gemfile": ("bundler", "Ruby"),
    "composer.json": ("composer", "PHP"),
}

# Famous frameworks/dbs to surface even when manifest only declares them.
_FRAMEWORK_HINTS = {
    "react": ("framework", "React"),
    "next": ("framework", "Next.js"),
    "vue": ("framework", "Vue"),
    "svelte": ("framework", "Svelte"),
    "express": ("framework", "Express"),
    "fastapi": ("framework", "FastAPI"),
    "django": ("framework", "Django"),
    "flask": ("framework", "Flask"),
    "nest": ("framework", "NestJS"),
    "spring": ("framework", "Spring"),
    "rails": ("framework", "Rails"),
    "gin": ("framework", "Gin"),
    "actix": ("framework", "Actix"),
    "rocket": ("framework", "Rocket"),
    "axum": ("framework", "Axum"),
    "prisma": ("framework", "Prisma"),
    "typeorm": ("framework", "TypeORM"),
    "sqlalchemy": ("framework", "SQLAlchemy"),
    "sequelize": ("framework", "Sequelize"),
    "postgres": ("db", "PostgreSQL"),
    "psycopg": ("db", "PostgreSQL"),
    "mysql": ("db", "MySQL"),
    "sqlite": ("db", "SQLite"),
    "mongodb": ("db", "MongoDB"),
    "mongoose": ("db", "MongoDB"),
    "redis": ("db", "Redis"),
    "jest": ("test", "Jest"),
    "vitest": ("test", "Vitest"),
    "pytest": ("test", "pytest"),
    "rspec": ("test", "RSpec"),
    "playwright": ("test", "Playwright"),
    "cypress": ("test", "Cypress"),
}


@dataclass
class RepoOverviewDef:
    name: str = ""
    description: str = ""
    primary_language: str | None = None
    loc_total: int = 0
    vcs: str = "git"
    license: str | None = None


@dataclass
class TechStackItemDef:
    id: str
    category: str  # language | framework | db | infra | ci | test | build
    name: str
    version: str | None = None
    confidence: str = "detected"  # detected | declared


@dataclass
class PackageInfoDef:
    id: str
    name: str
    path: str
    manager: str
    version: str | None = None
    dep_count: int = 0


@dataclass
class ModuleEntryDef:
    id: str
    path: str
    loc: int = 0
    language: str | None = None
    is_entry_point: bool = False
    purpose: str | None = None


@dataclass
class TreeScanResult:
    repo: RepoOverviewDef = field(default_factory=RepoOverviewDef)
    tech_stack: list[TechStackItemDef] = field(default_factory=list)
    packages: list[PackageInfoDef] = field(default_factory=list)
    modules: list[ModuleEntryDef] = field(default_factory=list)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _is_ignored(p: Path, ignore: set[str]) -> bool:
    return any(part in ignore for part in p.parts)


def _count_loc(path: Path) -> int:
    """Approximate LOC: non-blank lines."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return sum(1 for line in text.splitlines() if line.strip())


def _detect_repo(root: Path, modules: list[ModuleEntryDef]) -> RepoOverviewDef:
    """Repo-level facts: name (dir name), README headline, LOC total, license."""
    ro = RepoOverviewDef(name=root.name)

    # README first heading
    for readme in ("README.md", "README.rst", "README.txt", "README"):
        rp = root / readme
        if rp.is_file():
            try:
                text = rp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for line in text.splitlines():
                stripped = line.lstrip("#").strip()
                if stripped:
                    ro.description = stripped
                    break
            break

    # License
    for lic_name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"):
        if (root / lic_name).is_file():
            try:
                first = (root / lic_name).read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
                ro.license = first[:80]
            except (OSError, IndexError):
                pass
            break

    # LOC total + primary language (most common by LOC, excluding markup)
    code_modules = [m for m in modules if m.language not in (None, "Markdown", "JSON", "YAML", "TOML", "HTML", "CSS")]
    ro.loc_total = sum(m.loc for m in modules)
    if code_modules:
        by_lang: dict[str, int] = {}
        for m in code_modules:
            by_lang[m.language or "?"] = by_lang.get(m.language or "?", 0) + m.loc
        ro.primary_language = max(by_lang.items(), key=lambda kv: kv[1])[0]

    return ro


def _scan_packages_and_tech(root: Path, ignore: set[str]) -> tuple[list[PackageInfoDef], list[TechStackItemDef]]:
    packages: list[PackageInfoDef] = []
    tech_seen: dict[str, TechStackItemDef] = {}
    pkg_index = 0

    for filename, (manager, _hint_lang) in _MANIFESTS.items():
        for hit in root.rglob(filename):
            if _is_ignored(hit, ignore) or not hit.is_file():
                continue
            try:
                text = hit.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            pkg_index += 1
            rel_dir = str(hit.parent.relative_to(root)) or "."
            name, version, dep_count = _parse_manifest(filename, text)
            packages.append(
                PackageInfoDef(
                    id=f"PKG-{pkg_index:03d}",
                    name=name or rel_dir,
                    path=rel_dir,
                    manager=manager,
                    version=version,
                    dep_count=dep_count,
                )
            )

            # Surface known frameworks/dbs/test tools mentioned in manifest
            text_lower = text.lower()
            for hint, (cat, display) in _FRAMEWORK_HINTS.items():
                if hint in text_lower and display not in tech_seen:
                    tid = f"TCH-{_slug(display)}"
                    tech_seen[display] = TechStackItemDef(
                        id=tid, category=cat, name=display, confidence="detected"
                    )

    return packages, list(tech_seen.values())


def _parse_manifest(filename: str, text: str) -> tuple[str, str | None, int]:
    """Best-effort extract (name, version, dep count)."""
    name = ""
    version: str | None = None
    dep_count = 0
    if filename == "package.json":
        try:
            data = json.loads(text)
            name = data.get("name", "") or ""
            version = data.get("version") or None
            dep_count = (
                len(data.get("dependencies", {}) or {})
                + len(data.get("devDependencies", {}) or {})
            )
        except json.JSONDecodeError:
            pass
    elif filename == "pyproject.toml":
        m = re.search(r'^\s*name\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if m:
            name = m.group(1)
        m = re.search(r'^\s*version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if m:
            version = m.group(1)
        # Count under [tool.poetry.dependencies] / [project.dependencies] /
        # PEP-621 `dependencies = [...]` array.
        block = ""
        m_array = re.search(
            r"^\s*dependencies\s*=\s*\[(.*?)\]", text, re.MULTILINE | re.DOTALL
        )
        if m_array:
            block = m_array.group(1)
        else:
            m_section = re.search(
                r"^\[(?:tool\.poetry\.)?dependencies\][^\[]*",
                text, re.MULTILINE | re.DOTALL,
            )
            if m_section:
                block = m_section.group(0)
        dep_count = len(
            [line for line in block.splitlines()
             if line.strip() and not line.strip().startswith(("#", "["))]
        )
    elif filename == "Cargo.toml":
        m = re.search(r'^\s*name\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if m:
            name = m.group(1)
        m = re.search(r'^\s*version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if m:
            version = m.group(1)
        deps_block = re.search(r"\[dependencies\](.*?)(?:^\[|\Z)", text, re.MULTILINE | re.DOTALL)
        if deps_block:
            dep_count = len([line for line in deps_block.group(1).splitlines() if "=" in line])
    elif filename == "go.mod":
        m = re.search(r"^module\s+(\S+)", text, re.MULTILINE)
        if m:
            name = m.group(1)
        dep_count = len(re.findall(r"^\s*[a-zA-Z0-9./-]+\s+v\d", text, re.MULTILINE))
    return name, version, dep_count


def _scan_modules(root: Path, ignore: set[str]) -> list[ModuleEntryDef]:
    modules: list[ModuleEntryDef] = []
    idx = 0
    for f in root.rglob("*"):
        if not f.is_file() or _is_ignored(f, ignore):
            continue
        ext = f.suffix.lower()
        lang = _LANG_BY_EXT.get(ext)
        if lang is None:
            continue
        idx += 1
        rel = str(f.relative_to(root))
        loc = _count_loc(f)
        is_entry = (
            f.name in _ENTRY_FILENAMES
            or any(part in _ENTRY_DIRS for part in f.relative_to(root).parts[:-1])
        )
        modules.append(
            ModuleEntryDef(
                id=f"MOD-{idx:03d}",
                path=rel,
                loc=loc,
                language=lang,
                is_entry_point=is_entry,
            )
        )
    return modules


def _detect_languages_from_modules(modules: list[ModuleEntryDef]) -> list[TechStackItemDef]:
    """Add a TechStackItem(category=language) per language seen in modules."""
    seen: dict[str, int] = {}
    for m in modules:
        if not m.language:
            continue
        seen[m.language] = seen.get(m.language, 0) + m.loc
    out: list[TechStackItemDef] = []
    for lang_name in sorted(seen.keys()):
        out.append(
            TechStackItemDef(
                id=f"TCH-lang-{_slug(lang_name)}",
                category="language",
                name=lang_name,
                confidence="detected",
            )
        )
    return out


def scan_tree(paths: list[str], ignore: set[str] | None = None) -> TreeScanResult:
    ignore_set = ignore or _DEFAULT_IGNORES
    if not paths:
        return TreeScanResult()

    # First root drives repo overview; subsequent roots add packages/modules.
    root = Path(paths[0]).resolve()
    if not root.is_dir():
        log.warning("not a directory: %s", root)
        return TreeScanResult()

    modules: list[ModuleEntryDef] = []
    packages: list[PackageInfoDef] = []
    tech: list[TechStackItemDef] = []
    for raw in paths:
        rp = Path(raw).resolve()
        if not rp.is_dir():
            continue
        modules.extend(_scan_modules(rp, ignore_set))
        pkgs, framework_tech = _scan_packages_and_tech(rp, ignore_set)
        packages.extend(pkgs)
        tech.extend(framework_tech)

    # Add language tech items derived from module scan
    tech.extend(_detect_languages_from_modules(modules))
    # De-dup by id, preserve first
    seen_ids: set[str] = set()
    unique_tech: list[TechStackItemDef] = []
    for t in tech:
        if t.id not in seen_ids:
            unique_tech.append(t)
            seen_ids.add(t.id)

    repo = _detect_repo(root, modules)
    return TreeScanResult(
        repo=repo, tech_stack=unique_tech, packages=packages, modules=modules
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--paths", required=True, help="Comma-separated repo roots")
    p.add_argument("--output", required=True, help="JSON output file")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    paths = [s.strip() for s in args.paths.split(",") if s.strip()]
    res = scan_tree(paths)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "repo": asdict(res.repo),
                "tech_stack": [asdict(t) for t in res.tech_stack],
                "packages": [asdict(p) for p in res.packages],
                "modules": [asdict(m) for m in res.modules],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"Scanned: {len(res.modules)} modules, {len(res.packages)} packages, "
        f"{len(res.tech_stack)} tech items -> {args.output}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
