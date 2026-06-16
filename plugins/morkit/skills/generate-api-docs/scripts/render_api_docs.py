"""Render REST API docs markdown from a ProjectModel JSON.

Generates `docs/api-docs.md` with endpoints grouped by resource (first path segment).
Section IDs (ENDPOINT-METHOD-path-slug, ERR-CODE_NAME, WEBHOOK-event) are emitted as
H3 headings to match the markdown_ast anchor convention used by the diff engine.

CLI:
    render_api_docs.py --project-model {path}.json --language EN --output docs/api-docs.md
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))

from lib.language_pack import Language, t  # noqa: E402
from lib.normalized_schema import (  # noqa: E402
    ApiSpec,
    Endpoint,
    ErrorCode,
    ProjectModel,
    Webhook,
    load_project_model,
)


def _heading(level: int, text: str) -> str:
    return f"{'#' * level} {text}\n\n"


def _path_slug(path: str) -> str:
    """Convert URL path to a slug for section IDs.

    /users           -> users
    /users/{id}      -> users-by-id
    /users/{id}/posts -> users-by-id-posts
    /v1/users        -> v1-users
    """
    parts = []
    for seg in path.strip("/").split("/"):
        if not seg:
            continue
        if seg.startswith("{") and seg.endswith("}"):
            parts.append(f"by-{seg[1:-1].lower()}")
        elif seg.startswith(":"):
            parts.append(f"by-{seg[1:].lower()}")
        else:
            parts.append(seg.lower())
    return "-".join(parts) or "root"


def endpoint_section_id(ep: Endpoint) -> str:
    return f"ENDPOINT-{ep.method.upper()}-{_path_slug(ep.path)}"


def derive_resource_name(path: str) -> str:
    """First non-version path segment, capitalized. /users/{id} -> 'Users'."""
    for seg in path.strip("/").split("/"):
        if not seg:
            continue
        # skip version prefixes like v1, v2
        if seg.lower().startswith("v") and seg[1:].isdigit():
            continue
        if seg.startswith("{") or seg.startswith(":"):
            continue
        return seg.replace("-", " ").replace("_", " ").title()
    return "Misc"


def group_by_resource(endpoints: list[Endpoint]) -> dict[str, list[Endpoint]]:
    grouped: dict[str, list[Endpoint]] = {}
    for ep in endpoints:
        grouped.setdefault(derive_resource_name(ep.path), []).append(ep)
    # Sort each bucket: GET first, then POST/PUT/PATCH/DELETE; shorter paths first
    method_order = {"GET": 0, "POST": 1, "PUT": 2, "PATCH": 3, "DELETE": 4}
    for bucket in grouped.values():
        bucket.sort(key=lambda e: (len(e.path), method_order.get(e.method.upper(), 9), e.path))
    return grouped


def generate_curl(ep: Endpoint, base_url: str) -> str:
    parts = [f'curl -X {ep.method.upper()} "{base_url}{ep.path}"']
    if ep.auth_required:
        parts.append('  -H "Authorization: Bearer $TOKEN"')
    if ep.method.upper() in {"POST", "PUT", "PATCH"}:
        parts.append('  -H "Content-Type: application/json"')
        if ep.request_body_example:
            body = json.dumps(ep.request_body_example, ensure_ascii=False)
            parts.append(f"  -d '{body}'")
    return " \\\n".join(parts)


# --- Renderers ---


def _render_meta(model: ProjectModel, lang: Language) -> str:
    api = model.api
    today = date.today().isoformat()
    auth_type = api.auth.type if api.auth else "Bearer"
    title = "API ドキュメント" if lang == Language.JP else (
        "API Documentation" if lang == Language.EN else "Tài liệu API"
    )
    return (
        f"# {title} — {model.meta.project_name}\n\n"
        f"| Field | Value |\n|---|---|\n"
        f"| Version | {api.version} |\n"
        f"| Base URL | {api.base_url or '-'} |\n"
        f"| Date | {today} |\n"
        f"| Auth | {auth_type} |\n"
        f"| Language | {lang.value} |\n\n"
    )


def _render_overview(api: ApiSpec, lang: Language) -> str:
    out = _heading(2, f"1. {t('overview', lang)}")
    out += (api.overview or "_TBD_") + "\n\n"
    out += (
        "**Conventions:**\n"
        "- All requests/responses are JSON unless noted.\n"
        "- Timestamps: ISO 8601 UTC (`2026-05-03T10:00:00Z`).\n"
        "- IDs: UUID v4 strings.\n"
        "- Pagination: cursor-based (`?cursor=...&limit=20`).\n\n"
    )
    return out


def _render_auth(api: ApiSpec, lang: Language) -> str:
    out = _heading(2, f"2. {t('authentication', lang)}")
    if not api.auth or api.auth.type == "None":
        out += "_No authentication required._\n\n"
        return out
    auth = api.auth
    out += f"- **Type:** {auth.type}\n"
    if auth.description:
        out += f"- **Description:** {auth.description}\n"
    if auth.token_url:
        out += f"- **Token URL:** `{auth.token_url}`\n"
    if auth.scopes:
        out += f"- **Scopes:** {', '.join(auth.scopes)}\n"
    out += "\n```http\nAuthorization: Bearer <ACCESS_TOKEN>\n```\n\n"
    return out


def _render_global_error_codes(error_codes: list[ErrorCode], lang: Language) -> str:
    out = _heading(2, f"3. {t('error_codes', lang)}")
    out += "| Code | HTTP | Description |\n|---|---|---|\n"
    if error_codes:
        for ec in error_codes:
            out += f"| `{ec.code}` | {ec.http_status} | {ec.description or '-'} |\n"
    else:
        out += "| `BAD_REQUEST` | 400 | Validation failed |\n"
        out += "| `UNAUTHORIZED` | 401 | Missing/invalid auth |\n"
        out += "| `FORBIDDEN` | 403 | No permission |\n"
        out += "| `NOT_FOUND` | 404 | Resource not found |\n"
        out += "| `INTERNAL_ERROR` | 500 | Server error |\n"
    out += (
        "\n**Error Response Format:**\n\n"
        "```json\n"
        "{\n"
        '  "code": "ERROR_CODE",\n'
        '  "message": "Human-readable message",\n'
        '  "details": [{"field": "email", "issue": "Invalid format"}],\n'
        '  "request_id": "req_abc123"\n'
        "}\n"
        "```\n\n"
    )
    # Per-code H3 anchors (for diff engine)
    for ec in error_codes:
        out += _heading(3, f"ERR-{ec.code}")
        out += f"- **HTTP:** {ec.http_status}\n"
        if ec.description:
            out += f"- **Description:** {ec.description}\n"
        out += "\n"
    return out


def _render_rate_limits(api: ApiSpec, lang: Language) -> str:
    if not api.rate_limits:
        return ""
    out = _heading(2, f"4. {t('rate_limiting', lang)}")
    out += "| Tier | Limit | Window |\n|---|---|---|\n"
    for rl in api.rate_limits:
        out += f"| {rl.tier} | {rl.limit} | {rl.window} |\n"
    out += "\nHeaders: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.\n\n"
    return out


def _render_param_table(title: str, params: list, lang: Language) -> str:
    if not params:
        return ""
    out = f"**{title}:**\n\n"
    out += "| Name | Type | Required | Default | Description |\n|---|---|---|---|---|\n"
    for p in params:
        req = "Y" if p.required else "N"
        out += f"| {p.name} | {p.type} | {req} | {p.default or '-'} | {p.description or '-'} |\n"
    out += "\n"
    return out


def _render_endpoint(ep: Endpoint, base_url: str, lang: Language) -> str:
    sec_id = endpoint_section_id(ep)
    out = _heading(3, f"{sec_id}: `{ep.method} {ep.path}`")
    if ep.description:
        out += f"{ep.description}\n\n"
    out += f"- **Auth:** {'Required' if ep.auth_required else 'Public'}\n"
    if ep.related_fr:
        out += f"- **Related FR:** {', '.join(ep.related_fr)}\n"
    if ep.notes:
        out += f"- **Notes:** {ep.notes}\n"
    out += "\n"

    out += _render_param_table(t("path_parameters", lang), ep.path_params, lang)
    out += _render_param_table(t("query_parameters", lang), ep.query_params, lang)
    out += _render_param_table(t("request_headers", lang), ep.request_headers, lang)

    if ep.request_body_schema or ep.request_body_example:
        out += f"**{t('request_body', lang)}:**\n\n"
        if ep.request_body_schema:
            out += "Schema:\n```json\n"
            out += json.dumps(ep.request_body_schema, indent=2, ensure_ascii=False)
            out += "\n```\n\n"
        if ep.request_body_example:
            out += "Example:\n```json\n"
            out += json.dumps(ep.request_body_example, indent=2, ensure_ascii=False)
            out += "\n```\n\n"

    if ep.response_schemas or ep.response_examples:
        out += f"**{t('response', lang)}:**\n\n"
        statuses = sorted(set(ep.response_schemas) | set(ep.response_examples))
        for status in statuses:
            out += f"_Status {status}:_\n\n"
            if status in ep.response_schemas:
                out += "```json\n"
                out += json.dumps(ep.response_schemas[status], indent=2, ensure_ascii=False)
                out += "\n```\n\n"
            if status in ep.response_examples:
                out += "Example:\n```json\n"
                out += json.dumps(ep.response_examples[status], indent=2, ensure_ascii=False)
                out += "\n```\n\n"

    if ep.error_codes:
        out += f"**Errors:** {', '.join(f'`{c}`' for c in ep.error_codes)}\n\n"

    out += "**cURL:**\n\n```bash\n" + generate_curl(ep, base_url or "") + "\n```\n\n"
    return out


def _render_endpoints(api: ApiSpec, lang: Language) -> str:
    if not api.endpoints:
        return ""
    out = _heading(2, f"5. {t('endpoints', lang)}")
    grouped = group_by_resource(api.endpoints)
    # Index table
    out += "| Method | Path | Resource | Auth |\n|---|---|---|---|\n"
    for resource, eps in grouped.items():
        for ep in eps:
            auth = "Y" if ep.auth_required else "N"
            out += f"| {ep.method.upper()} | `{ep.path}` | {resource} | {auth} |\n"
    out += "\n"
    # Per-resource sections
    for resource, eps in grouped.items():
        out += _heading(3, f"{resource} Resource")
        for ep in eps:
            out += _render_endpoint(ep, api.base_url or "", lang)
    return out


def _render_webhooks(webhooks: list[Webhook], lang: Language) -> str:
    if not webhooks:
        return ""
    out = _heading(2, f"6. {t('webhooks', lang)}")
    out += "| Event | Description |\n|---|---|\n"
    for w in webhooks:
        out += f"| `{w.event}` | {w.description or '-'} |\n"
    out += "\n"
    for w in webhooks:
        out += _heading(3, w.id)
        out += f"- **Event:** `{w.event}`\n"
        if w.description:
            out += f"- **Description:** {w.description}\n"
        if w.payload_schema:
            out += "\nPayload schema:\n```json\n"
            out += json.dumps(w.payload_schema, indent=2, ensure_ascii=False)
            out += "\n```\n"
        out += "\n"
    out += (
        "**Signature verification:**\n\n"
        "```\nHMAC-SHA256(payload, webhook_secret) == header X-Signature\n```\n\n"
    )
    return out


def _render_revision_history() -> str:
    return (
        "## Revision History\n\n"
        "| Version | Date | Author | Changes |\n"
        "|---|---|---|---|\n"
        f"| 1.0 | {date.today().isoformat()} | docs-hero (auto) | Initial generation |\n"
    )


def render_api_docs(model: ProjectModel, lang: Language) -> str:
    api = model.api
    parts = [
        _render_meta(model, lang),
        _render_overview(api, lang),
        _render_auth(api, lang),
        _render_global_error_codes(api.error_codes, lang),
        _render_rate_limits(api, lang),
        _render_endpoints(api, lang),
        _render_webhooks(api.webhooks, lang),
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
    text = render_api_docs(model, Language(args.language))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Rendered API docs -> {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
