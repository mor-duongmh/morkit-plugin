#!/usr/bin/env python3
"""Build morkit docs site (no runtime deps; stdlib only).

Reads:
  - plugins/morkit/skills/<name>/SKILL.md   (frontmatter: name, description)
  - plugins/morkit/commands/<name>.md       (frontmatter: description)

Writes:
  - docs/skills/<name>.html      (one page per skill dir)
  - docs/commands/<name>.html    (one page per command .md)

docs/index.html and docs/docs.html are hand-maintained — never written here.

Idempotent — safe to run multiple times. Overwrites existing files.
Run from repo root:
    python3 docs/_scaffolder/build.py
"""

from __future__ import annotations
import re
import sys
from pathlib import Path

SCAFFOLD_DIR = Path(__file__).resolve().parent
DOCS_DIR     = SCAFFOLD_DIR.parent
REPO_ROOT    = DOCS_DIR.parent
SKILLS_DIR   = REPO_ROOT / "plugins" / "morkit" / "skills"
COMMANDS_DIR = REPO_ROOT / "plugins" / "morkit" / "commands"

sys.path.insert(0, str(SCAFFOLD_DIR))
import content as C            # noqa: E402
import templates as T          # noqa: E402


# ---------------------------------------------------------------- parsing
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.S)


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    out = {}
    block = m.group(1)
    # Naive single-line key: value parser (good enough for {name, description})
    for line in block.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        out[key.strip()] = val
    return out


def read_skill(slug: str) -> dict:
    p = SKILLS_DIR / slug / "SKILL.md"
    if not p.exists():
        return {"name": slug, "description": ""}
    fm = parse_frontmatter(p.read_text(encoding="utf-8"))
    return {"name": fm.get("name", slug), "description": fm.get("description", "")}


def read_command(slug: str) -> dict:
    p = COMMANDS_DIR / f"{slug}.md"
    if not p.exists():
        return {"name": slug, "description": ""}
    fm = parse_frontmatter(p.read_text(encoding="utf-8"))
    # commands typically don't have `name:` in frontmatter — use slug
    return {"name": fm.get("name", slug), "description": fm.get("description", "")}


# ---------------------------------------------------------------- helpers
def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )


def is_deprecated(desc: str, curated: dict) -> bool:
    if curated.get("deprecated"):
        return True
    return desc.strip().lower().startswith("deprecated")


def related_for(kind: str, slug: str) -> list[tuple[str, str, str]]:
    """Return up to 4 related items as (href, title, sub) tuples."""
    group = C.group_of(kind, slug)
    out: list[tuple[str, str, str]] = []
    if group == "misc":
        return out

    kind_vn = {"skills": "skill", "commands": "command"}
    items = C.GROUPS[group]
    # Same-kind siblings first (exclude self)
    for sib in items.get(kind, []):
        if sib == slug:
            continue
        href = f"../{kind}/{sib}.html"
        out.append((href, f"/morkit:{sib}" if kind == "commands" else sib, f"{C.GROUP_LABELS[group]} · {kind_vn[kind]}"))
    # Cross-kind siblings if we have room
    cross_kind = "skills" if kind == "commands" else "commands"
    for sib in items.get(cross_kind, []):
        if len(out) >= 4:
            break
        href = f"../{cross_kind}/{sib}.html"
        out.append((href, f"/morkit:{sib}" if cross_kind == "commands" else sib, f"{C.GROUP_LABELS[group]} · {kind_vn[cross_kind]}"))
    return out[:6]


def fallback_when_to_use(description: str) -> list[str]:
    """Heuristic fallback if no curated bullets supplied."""
    desc = description.strip()
    if not desc:
        return ["Tham khảo mô tả ở phần 'Để làm gì' phía trên."]
    # Try to split on common cue phrases
    parts = re.split(r"(?:Use when|Triggered by|Run once|Run when)\s*", desc, flags=re.I)
    if len(parts) > 1:
        cue = parts[1].split(".")[0].strip()
        if cue:
            return [f"Khi {cue[0].lower()}{cue[1:]}." if cue and cue[0].isupper() else f"Khi {cue}."]
    return ["Tham khảo mô tả ở phần 'Để làm gì' phía trên."]


