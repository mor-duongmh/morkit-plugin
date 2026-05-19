"""Tests for generate-api-docs sub-skill (render_api_docs, sync propose/apply)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))

_API = Path(__file__).resolve().parents[2] / "generate-api-docs" / "scripts"
sys.path.insert(0, str(_API))

from api_sync_apply import parse_proposal  # noqa: E402
from api_sync_propose import (  # noqa: E402
    diff_endpoints,
    parse_existing_endpoints,
    render_proposal,
)
from lib.normalized_schema import (  # noqa: E402
    ApiSpec,
    AuthConfig,
    Endpoint,
    ErrorCode,
    Language,
    Parameter,
    ProjectMeta,
    ProjectModel,
    Webhook,
)
from parse_codebase_routes import EndpointDef  # noqa: E402
from render_api_docs import (  # noqa: E402
    _path_slug,
    derive_resource_name,
    endpoint_section_id,
    generate_curl,
    group_by_resource,
    render_api_docs,
)


def _build_minimal_api_model() -> ProjectModel:
    return ProjectModel(
        meta=ProjectMeta(project_name="TestAPI", version="1.0"),
        api=ApiSpec(
            base_url="https://api.test.com",
            version="1.0",
            overview="Test API for unit tests.",
            auth=AuthConfig(type="Bearer", description="JWT bearer token"),
            endpoints=[
                Endpoint(
                    id="ENDPOINT-GET-users",
                    method="GET",
                    path="/users",
                    description="List users",
                    auth_required=True,
                    related_fr=["FR-001"],
                    query_params=[
                        Parameter(name="limit", type="int", required=False, default="20"),
                    ],
                ),
                Endpoint(
                    id="ENDPOINT-GET-users-by-id",
                    method="GET",
                    path="/users/{id}",
                    description="Get user by ID",
                    auth_required=True,
                    path_params=[Parameter(name="id", type="UUID", required=True)],
                    response_examples={"200": {"id": "u1", "name": "Alice"}},
                ),
                Endpoint(
                    id="ENDPOINT-POST-users",
                    method="POST",
                    path="/users",
                    description="Create user",
                    auth_required=True,
                    request_body_example={"name": "Bob", "email": "b@x.com"},
                ),
                Endpoint(
                    id="ENDPOINT-GET-orders",
                    method="GET",
                    path="/orders",
                    description="List orders",
                    auth_required=False,
                ),
            ],
            error_codes=[
                ErrorCode(id="ERR-USER_NOT_FOUND", code="USER_NOT_FOUND",
                          http_status=404, description="User does not exist"),
            ],
            webhooks=[
                Webhook(id="WEBHOOK-users-created", event="users.created",
                        description="Fired when a user is created"),
            ],
        ),
    )


# --- _path_slug ---


def test_path_slug_basic():
    assert _path_slug("/users") == "users"


def test_path_slug_with_param():
    assert _path_slug("/users/{id}") == "users-by-id"


def test_path_slug_nested_param():
    assert _path_slug("/users/{userId}/posts") == "users-by-userid-posts"


def test_path_slug_colon_param_django():
    assert _path_slug("/users/:id") == "users-by-id"


def test_path_slug_root():
    assert _path_slug("/") == "root"


# --- derive_resource_name ---


def test_resource_name_skips_version():
    assert derive_resource_name("/v1/users/{id}") == "Users"


def test_resource_name_first_segment():
    assert derive_resource_name("/orders/123") == "Orders"


# --- group_by_resource ---


def test_group_by_resource_separates_users_and_orders():
    model = _build_minimal_api_model()
    grouped = group_by_resource(model.api.endpoints)
    assert "Users" in grouped and "Orders" in grouped
    assert len(grouped["Users"]) == 3
    assert len(grouped["Orders"]) == 1


def test_group_sorts_get_before_post():
    model = _build_minimal_api_model()
    grouped = group_by_resource(model.api.endpoints)
    methods = [ep.method for ep in grouped["Users"]]
    # "/users" GET should come before "/users" POST
    short_path_methods = [ep.method for ep in grouped["Users"] if ep.path == "/users"]
    assert short_path_methods == ["GET", "POST"]


# --- generate_curl ---


def test_curl_get_includes_auth_header():
    ep = Endpoint(id="x", method="GET", path="/users", auth_required=True)
    curl = generate_curl(ep, "https://api.test.com")
    assert 'curl -X GET "https://api.test.com/users"' in curl
    assert "Authorization: Bearer $TOKEN" in curl


def test_curl_post_includes_body():
    ep = Endpoint(
        id="x", method="POST", path="/users", auth_required=True,
        request_body_example={"name": "Alice"},
    )
    curl = generate_curl(ep, "https://api.test.com")
    assert "Content-Type: application/json" in curl
    assert '"name": "Alice"' in curl


def test_curl_public_endpoint_omits_auth():
    ep = Endpoint(id="x", method="GET", path="/health", auth_required=False)
    curl = generate_curl(ep, "")
    assert "Authorization" not in curl


# --- endpoint_section_id ---


def test_endpoint_section_id_format():
    ep = Endpoint(id="ignored", method="DELETE", path="/users/{id}/posts")
    assert endpoint_section_id(ep) == "ENDPOINT-DELETE-users-by-id-posts"


# --- render_api_docs ---


def test_render_includes_main_sections():
    text = render_api_docs(_build_minimal_api_model(), Language.EN)
    assert "API Documentation" in text
    assert "TestAPI" in text
    assert "https://api.test.com" in text
    assert "USER_NOT_FOUND" in text


def test_render_emits_h3_endpoint_anchors():
    """Diff engine relies on H3 ENDPOINT- anchors."""
    text = render_api_docs(_build_minimal_api_model(), Language.EN)
    assert "### ENDPOINT-GET-users" in text
    assert "### ENDPOINT-GET-users-by-id" in text
    assert "### ENDPOINT-POST-users" in text
    assert "### ENDPOINT-GET-orders" in text


def test_render_emits_h3_error_anchors():
    text = render_api_docs(_build_minimal_api_model(), Language.EN)
    assert "### ERR-USER_NOT_FOUND" in text


def test_render_emits_h3_webhook_anchors():
    text = render_api_docs(_build_minimal_api_model(), Language.EN)
    assert "### WEBHOOK-users-created" in text


def test_render_groups_endpoints_under_resource():
    text = render_api_docs(_build_minimal_api_model(), Language.EN)
    assert "Users Resource" in text
    assert "Orders Resource" in text


def test_render_jp_uses_japanese_headings():
    text = render_api_docs(_build_minimal_api_model(), Language.JP)
    assert "概要" in text  # overview
    assert "認証" in text  # authentication
    assert "エンドポイント" in text  # endpoints


def test_render_vn_uses_vietnamese_headings():
    text = render_api_docs(_build_minimal_api_model(), Language.VN)
    assert "Tổng quan" in text
    assert "Xác thực" in text


def test_render_includes_curl_blocks():
    text = render_api_docs(_build_minimal_api_model(), Language.EN)
    assert "curl -X GET" in text
    assert "curl -X POST" in text


def test_render_includes_query_params_table():
    text = render_api_docs(_build_minimal_api_model(), Language.EN)
    assert "limit" in text


# --- sync: parse_existing_endpoints ---


def test_parse_existing_endpoints_extracts_h3_ids():
    with tempfile.TemporaryDirectory() as td:
        doc = Path(td) / "api-docs.md"
        doc.write_text(
            "# API\n\n"
            "### ENDPOINT-GET-users: `GET /users`\n\nbody\n\n"
            "### ENDPOINT-POST-users: `POST /users`\n\nbody\n\n"
            "### ERR-FOO\n",
            encoding="utf-8",
        )
        keys = parse_existing_endpoints(doc)
        assert ("GET", "users") in keys
        assert ("POST", "users") in keys
        assert len(keys) == 2  # ERR not counted as endpoint


def test_parse_existing_endpoints_missing_doc_returns_empty():
    keys = parse_existing_endpoints(Path("/nonexistent/file.md"))
    assert keys == set()


# --- sync: diff_endpoints ---


def test_diff_finds_adds_and_deprecates():
    code = [
        EndpointDef(method="GET", path="/users", framework="express"),
        EndpointDef(method="POST", path="/users", framework="express"),
        EndpointDef(method="GET", path="/health", framework="express"),
    ]
    doc_keys = {("GET", "users"), ("DELETE", "users-by-id")}
    to_add, to_deprecate = diff_endpoints(code, doc_keys)
    add_keys = {(e.method, _path_slug(e.path)) for e in to_add}
    assert ("POST", "users") in add_keys
    assert ("GET", "health") in add_keys
    assert ("DELETE", "users-by-id") in to_deprecate


# --- sync: render_proposal ---


def test_proposal_has_checkbox_per_candidate():
    code = [EndpointDef(method="POST", path="/users", framework="express", file="src/x.ts", line=1)]
    md = render_proposal(["src"], Path("docs/api-docs.md"), code, code, [("DELETE", "old")])
    assert "[ ] ADD ENDPOINT-POST-users" in md
    assert "[ ] DEPRECATE ENDPOINT-DELETE-old" in md


def test_proposal_includes_summary_counts():
    code = [EndpointDef(method="GET", path="/x", framework="express", file="a", line=1)]
    md = render_proposal(["src"], Path("d.md"), code, code, [])
    assert "ADD candidates (1)" in md
    assert "DEPRECATE candidates (0)" in md


# --- sync: parse_proposal (apply step) ---


def test_apply_extracts_only_checked_items():
    proposal = (
        "# Proposal\n\n"
        "### [x] ADD ENDPOINT-GET-users\n"
        "- `GET /users`\n"
        "- Source: `src/x.ts:1`\n"
        "- Auth: required\n\n"
        "### [ ] ADD ENDPOINT-POST-users\n"
        "- `POST /users`\n"
        "- Auth: required\n\n"
        "### [X] DEPRECATE ENDPOINT-DELETE-old\n"
        "- old endpoint\n\n"
    )
    changes = parse_proposal(proposal)
    ids = [c.entity_id for c in changes]
    ops = [c.op for c in changes]
    assert "ENDPOINT-GET-users" in ids
    assert "ENDPOINT-DELETE-old" in ids
    assert "ENDPOINT-POST-users" not in ids  # unchecked
    assert "ADD" in ops and "DEPRECATE" in ops


def test_apply_extracts_method_and_path_payload():
    proposal = (
        "### [x] ADD ENDPOINT-POST-users\n"
        "- `POST /users`\n"
        "- Auth: required\n\n"
    )
    changes = parse_proposal(proposal)
    assert len(changes) == 1
    payload = changes[0].payload or {}
    assert payload.get("method") == "POST"
    assert payload.get("path") == "/users"
    assert payload.get("auth_required") is True


def test_apply_handles_no_checked_items():
    proposal = "### [ ] ADD ENDPOINT-GET-users\n- skipped\n\n"
    changes = parse_proposal(proposal)
    assert changes == []
