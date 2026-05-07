"""Scan a codebase for HTTP API endpoints.

Supported frameworks (regex-based, conservative):
    Express (JS/TS)   — app.METHOD('/path', handler), router.METHOD(...)
    NestJS            — @Get('/path'), @Post('/path') decorators
    FastAPI           — @app.get('/path'), @router.post(...)
    Django REST       — path('...', view), urlpatterns
    Spring Boot       — @GetMapping('/path'), @PostMapping(...)
    Gin (Go)          — r.GET("/path", handler)
    Rails             — routes.rb resources/get/post

Output: list of EndpointDef dicts saved as JSON.

CLI:
    parse-codebase-routes.py --paths "src/api,src/routes" --output routes.json

Public API:
    scan_routes(paths, ignore=None) -> list[dict]
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

# Default ignored directories
_DEFAULT_IGNORES = {".git", "node_modules", "dist", "build", ".next", ".venv", "__pycache__", "vendor"}


@dataclass
class EndpointDef:
    method: str
    path: str
    handler: str = ""
    file: str = ""
    line: int = 0
    framework: str = "unknown"
    auth_required: bool = False
    notes: str = ""

    def key(self) -> tuple[str, str]:
        return (self.method.upper(), _normalize_path(self.path))


# --- Patterns per framework ---

# Express / Express-like (JS/TS): app.get('/x', ...), router.post('...', ...)
_EXPRESS = re.compile(
    r"\b(app|router|api)\s*\.\s*(get|post|put|patch|delete|all|head|options)\s*\(\s*"
    r"['\"`]([^'\"`]+)['\"`]"
    r"(?:[^)]*?)\)",
    re.IGNORECASE,
)

# NestJS decorators: @Get('/path'), @Post('path'), @Get(), with optional path
_NESTJS_DECO = re.compile(
    r"@(Get|Post|Put|Patch|Delete|Head|Options|All)\s*\(\s*"
    r"(?:['\"`]([^'\"`]+)['\"`])?\s*\)",
    re.IGNORECASE,
)
_NESTJS_CONTROLLER = re.compile(
    r"@Controller\s*\(\s*(?:['\"`]([^'\"`]+)['\"`])?\s*\)"
)

# FastAPI: @app.get('/path'), @router.post('/path', ...)
_FASTAPI = re.compile(
    r"@(?:app|router|api)\s*\.\s*(get|post|put|patch|delete|head|options)\s*\(\s*"
    r"['\"]([^'\"]+)['\"]"
)

# Django: path('users/<int:id>/', view) or url(r'^users/(?P<id>\d+)/$', view)
_DJANGO_PATH = re.compile(
    r"\bpath\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*([\w\.]+)"
)
_DJANGO_RE_PATH = re.compile(
    r"\bre_path\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*([\w\.]+)"
)

# Spring Boot: @GetMapping("/path"), @RequestMapping(value="/path", method=GET)
_SPRING_MAPPING = re.compile(
    r"@(Get|Post|Put|Patch|Delete|RequestMapping)Mapping\s*\(\s*"
    r"(?:value\s*=\s*)?['\"]([^'\"]+)['\"]"
)

# Gin (Go): r.GET("/path", handler), router.POST(...)
_GIN = re.compile(
    r"\b\w+\s*\.\s*(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|Any)\s*\(\s*"
    r"['\"`]([^'\"`]+)['\"`]"
)

# Rails routes.rb: get '/path', to: 'controller#action' OR resources :users
_RAILS_VERB = re.compile(
    r"^\s*(get|post|put|patch|delete)\s+['\"]([^'\"]+)['\"]"
)
_RAILS_RESOURCES = re.compile(r"^\s*resources?\s+:(\w+)")

# Auth-detection hints (decorators / middleware)
_AUTH_HINTS = re.compile(
    r"(?:@(?:UseGuards|AuthGuard|PreAuthorize|Authorize|protected)\b)"
    r"|"
    r"(?:\b(?:requireAuth|isAuthenticated|jwt_required|login_required|"
    r"authenticate|auth_required|verify_token)\b)",
    re.IGNORECASE,
)


def _normalize_path(path: str) -> str:
    """Normalize path: trim trailing slash, normalize param syntax to {name}."""
    p = path.strip().rstrip("/") or "/"
    # Django <int:id> → {id} (must run BEFORE generic ":name" pattern)
    p = re.sub(r"<\w+:(\w+)>", r"{\1}", p)
    # Django <id> → {id}
    p = re.sub(r"<(\w+)>", r"{\1}", p)
    # Express :id, Rails :id → {id}
    p = re.sub(r":(\w+)", r"{\1}", p)
    return p


def _check_auth_nearby(lines: list[str], line_idx: int, window: int = 3) -> bool:
    """Look ±window lines around line_idx for auth decorators / middleware names."""
    start = max(0, line_idx - window)
    end = min(len(lines), line_idx + window + 1)
    for i in range(start, end):
        if _AUTH_HINTS.search(lines[i]):
            return True
    return False


def _detect_framework(file_path: Path, content: str) -> str:
    """Coarse framework hint based on imports / file extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".prisma":
        return "prisma"
    if suffix in {".ts", ".js", ".tsx", ".jsx"}:
        if "@nestjs/common" in content or "@Controller" in content:
            return "nestjs"
        if "express" in content:
            return "express"
        return "express"
    if suffix == ".py":
        if "fastapi" in content.lower() or "from fastapi" in content:
            return "fastapi"
        if "django" in content.lower() or "urlpatterns" in content:
            return "django"
        return "fastapi"
    if suffix == ".java" or suffix == ".kt":
        return "spring"
    if suffix == ".go":
        return "gin"
    if suffix == ".rb":
        return "rails"
    return "unknown"


