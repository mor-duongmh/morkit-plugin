"""Tests for generate-codebase-summary sub-skill + parse_codebase_tree scanner."""
from __future__ import annotations

import sys
from pathlib import Path

_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))

_SUM = Path(__file__).resolve().parents[2] / "generate-codebase-summary" / "scripts"
sys.path.insert(0, str(_SUM))

from codebase_summary_sync_apply import parse_proposal  # noqa: E402
from codebase_summary_sync_propose import (  # noqa: E402
    diff_simple_ids,
    parse_existing_ids,
    render_proposal,
)
from lib.normalized_schema import (  # noqa: E402
    Language,
    ModuleEntry,
    PackageInfo,
    ProjectMeta,
    ProjectModel,
    RepoOverview,
    TechStackItem,
)
from parse_codebase_tree import (  # noqa: E402
    ModuleEntryDef,
    PackageInfoDef,
    TechStackItemDef,
    scan_tree,
)
from render_codebase_summary import render_codebase_summary  # noqa: E402


def _build_minimal_summary_model() -> ProjectModel:
    return ProjectModel(
        meta=ProjectMeta(project_name="TestSum", version="1.0"),
        repo_overview=RepoOverview(
            name="testsum",
            description="A test project",
            primary_language="Python",
            loc_total=12345,
            license="MIT",
        ),
        tech_stack=[
            TechStackItem(id="TCH-lang-python", category="language", name="Python", confidence="detected"),
            TechStackItem(id="TCH-fastapi", category="framework", name="FastAPI", version="0.115.0", confidence="declared"),
        ],
        packages=[
            PackageInfo(id="PKG-001", name="testsum", path=".", manager="pip", version="1.0", dep_count=12),
        ],
        modules=[
            ModuleEntry(id="MOD-001", path="src/main.py", loc=120, language="Python", is_entry_point=True),
            ModuleEntry(id="MOD-002", path="src/util.py", loc=45, language="Python"),
        ],
    )


# --- Renderer ---


def test_render_summary_top_sections():
    model = _build_minimal_summary_model()
    text = render_codebase_summary(model, Language.EN)
    assert text.startswith("# Codebase Summary — TestSum")
    for heading in (
        "## 1. What is this repo",
        "## 2. Tech Stack",
        "## 3. Repository Layout",
        "## 4. Packages / Workspaces",
        "## 5. Entry Points",
        "## 6. LOC by Language",
        "## 7. Build & Run quickstart",
    ):
        assert heading in text, f"missing {heading!r}"
    # Approximate-LOC disclaimer must appear
    assert "approximate" in text.lower()
    # Tech-stack subsections appear when category present
    assert "### Languages" in text
    assert "### Frameworks" in text
    # IDs surface
    assert "PKG-001" in text
    assert "MOD-001" in text
    # Singleton overview pulled
    assert "12,345" in text  # formatted LOC
    assert "MIT" in text


def test_render_summary_empty_model_uses_placeholders():
    pm = ProjectModel(meta=ProjectMeta(project_name="Empty"))
    text = render_codebase_summary(pm, Language.EN)
    assert "| PKG-001 | _TBD_" in text
    assert "| MOD-001 | _TBD_" in text


def test_render_summary_jp_title():
    model = _build_minimal_summary_model()
    text = render_codebase_summary(model, Language.JP)
    assert text.startswith("# コードベース概要")


def test_render_summary_loc_table_only_counts_entry_modules_separately():
    model = _build_minimal_summary_model()
    text = render_codebase_summary(model, Language.EN)
    # Total LOC row in §6 should reflect both modules
    assert "**165**" in text or "165" in text  # 120 + 45


# --- Scanner ---


