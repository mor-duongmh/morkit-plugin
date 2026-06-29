"""Tests for the generate-srs sub-skill (render_srs, render_screen_spec, annotate_mockup)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from PIL import Image

# Path to orchestrator scripts (for normalized_schema, etc.)
_ORCH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_ORCH))

# Path to generate-srs scripts (sibling skill folder)
_SRS = Path(__file__).resolve().parents[2] / "generate-srs" / "scripts"
sys.path.insert(0, str(_SRS))

from annotate_mockup import AnnotateItem, annotate  # noqa: E402
from lib.normalized_schema import (  # noqa: E402
    DataItem,
    ExternalInterface,
    FunctionalRequirement,
    Language,
    NonFunctionalRequirement,
    Overview,
    Priority,
    ProjectMeta,
    ProjectModel,
    Screen,
    ScreenItem,
    SourceRef,
    Stakeholder,
)
from render_screen_spec import render_screen_spec  # noqa: E402
from render_srs import render_srs  # noqa: E402


def _build_minimal_model() -> ProjectModel:
    return ProjectModel(
        meta=ProjectMeta(project_name="TestApp", version="1.0", brse_name="Phong"),
        overview=Overview(
            purpose="Hệ thống quản lý đặt hàng cho doanh nghiệp.",
            in_scope=["User registration", "Order placement"],
            out_of_scope=["Inventory forecasting"],
            stakeholders=[Stakeholder(role="Customer", name="Acme Co", concern="Reliability")],
        ),
        functional_requirements=[
            FunctionalRequirement(
                id="FR-001",
                name="Login",
                description="User logs in with email + password.",
                main_flow=["Submit creds", "Validate", "Issue session"],
                postcondition="User authenticated",
                related_screens=["SCREEN-001"],
                priority=Priority.HIGH,
                source=SourceRef(origin="manual"),
            ),
            FunctionalRequirement(
                id="FR-002",
                name="Logout",
                description="User logs out.",
                main_flow=["Click logout", "Clear session"],
                related_screens=["SCREEN-001"],
                priority=Priority.MID,
                source=SourceRef(origin="manual"),
            ),
        ],
        non_functional_requirements=[
            NonFunctionalRequirement(
                id="NFR-001",
                category="Performance",
                requirement="Login page must render quickly",
                metric="< 500ms p95",
                source=SourceRef(origin="manual"),
            ),
        ],
        screens=[
            Screen(
                id="SCREEN-001",
                slug="login",
                name="Login Screen",
                related_fr=["FR-001", "FR-002"],
                role="guest",
                url_path="/login",
                items=[
                    ScreenItem(number=1, label="Email", kind="input", type="email", required=True,
                               bbox=[0.1, 0.3, 0.8, 0.05], validation="RFC 5322"),
                    ScreenItem(number=2, label="Password", kind="input", type="password", required=True,
                               bbox=[0.1, 0.4, 0.8, 0.05], validation="min 8 chars"),
                    ScreenItem(number=3, label="Sign In", kind="button", type="submit",
                               bbox=[0.4, 0.55, 0.2, 0.05], api_call="POST /auth/login"),
                ],
                source=SourceRef(origin="manual"),
            ),
        ],
        data_items=[
            DataItem(
                id="DATA-001",
                entity="users",
                field_name="email",
                field_type="VARCHAR",
                length=255,
                nullable=False,
                constraint="UNIQUE",
                source=SourceRef(origin="manual"),
            ),
        ],
        external_interfaces=[
            ExternalInterface(
                id="INT-001",
                name="Auth Service",
                type="REST",
                target="auth-service",
                summary="Validates credentials",
                method="POST",
                endpoint_path="/auth/login",
                source=SourceRef(origin="manual"),
            ),
        ],
    )


# --- render_srs ---


def test_render_srs_includes_all_main_sections():
    model = _build_minimal_model()
    text = render_srs(model, Language.EN)
    assert "TestApp" in text
    assert "FR-001" in text and "FR-002" in text
    assert "NFR-001" in text
    assert "SCREEN-001" in text
    assert "DATA-001" in text
    assert "INT-001" in text


def test_render_srs_jp_uses_japanese_headings():
    model = _build_minimal_model()
    text = render_srs(model, Language.JP)
    assert "ドキュメントの目的" in text  # §1 Document Purpose (was 概要 Overview)
    assert "機能要件" in text
    assert "非機能要件" in text


def test_render_srs_vn_uses_vietnamese_headings():
    model = _build_minimal_model()
    text = render_srs(model, Language.VN)
    assert "Mục đích tài liệu" in text  # §1 (restructured from "Tổng quan")
    assert "Luồng nghiệp vụ" in text
    assert "Yêu cầu chức năng" in text


def test_render_srs_uc_basic_flow_numbered():
    """UC basic flow steps are numbered (FR flows moved into the §2 use cases)."""
    from lib.normalized_schema import UseCase
    model = _build_minimal_model()
    model.business_flow.use_cases = [
        UseCase(id="UC-001", name="Login", actor="End User",
                main_success_scenario=["Submit creds", "Validate", "Issue session"],
                related_fr=["FR-001"])
    ]
    text = render_srs(model, Language.EN)
    assert "1. Submit creds" in text
    assert "2. Validate" in text


def test_render_srs_screen_index_links_to_per_screen_file():
    model = _build_minimal_model()
    text = render_srs(model, Language.EN)
    assert "screen-specs/SCREEN-001-login.md" in text


def test_render_srs_emits_h3_anchors_for_diff_engine():
    """The diff engine relies on H3 headings with FR-NNN/NFR-NNN/SCREEN-NNN IDs.

    §3.2 emits a minimal per-FR stub anchor so `docs-update` can patch FR changes
    incrementally — even though the verbose detail now lives in the §2 use cases.
    """
    model = _build_minimal_model()
    text = render_srs(model, Language.EN)
    assert "### FR-001" in text  # minimal stub anchor (not verbose detail)
    assert "### NFR-001" in text
    assert "### SCREEN-001" in text


# --- template-updated 13-section coverage ---


def test_render_srs_includes_13_sections_and_appendix_a():
    """Restructured SRS has 13 numbered sections + Appendix A (Glossary appendix B removed)."""
    model = _build_minimal_model()
    text = render_srs(model, Language.EN)
    for token in ("## 0.", "## 1.", "## 2.", "## 3.", "## 4.", "## 5.",
                  "## 6.", "## 7.", "## 8.", "## 9.", "## 10.", "## 11.",
                  "## 12.", "## 13.", "## Appendix A:"):
        assert token in text, f"missing section marker: {token!r}"
    # Appendix B Glossary was removed; terminology now lives in §1.5.
    assert "## Appendix B:" not in text


def test_render_srs_business_rule_section_renders():
    from lib.normalized_schema import BusinessRule
    model = _build_minimal_model()
    model.business_rules = [
        BusinessRule(id="BR-001", rule="Order total must be positive", related_fr=["FR-001"])
    ]
    text = render_srs(model, Language.EN)
    assert "BR-001" in text
    assert "Order total must be positive" in text


def test_render_srs_role_and_permission_matrix():
    from lib.normalized_schema import PermissionEntry, Role
    model = _build_minimal_model()
    model.roles = [Role(id="ROLE-001", name="Admin", user_type="Internal")]
    model.permission_matrix = [
        PermissionEntry(role="Admin", fr_id="FR-001", screen="SCREEN-001",
                        view=True, create=True, update=True, delete=False)
    ]
    text = render_srs(model, Language.EN)
    assert "ROLE-001" in text
    assert "Admin" in text
    assert "Permission Matrix" in text


def test_render_srs_acceptance_criteria_section():
    from lib.normalized_schema import AcceptanceCriterion
    model = _build_minimal_model()
    model.acceptance_criteria = [
        AcceptanceCriterion(id="AC-001",
                            criterion="Given valid creds, when login, then session issued",
                            related_fr=["FR-001"])
    ]
    text = render_srs(model, Language.EN)
    assert "AC-001" in text
    assert "session issued" in text


def test_render_srs_report_section():
    from lib.normalized_schema import Report, ReportItem
    model = _build_minimal_model()
    model.reports = [
        Report(id="RPT-001", name="Sales Report", type="CSV Export",
               items=[ReportItem(no=1, output_field="order_id", required=True)])
    ]
    text = render_srs(model, Language.EN)
    assert "RPT-001" in text
    assert "Sales Report" in text
    assert "order_id" in text


def test_render_srs_open_questions():
    from lib.normalized_schema import OpenQuestion
    model = _build_minimal_model()
    model.open_questions = [
        OpenQuestion(id="Q-001", question="Confirm session timeout?",
                     owner="PM", q_status="Open")
    ]
    text = render_srs(model, Language.EN)
    assert "Q-001" in text
    assert "Confirm session timeout?" in text


def test_render_srs_constraints_assumptions_structured():
    from lib.normalized_schema import Assumption, Constraint
    model = _build_minimal_model()
    model.constraints_risks.constraint_records = [
        Constraint(id="CONS-001", category="Tech",
                   constraint="Must run on PostgreSQL 15+", impact="High")
    ]
    model.constraints_risks.assumption_records = [
        Assumption(id="ASM-001", assumption="Stable network",
                   impact_if_false="Login fails")
    ]
    text = render_srs(model, Language.EN)
    assert "CONS-001" in text
    assert "PostgreSQL 15+" in text
    assert "ASM-001" in text


def test_render_srs_traceability_auto_derived_from_fr():
    """When no explicit traceability rows, derive from FR cross-refs."""
    model = _build_minimal_model()
    text = render_srs(model, Language.EN)
    # Section 11 traceability should include FR-001 row with SCREEN-001
    assert "Traceability" in text
    # FR-001 traceability row includes SCREEN-001 cross-ref
    trace_idx = text.find("11.")
    appendix_idx = text.find("Appendix A:")
    trace_block = text[trace_idx:appendix_idx]
    assert "FR-001" in trace_block
    assert "SCREEN-001" in trace_block


def test_render_srs_use_case_detail_section():
    from lib.normalized_schema import UseCase
    model = _build_minimal_model()
    model.business_flow.use_cases = [
        UseCase(id="UC-001", name="User Login", actor="End User",
                trigger="User submits credentials",
                main_success_scenario=["Enter creds", "Submit", "Issue token"],
                related_fr=["FR-001"])
    ]
    text = render_srs(model, Language.EN)
    assert "UC-001" in text
    assert "User Login" in text
    assert "Issue token" in text


def test_render_srs_doc_control_section_present():
    """Section 0 with status + priority definitions."""
    model = _build_minimal_model()
    text = render_srs(model, Language.EN)
    assert "Document Control Rules" in text
    assert "Status Definition" in text
    assert "Priority Definition" in text
    assert "Must" in text and "Should" in text


def test_render_srs_nfr_ipa_category_accepted():
    """NFR with IPA-style 'Performance & Scalability' category renders."""
    from lib.normalized_schema import NonFunctionalRequirement
    model = _build_minimal_model()
    model.non_functional_requirements.append(
        NonFunctionalRequirement(
            id="NFR-002",
            category="Performance & Scalability",
            requirement="Sustain 1000 concurrent users",
            metric="p95 < 200ms",
            measurement_condition="Endpoint /login, peak hour",
        )
    )
    text = render_srs(model, Language.EN)
    assert "NFR-002" in text
    assert "Performance & Scalability" in text
    assert "p95 < 200ms" in text


def test_render_srs_revision_history_includes_reviewer_column():
    """Template-updated revision history adds Reviewer + Approval Status columns."""
    model = _build_minimal_model()
    text = render_srs(model, Language.EN)
    # Check the revision-history table header
    assert "Reviewer" in text
    assert "Approval Status" in text


# --- template restructure: §1 purpose / terminology / actors ---


def test_render_srs_section1_terminology_and_actors_tables():
    """§1 carries a single-language terminology table (with abbreviation) + actors."""
    from lib.normalized_schema import GlossaryEntry, SystemActor
    model = _build_minimal_model()
    model.glossary = [GlossaryEntry(term_vn="Khách hàng", abbreviation="KH", definition="Người mua")]
    model.system_actors = [SystemActor(name="NVTN", description="Người tạo đơn")]
    text = render_srs(model, Language.VN)
    # §1.5 terminology table header (STT | Khái niệm/Thuật ngữ | Viết tắt | Mô tả)
    assert "Thuật ngữ viết tắt" in text
    assert "| STT | Khái niệm/Thuật ngữ | Viết tắt | Mô tả |" in text
    assert "| 1 | Khách hàng | KH | Người mua |" in text
    # §1.6 system actors table
    assert "Đối tượng sử dụng hệ thống" in text
    assert "| NVTN | Người tạo đơn |" in text


def test_render_srs_section1_strengths_and_phases():
    from lib.normalized_schema import DevelopmentPhase
    model = _build_minimal_model()
    model.overview.strengths = ["Tự động hóa"]
    model.overview.development_phases = [
        DevelopmentPhase(phase="Giai đoạn 1", items=["Tạo đơn"]),
        DevelopmentPhase(phase="Giai đoạn 2", items=["Tích điểm"]),
    ]
    text = render_srs(model, Language.VN)
    assert "Điểm mạnh của hệ thống" in text
    assert "Tự động hóa" in text
    assert "**Giai đoạn 1**" in text and "**Giai đoạn 2**" in text


def test_render_srs_uc_detail_has_diagram_and_inline_screens():
    """Each UC detail auto-generates a Mermaid workflow and links its screens inline."""
    from lib.normalized_schema import UseCase
    model = _build_minimal_model()
    model.business_flow.use_cases = [
        UseCase(id="UC-001", name="Login", actor="End User",
                main_success_scenario=["Enter creds", "Submit"],
                business_rules=["BR-001"], related_screens=["SCREEN-001"])
    ]
    text = render_srs(model, Language.EN)
    assert "Use Case Diagram" in text
    assert "flowchart TD" in text and "Start" in text
    # screen linked inline to its per-screen spec
    assert "(./screen-specs/SCREEN-001-login.md)" in text


def test_uc_mermaid_escapes_special_chars():
    """Mermaid label sanitizer keeps the diagram syntactically valid."""
    from lib.normalized_schema import UseCase
    model = _build_minimal_model()
    model.business_flow.use_cases = [
        UseCase(id="UC-001", name="X", actor="A",
                main_success_scenario=['Pick [combo] "x2"', "Confirm | pay"],
                exception_scenarios=["Out of stock"])
    ]
    text = render_srs(model, Language.EN)
    # Inspect only the generated Mermaid block (the UC list table keeps raw text).
    mermaid = text[text.index("flowchart TD"):text.index("```", text.index("flowchart TD"))]
    # special chars replaced inside node labels: [ ] -> ( ), " -> ', | -> /
    assert "N1[\"Pick (combo) 'x2'\"]" in mermaid
    assert "Confirm / pay" in mermaid
    assert '"x2"' not in mermaid  # double quotes downgraded to single inside labels


def test_render_srs_backward_compat_without_new_fields():
    """A ProjectModel lacking the new fields still renders (TBD placeholders)."""
    model = ProjectModel(meta=ProjectMeta(project_name="Legacy"))
    text = render_srs(model, Language.VN)
    assert "Mục đích tài liệu" in text
    assert "Thuật ngữ viết tắt" in text  # table renders with _TBD_ row
    assert "## 3." in text


# --- update-mode safety (FR is table-rendered, not section-patched) ---


def test_srs_roundtrip_preserves_content_byte_identical():
    """parse_doc → serialize_blocks must round-trip the restructured SRS losslessly.

    Guards the update-mode risk: §1 (purpose/terminology/actors) and the §3 FR
    table are non-anchored content; a lossy round-trip would silently drop them.
    """
    from lib.normalized_schema import UseCase, GlossaryEntry, SystemActor
    from lib.markdown_ast import parse_doc, serialize_blocks, split_preamble_postamble
    model = _build_minimal_model()
    model.glossary = [GlossaryEntry(term_vn="Khách hàng", abbreviation="KH", definition="Người mua")]
    model.system_actors = [SystemActor(name="NVTN", description="Tạo đơn")]
    model.business_flow.use_cases = [
        UseCase(id="UC-001", name="Login", actor="User",
                main_success_scenario=["A", "B"], related_screens=["SCREEN-001"])
    ]
    md = render_srs(model, Language.VN)
    blocks = parse_doc(md)
    preamble, postamble = split_preamble_postamble(md, blocks)
    order = sorted(blocks.keys(), key=lambda sid: blocks[sid].line_start)
    rebuilt = serialize_blocks(blocks, order, preamble, postamble)
    assert rebuilt == md, "round-trip dropped or reordered content"
    # the at-risk §1 content survives inside the preamble
    assert "Thuật ngữ viết tắt" in rebuilt
    assert "Đối tượng sử dụng hệ thống" in rebuilt


# --- render_screen_spec ---


def test_render_screen_spec_includes_items_grouped():
    model = _build_minimal_model()
    text = render_screen_spec(model.screens[0], Language.EN)
    assert "Email" in text
    assert "Password" in text
    assert "Sign In" in text
    # Three sections (input/output/action) — at least input + action visible
    assert "🔵" in text
    assert "🟠" in text


def test_render_screen_spec_includes_validation():
    model = _build_minimal_model()
    text = render_screen_spec(model.screens[0], Language.EN)
    assert "RFC 5322" in text
    assert "min 8 chars" in text


def test_render_screen_spec_includes_api_call_for_button():
    model = _build_minimal_model()
    text = render_screen_spec(model.screens[0], Language.EN)
    assert "POST /auth/login" in text


def test_render_screen_spec_jp():
    model = _build_minimal_model()
    text = render_screen_spec(model.screens[0], Language.JP)
    assert "入力項目" in text  # input_items in JP
    assert "アクション" in text  # actions in JP


# --- annotate_mockup ---


def test_annotate_mockup_writes_output_png():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "mockup.png"
        Image.new("RGB", (400, 600), (240, 240, 240)).save(str(src), "PNG")

        items = [
            AnnotateItem(number=1, kind="input", bbox=(0.1, 0.3, 0.8, 0.05)),
            AnnotateItem(number=2, kind="button", bbox=(0.4, 0.55, 0.2, 0.05)),
        ]
        out = Path(td) / "annotated.png"
        annotate(src, items, out)

        assert out.exists()
        # Verify it's a valid PNG
        result = Image.open(str(out))
        assert result.format == "PNG"
        # Size should match original (no resize for small image)
        assert result.size == (400, 600)


def test_annotate_mockup_clamps_bbox_out_of_bounds():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "m.png"
        Image.new("RGB", (200, 200), (255, 255, 255)).save(str(src), "PNG")
        items = [
            AnnotateItem(number=1, kind="input", bbox=(-0.1, 1.5, 0.0, 0.0)),  # out of bounds
        ]
        out = Path(td) / "out.png"
        annotate(src, items, out)
        assert out.exists()  # No crash; clamped


def test_annotate_mockup_handles_overlapping_items():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "m.png"
        Image.new("RGB", (400, 400), (255, 255, 255)).save(str(src), "PNG")
        # Two items same bbox
        items = [
            AnnotateItem(number=1, kind="input", bbox=(0.5, 0.5, 0.0, 0.0)),
            AnnotateItem(number=2, kind="button", bbox=(0.5, 0.5, 0.0, 0.0)),
        ]
        out = Path(td) / "out.png"
        annotate(src, items, out)
        assert out.exists()


def test_annotate_mockup_loads_items_from_json_format():
    """Items JSON format from Claude vision should parse correctly."""
    from annotate_mockup import _load_items

    with tempfile.TemporaryDirectory() as td:
        items_path = Path(td) / "items.json"
        items_path.write_text(json.dumps({
            "screen_id": "SCREEN-001",
            "items": [
                {"number": 1, "label": "Email", "kind": "input", "bbox": [0.1, 0.3, 0.8, 0.05]},
                {"number": 2, "label": "Submit", "kind": "button", "bbox": [0.4, 0.5, 0.2, 0.05]},
            ],
        }))
        loaded = _load_items(items_path)
        assert len(loaded) == 2
        assert loaded[0].number == 1
        assert loaded[0].kind == "input"