def _scan_file(file_path: Path) -> list[EndpointDef]:
    """Run all framework detectors, deduplicate by (method, normalized_path)."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        log.warning("read failed %s: %s", file_path, exc)
        return []

    lines = content.splitlines()
    framework = _detect_framework(file_path, content)
    endpoints: list[EndpointDef] = []
    seen: set[tuple[str, str]] = set()

    def add(ep: EndpointDef) -> None:
        k = ep.key()
        if k in seen:
            return
        seen.add(k)
        ep.path = _normalize_path(ep.path)
        endpoints.append(ep)

    # Find @Controller prefix for NestJS
    controller_prefix = ""
    if framework == "nestjs":
        m = _NESTJS_CONTROLLER.search(content)
        if m and m.group(1):
            controller_prefix = "/" + m.group(1).strip("/")

    # Express / NestJS / FastAPI / Spring / Gin / Rails / Django
    detectors: list[tuple[re.Pattern, str]] = []
    if framework in {"express", "unknown"} and file_path.suffix.lower() in {".js", ".ts", ".tsx", ".jsx"}:
        detectors.append((_EXPRESS, "express"))
    if framework == "nestjs":
        detectors.append((_NESTJS_DECO, "nestjs"))
    if framework == "fastapi":
        detectors.append((_FASTAPI, "fastapi"))
    if framework == "spring":
        detectors.append((_SPRING_MAPPING, "spring"))
    if framework == "gin":
        detectors.append((_GIN, "gin"))

    for pattern, fw_name in detectors:
        for m in pattern.finditer(content):
            line_no = content.count("\n", 0, m.start()) + 1
            line_idx = line_no - 1
            if fw_name == "express":
                method, path = m.group(2), m.group(3)
            elif fw_name == "nestjs":
                method = m.group(1)
                path = m.group(2) or ""
                if controller_prefix:
                    path = controller_prefix + ("/" + path.lstrip("/") if path else "")
                if not path:
                    path = controller_prefix or "/"
            elif fw_name == "fastapi":
                method, path = m.group(1), m.group(2)
            elif fw_name == "spring":
                verb = m.group(1)
                if verb.lower() == "request":
                    method = "GET"  # default
                else:
                    method = verb
                path = m.group(2)
            elif fw_name == "gin":
                method, path = m.group(1), m.group(2)
            else:
                continue

            ep = EndpointDef(
                method=method.upper(),
                path=path,
                file=str(file_path),
                line=line_no,
                framework=fw_name,
                auth_required=_check_auth_nearby(lines, line_idx),
            )
            add(ep)

    # Django path()
    if framework == "django" or (file_path.name in {"urls.py"}):
        for pattern in (_DJANGO_PATH, _DJANGO_RE_PATH):
            for m in pattern.finditer(content):
                line_no = content.count("\n", 0, m.start()) + 1
                add(
                    EndpointDef(
                        method="GET",  # Django path() doesn't bind to method
                        path="/" + m.group(1).lstrip("/"),
                        handler=m.group(2),
                        file=str(file_path),
                        line=line_no,
                        framework="django",
                        notes="django path; method varies by view",
                    )
                )

    # Rails routes.rb
    if framework == "rails" or file_path.name == "routes.rb":
        for line_no, line in enumerate(lines, start=1):
            m = _RAILS_VERB.match(line)
            if m:
                add(
                    EndpointDef(
                        method=m.group(1).upper(),
                        path="/" + m.group(2).lstrip("/"),
                        file=str(file_path),
                        line=line_no,
                        framework="rails",
                    )
                )
                continue
            m = _RAILS_RESOURCES.match(line)
            if m:
                resource = m.group(1)
                # Standard CRUD routes for resources
                for method, suffix in [
                    ("GET", ""),
                    ("POST", ""),
                    ("GET", "/{id}"),
                    ("PUT", "/{id}"),
                    ("PATCH", "/{id}"),
                    ("DELETE", "/{id}"),
                ]:
                    add(
                        EndpointDef(
                            method=method,
                            path=f"/{resource}{suffix}",
                            file=str(file_path),
                            line=line_no,
                            framework="rails",
                            notes="from resources :{}".format(resource),
                        )
                    )

    return endpoints


def scan_routes(paths: list[str | Path], ignore: set[str] | None = None) -> list[EndpointDef]:
    """Walk paths recursively, return all detected endpoints (deduped)."""
    ignore = (ignore or set()) | _DEFAULT_IGNORES
    endpoints: list[EndpointDef] = []
    seen: set[tuple[str, str]] = set()

    valid_exts = {".js", ".ts", ".tsx", ".jsx", ".py", ".java", ".kt", ".go", ".rb"}

    for raw in paths:
        root = Path(raw)
        if not root.exists():
            log.warning("path not found: %s", root)
            continue
        if root.is_file():
            files = [root]
        else:
            files = []
            for f in root.rglob("*"):
                if not f.is_file():
                    continue
                if any(part in ignore for part in f.parts):
                    continue
                if f.suffix.lower() in valid_exts:
                    files.append(f)
        for file_path in files:
            for ep in _scan_file(file_path):
                k = ep.key()
                if k in seen:
                    continue
                seen.add(k)
                endpoints.append(ep)
    return endpoints


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--paths", required=True, help="Comma-separated paths")
    p.add_argument("--output", required=True)
    args = p.parse_args()

    paths = [s.strip() for s in args.paths.split(",") if s.strip()]
    endpoints = scan_routes(paths)
    Path(args.output).write_text(
        json.dumps([asdict(ep) for ep in endpoints], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        f"Found {len(endpoints)} endpoints across {len(paths)} paths -> {args.output}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