# ---------------------------------------------------------------- render
def render_one(kind: str, slug: str) -> str:
    """kind: 'skills' | 'commands'"""
    if kind == "skills":
        meta = read_skill(slug)
    else:
        meta = read_command(slug)

    curated = C.CURATED.get(f"{kind}.{slug}", {})
    name = meta["name"] or slug
    description = meta["description"]
    lede = curated.get("lede") or description or f"{name}"
    details = curated.get("details", "")

    deprecated = is_deprecated(description, curated)

    group = C.group_of(kind, slug)
    group_label = C.GROUP_LABELS.get(group, "Khác")

    when_bullets = curated.get("when_to_use") or fallback_when_to_use(description)

    invocation = f"/morkit:{slug}"
    args = curated.get("example_args", "")
    example_note = curated.get("example_note",
                               "Đây là ví dụ minh hoạ — tham khảo SKILL.md để xem cú pháp đầy đủ.")

    related = related_for(kind, slug)
    cards_html = "\n".join(
        f"    {T.related_card_html(href, html_escape(title), html_escape(sub))}"
        for href, title, sub in related
    ) or '    <p class="lede" style="font-size:13px;">(Không có item liên quan trong cùng nhóm.)</p>'

    # `kind` in templates is singular ("skill" / "command")
    page_kind = "skill" if kind == "skills" else "command"
    return T.detail_page(
        kind=page_kind,
        slug=slug,
        name=name,
        lede=html_escape(lede),
        details=details,  # raw HTML allowed (contains <code> spans)
        group_label=group_label,
        deprecated=deprecated,
        when_bullets=[html_escape(b) for b in when_bullets],
        invocation=invocation,
        args=html_escape(args),
        example_note=html_escape(example_note),
        related_cards_html=cards_html,
    )


def main():
    out_skills = DOCS_DIR / "skills"
    out_commands = DOCS_DIR / "commands"
    out_skills.mkdir(parents=True, exist_ok=True)
    out_commands.mkdir(parents=True, exist_ok=True)

    # Discover slugs from filesystem (source of truth).
    # Skip dot-directories (e.g. .pytest_cache, .venv) — they are tooling
    # artifacts, never skills, and would otherwise render a spurious page.
    skill_slugs = sorted(
        p.name for p in SKILLS_DIR.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )
    command_slugs = sorted(p.stem for p in COMMANDS_DIR.glob("*.md"))

    written = 0
    for slug in skill_slugs:
        html = render_one("skills", slug)
        (out_skills / f"{slug}.html").write_text(html, encoding="utf-8")
        written += 1
    for slug in command_slugs:
        html = render_one("commands", slug)
        (out_commands / f"{slug}.html").write_text(html, encoding="utf-8")
        written += 1

    # NOTE: docs/index.html is the hand-maintained "v2 landing" (promoted from the
    # old docs-v2.html). build.py never writes it — doing so would clobber the
    # hand-crafted hub.

    # Cleanup orphans: HTML files in out dirs whose source .md no longer exists
    orphans = []
    for p in out_skills.glob("*.html"):
        if p.stem not in skill_slugs:
            orphans.append(p)
    for p in out_commands.glob("*.html"):
        if p.stem not in command_slugs:
            orphans.append(p)
    for p in orphans:
        p.unlink()

    print(f"Wrote {written} files. ({len(skill_slugs)} skills + {len(command_slugs)} commands)")
    if orphans:
        print(f"Cleaned {len(orphans)} orphan(s): {[str(p.relative_to(REPO_ROOT)) for p in orphans]}")
    print(f"  → {out_skills.relative_to(REPO_ROOT)}/")
    print(f"  → {out_commands.relative_to(REPO_ROOT)}/")
    print(f"  (index.html left untouched — hand-maintained v2 landing)")


if __name__ == "__main__":
    main()