def test_scan_tree_detects_languages_and_loc(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (tmp_path / "src" / "lib.py").write_text("X = 1\n", encoding="utf-8")
    (tmp_path / "ui").mkdir()
    (tmp_path / "ui" / "app.tsx").write_text("export const App = () => null;\n", encoding="utf-8")

    res = scan_tree([str(tmp_path)])
    langs = {t.name for t in res.tech_stack if t.category == "language"}
    assert "Python" in langs
    assert "TypeScript" in langs
    # main.py is detected as entry point
    entry = next((m for m in res.modules if m.path == "src/main.py"), None)
    assert entry is not None
    assert entry.is_entry_point is True
    # LOC total is sum of non-blank lines
    assert res.repo.loc_total == sum(m.loc for m in res.modules)


def test_scan_tree_detects_packages_from_package_json(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"name": "test-pkg", "version": "1.2.3", "dependencies": {"react": "^18", "axios": "^1"}}',
        encoding="utf-8",
    )
    res = scan_tree([str(tmp_path)])
    assert len(res.packages) == 1
    p = res.packages[0]
    assert p.name == "test-pkg"
    assert p.version == "1.2.3"
    assert p.dep_count == 2
    # Famous frameworks should surface in tech_stack via FRAMEWORK_HINTS
    fw = {t.name for t in res.tech_stack if t.category == "framework"}
    assert "React" in fw


def test_scan_tree_ignores_node_modules_and_venv(tmp_path):
    nm = tmp_path / "node_modules" / "x"
    nm.mkdir(parents=True)
    (nm / "package.json").write_text('{"name": "ignored"}', encoding="utf-8")
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "ignored.py").write_text("X = 1", encoding="utf-8")

    res = scan_tree([str(tmp_path)])
    assert res.packages == []
    assert res.modules == []


def test_scan_tree_repo_overview_from_readme_and_license(tmp_path):
    (tmp_path / "README.md").write_text("# my-repo\n\nA cool thing.\n", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT License\n\nCopyright (c) 2026 ...\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("X = 1\n", encoding="utf-8")
    res = scan_tree([str(tmp_path)])
    assert res.repo.name == tmp_path.name
    assert res.repo.description == "my-repo"
    assert res.repo.license is not None
    assert res.repo.primary_language == "Python"


# --- Sync ---


def test_diff_simple_ids():
    add, dep = diff_simple_ids({"A", "B", "C"}, {"B", "D"})
    assert add == ["A", "C"]
    assert dep == ["D"]


def test_render_summary_proposal_has_sections(tmp_path):
    pkg = PackageInfoDef(id="PKG-001", name="x", path=".", manager="pip", dep_count=3)
    tch = TechStackItemDef(id="TCH-fastapi", category="framework", name="FastAPI")
    mod = ModuleEntryDef(id="MOD-001", path="src/main.py", loc=10, language="Python", is_entry_point=True)
    text = render_proposal(
        [str(tmp_path)], tmp_path / "doc.md",
        [pkg], ["PKG-old"], [tch], [], [mod], [],
    )
    assert "Packages — ADD (1)" in text
    assert "Packages — DEPRECATE (1)" in text
    assert "Tech Stack — ADD (1)" in text
    assert "Entry Points — ADD (1)" in text
    assert "[ ] ADD PKG-001" in text
    assert "[ ] DEPRECATE PKG-old" in text


def test_parse_summary_proposal_picks_only_checked():
    proposal = (
        "### [x] ADD PKG-001\n- Name: `mypkg`\n- Path: `pkgs/mypkg`\n\n"
        "### [ ] ADD PKG-skipped\n- Name: `nope`\n\n"
        "### [X] ADD TCH-fastapi\n- Name: `FastAPI`\n\n"
        "### [x] DEPRECATE MOD-old\n"
    )
    changes = parse_proposal(proposal)
    by_id = {c.entity_id: c for c in changes}
    assert set(by_id.keys()) == {"PKG-001", "TCH-fastapi", "MOD-old"}
    assert by_id["PKG-001"].entity_type == "PKG"
    assert by_id["PKG-001"].payload == {"name": "mypkg", "path": "pkgs/mypkg"}
    assert by_id["TCH-fastapi"].entity_type == "TCH"
    assert by_id["MOD-old"].op == "DEPRECATE"


def test_parse_existing_ids_partitions_by_kind(tmp_path):
    doc = tmp_path / "codebase-summary.md"
    doc.write_text(
        "## 4. Packages\n| ID | Name |\n|---|---|\n| PKG-001 | x |\n"
        "## 2. Tech Stack\n| TCH-react | React |\n"
        "## 5. Entry Points\n| MOD-001 | src/main.ts |\n",
        encoding="utf-8",
    )
    ids = parse_existing_ids(doc)
    assert ids["PKG"] == {"PKG-001"}
    assert ids["TCH"] == {"TCH-react"}
    assert ids["MOD"] == {"MOD-001"}
