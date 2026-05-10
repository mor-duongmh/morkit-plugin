"""Pydantic models for ProjectModel + Delta — single source of truth.

Validates and serializes the normalized data shared by all parsers and renderers.
Preserves unknown fields via `extra="allow"` (per phase-02 decision Q4).

Public API:
    ProjectModel — top-level container for all entities
    Delta        — list of changes (ADD / UPDATE / DEPRECATE)
    load_project_model(path) -> ProjectModel
    save_project_model(model, path)
    load_delta(path) -> Delta
    save_delta(delta, path)
"""
from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# --- Enums ---


class Language(str, Enum):
    JP = "JP"
    EN = "EN"
    VN = "VN"


class Priority(str, Enum):
    HIGH = "High"
    MID = "Mid"
    LOW = "Low"
    # MoSCoW (BrSE template uses these labels alongside High/Mid/Low)
    MUST = "Must"
    SHOULD = "Should"
    COULD = "Could"
    WONT = "Won't"


class Status(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class DocStatus(str, Enum):
    """Document workflow status (per Section 0.2 of SRS template)."""

    DRAFT = "Draft"
    IN_REVIEW = "In Review"
    REVIEWED = "Reviewed"
    APPROVED = "Approved"
    DEFERRED = "Deferred"


class ImplStatus(str, Enum):
    """Implementation progress for an FR / Endpoint / Screen.

    Distinct from DocStatus (which tracks doc-review state). Surfaces
    in SRS § 3 so BrSE/PM can see at a glance which functions are done
    vs still on paper.
    """

    NOT_STARTED = "NotStarted"
    IN_PROGRESS = "InProgress"
    DONE = "Done"
    VERIFIED = "Verified"  # Done + has passing tests
    BLOCKED = "Blocked"


# --- Common base ---


class _Base(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=False)


class SourceRef(_Base):
    origin: Literal[
        "openspec", "pdf", "excel", "docx", "codebase", "plan", "manual", "codebase-sync"
    ]
    file_path: Optional[str] = None
    line_range: Optional[tuple[int, int]] = None
    openspec_change_id: Optional[str] = None


class EvidenceRef(_Base):
    """Pointer to evidence backing an ImplStatus claim."""

    kind: Literal["openspec", "commit", "test", "code", "manual"]
    ref: str  # change-id, commit SHA, file path, etc.
    note: Optional[str] = None


class _Entity(_Base):
    """Base for all ID-anchored entities."""

    id: str
    status: Status = Status.ACTIVE
    source: Optional[SourceRef] = None
    hash: Optional[str] = None  # Computed at render time


# --- Meta ---


class ProjectMeta(_Base):
    project_name: str
    version: str = "1.0"
    date: Optional[str] = None
    language: Language = Language.EN
    brse_name: Optional[str] = None
    customer: Optional[str] = None
    release_name: Optional[str] = None
    doc_status: Optional[DocStatus] = None
    baseline_date: Optional[str] = None
    reviewer: Optional[str] = None


class Stakeholder(_Base):
    role: str
    name: Optional[str] = None
    organization: Optional[str] = None
    concern: Optional[str] = None
    approval_authority: Optional[bool] = None


class Reference(_Base):
    """SRS §1.6 reference document entry (REF-001)."""

    id: str  # REF-001
    document: str = ""
    version_or_date: Optional[str] = None
    owner: Optional[str] = None
    notes: Optional[str] = None


class TargetRelease(_Base):
    """SRS §1.3 target release context."""

    release_name: Optional[str] = None
    target_date: Optional[str] = None
    target_environment: Optional[str] = None  # Dev / Staging / Production
    target_users: Optional[str] = None


class OpenQuestion(_Base):
    """SRS §1.4.4 / §12 open question (Q-001)."""

    id: str  # Q-001
    date: Optional[str] = None
    category: Optional[str] = None  # Scope / FR / NFR / Data / UI / Interface / Ops
    topic: Optional[str] = None
    question: str = ""
    answer: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[str] = None
    q_status: Literal["Open", "Answered", "Closed"] = "Open"
    related_id: Optional[str] = None


class Overview(_Base):
    purpose: str = ""
    background: str = ""
    target_release: Optional[TargetRelease] = None
    in_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    future_scope: list[str] = Field(default_factory=list)
    pending_questions: list[OpenQuestion] = Field(default_factory=list)
    stakeholders: list[Stakeholder] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)


class UseCase(_Base):
    """SRS §2.4 / §2.5 use case (UC-001).

    Basic fields (id/name/actor/summary) keep backwards compat;
    extended fields populate §2.5 detail block.
    """

    id: str  # UC-001
    name: str
    actor: str
    summary: str = ""
    # Extended (§2.5)
    trigger: Optional[str] = None
    main_success_scenario: list[str] = Field(default_factory=list)
    exception: Optional[str] = None
    related_fr: list[str] = Field(default_factory=list)
    priority: Priority = Priority.MID
    goal: Optional[str] = None
    precondition: Optional[str] = None
    postcondition: Optional[str] = None
    related_screen: Optional[str] = None
    alternate_scenarios: list[str] = Field(default_factory=list)
    exception_scenarios: list[str] = Field(default_factory=list)


class Issue(_Base):
    """SRS §2.2 current issue (ISSUE-001)."""

    id: str  # ISSUE-001
    issue: str = ""
    impact: Literal["High", "Mid", "Low"] = "Mid"
    related_process: Optional[str] = None
    owner: Optional[str] = None


class BusinessFlow(_Base):
    current_process: str = ""
    # Legacy plain-string list kept for backwards compat;
    # new structured list lives in `issue_records`.
    issues: list[str] = Field(default_factory=list)
    issue_records: list[Issue] = Field(default_factory=list)
    to_be_mermaid: str = ""
    use_cases: list[UseCase] = Field(default_factory=list)


# --- Requirements ---


class ValidationRule(_Base):
    """FR §3.2 validation rule row."""

    field: str
    rule: str = ""
    error_message: Optional[str] = None
    timing: Optional[str] = None  # Input / Submit / Import / Batch


class ExceptionFlow(_Base):
    """FR §3.2 exception flow row (EF-001)."""

    id: str  # EF-001
    error_condition: str = ""
    system_behavior: Optional[str] = None
    user_message: Optional[str] = None
    log_required: Optional[bool] = None


class PermissionEntry(_Base):
    """FR §3.2 / §5.2 permission row (per role)."""

    role: str
    fr_id: Optional[str] = None
    screen: Optional[str] = None
    view: Optional[bool] = None
    create: Optional[bool] = None
    update: Optional[bool] = None
    delete: Optional[bool] = None
    approve: Optional[bool] = None
    export: Optional[bool] = None
    import_: Optional[bool] = Field(default=None, alias="import")
    notes: Optional[str] = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class AuditLogEntry(_Base):
    """FR §3.2 audit log row."""

    event: str
    logged_items: Optional[str] = None
    retention: Optional[str] = None
    related_nfr: list[str] = Field(default_factory=list)


class TestViewpoints(_Base):
    """FR §3.2 test viewpoints block."""

    normal: Optional[str] = None
    boundary: Optional[str] = None
    exception: Optional[str] = None
    permission: Optional[str] = None


class FunctionalRequirement(_Entity):
    id: str = Field(pattern=r"^FR-[A-Z0-9_-]+$")
    name: str
    summary: Optional[str] = None
    description: str = ""
    precondition: Optional[str] = None
    trigger: Optional[str] = None
    main_flow: list[str] = Field(default_factory=list)
    alt_flow: Optional[str] = None
    alt_flows: list[str] = Field(default_factory=list)  # AF-001, AF-002, ...
    exception_flows: list[ExceptionFlow] = Field(default_factory=list)
    business_rules: list[str] = Field(default_factory=list)  # BR-NNN refs
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    permissions: list[PermissionEntry] = Field(default_factory=list)
    audit_logs: list[AuditLogEntry] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)  # AC-NNN refs
    test_viewpoints: Optional[TestViewpoints] = None
    notes: list[str] = Field(default_factory=list)
    postcondition: Optional[str] = None
    related_uc: list[str] = Field(default_factory=list)
    related_screens: list[str] = Field(default_factory=list)
    related_data: list[str] = Field(default_factory=list)
    related_interfaces: list[str] = Field(default_factory=list)
    related_nfr: list[str] = Field(default_factory=list)
    related_test_cases: list[str] = Field(default_factory=list)
    role: Optional[str] = None
    owner: Optional[str] = None
    doc_status: Optional[DocStatus] = None
    priority: Priority = Priority.MID
    impl_status: ImplStatus = ImplStatus.NOT_STARTED
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


# IPA-aligned NFR categories (template §6.1)
NFR_CATEGORIES = (
    "Availability",
    "Performance",  # legacy
    "Performance & Scalability",
    "Operations & Maintainability",
    "Migration",
    "Security",
    "System Environment & Ecology",
    "Scalability",  # legacy
    "Operations",  # legacy
    "Other",
)


class NonFunctionalRequirement(_Entity):
    id: str = Field(pattern=r"^NFR-[A-Z0-9_-]+$")
    category: Literal[
        "Availability",
        "Performance",
        "Performance & Scalability",
        "Operations & Maintainability",
        "Migration",
        "Security",
        "System Environment & Ecology",
        "Scalability",
        "Operations",
        "Other",
    ] = "Other"
    requirement: str = ""
    metric: Optional[str] = None
    measurement_condition: Optional[str] = None
    priority: Priority = Priority.MID
    owner: Optional[str] = None
    doc_status: Optional[DocStatus] = None


class SecurityPiiItem(_Base):
    """SRS §6.2 security/PII row."""

    item: str  # Authentication / Authorization / Encryption / Audit log / ...
    requirement: str = ""
    related_data: list[str] = Field(default_factory=list)
    related_fr: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class BusinessRule(_Entity):
    """SRS §4 business rule (BR-001)."""

    id: str = Field(pattern=r"^BR-[A-Z0-9_-]+$")
    rule: str = ""
    related_fr: list[str] = Field(default_factory=list)
    priority: Priority = Priority.MID
    owner: Optional[str] = None
    notes: Optional[str] = None


class Role(_Entity):
    """SRS §5.1 role definition (ROLE-001)."""

    id: str = Field(pattern=r"^ROLE-[A-Z0-9_-]+$")
    name: str
    description: Optional[str] = None
    user_type: Optional[str] = None  # Internal / Customer / Partner / Admin
    notes: Optional[str] = None


# --- Screen ---


class MockupRef(_Base):
    type: Literal["image", "figma", "ascii", "ai-generated", "missing"] = "ascii"
    path: Optional[str] = None
    annotated_path: Optional[str] = None
    image_hash: Optional[str] = None  # For drift detection (phase-04 Q3)
    url: Optional[str] = None
    description: str = ""
    layout_ascii: Optional[str] = None


class ScreenItem(_Base):
    """One numbered item on a screen mockup (input / output / button / etc)."""

    number: int
    label: str
    kind: Literal["input", "button", "label", "output", "table", "chart", "link"]
    type: Optional[str] = None  # text, password, submit, etc.
    bbox: Optional[list[float]] = None  # [x_pct, y_pct, w_pct, h_pct]
    required: Optional[bool] = None
    notes: Optional[str] = None
    validation: Optional[str] = None
    api_call: Optional[str] = None
    error_code: Optional[str] = None


class Transition(_Base):
    trigger: str
    from_screen: str
    to_screen: str
    condition: Optional[str] = None
    method: Optional[str] = None


class Screen(_Entity):
    id: str = Field(pattern=r"^SCREEN-[A-Z0-9_-]+$")
    slug: str
    name: str
    related_fr: list[str] = Field(default_factory=list)
    role: str = "user"
    url_path: Optional[str] = None
    parent_screen: Optional[str] = None
    children_screens: list[str] = Field(default_factory=list)
    priority: Priority = Priority.MID
    mockup: Optional[MockupRef] = None
    items: list[ScreenItem] = Field(default_factory=list)
    transitions: list[Transition] = Field(default_factory=list)
    business_logic: dict[str, list[str]] = Field(default_factory=dict)
    test_considerations: list[str] = Field(default_factory=list)


# --- Data + Interfaces ---


class EntityDef(_Entity):
    """SRS §7.1 main entity (ENT-001) — business meaning index."""

    id: str = Field(pattern=r"^ENT-[A-Z0-9_-]+$")
    entity: str  # table / object name
    business_meaning: Optional[str] = None
    owner: Optional[str] = None
    notes: Optional[str] = None


class DataItem(_Entity):
    id: str = Field(pattern=r"^DATA-[A-Z0-9_-]+$")
    entity: str  # e.g. "users"
    field_name: str
    field_type: str
    business_meaning: Optional[str] = None
    example: Optional[str] = None
    length: Optional[int] = None
    nullable: bool = False
    validation: Optional[str] = None
    constraint: Optional[str] = None
    pii: Optional[bool] = None
    data_source: Optional[str] = None  # System / User input / External
    update_timing: Optional[str] = None
    notes: Optional[str] = None


class DataRetention(_Base):
    """SRS §7.3 retention row."""

    data_or_entity: str
    retention_period: Optional[str] = None
    deletion_trigger: Optional[str] = None
    backup_handling: Optional[str] = None
    compliance_notes: Optional[str] = None


class ExternalInterface(_Entity):
    id: str = Field(pattern=r"^INT-[A-Z0-9_-]+$")
    name: str
    type: Literal["REST", "GraphQL", "File", "DB", "Message", "Webhook", "Other"] = "REST"
    direction: Optional[Literal["Inbound", "Outbound"]] = None
    target: Optional[str] = None
    summary: str = ""
    method: Optional[str] = None
    endpoint_path: Optional[str] = None
    protocol: Optional[str] = None  # HTTPS / SFTP / JDBC
    auth: Optional[str] = None
    format: Optional[str] = None  # JSON / CSV / XML / Fixed-length
    timing: Optional[str] = None  # Real-time / Batch / Manual
    retry: Optional[str] = None
    timeout: Optional[str] = None
    error_handling: Optional[str] = None
    owner: Optional[str] = None
    related_fr: list[str] = Field(default_factory=list)
    # File interface §8.1
    file_name_pattern: Optional[str] = None
    charset: Optional[str] = None
    delimiter: Optional[str] = None
    header: Optional[bool] = None
    compression: Optional[str] = None
    duplicate_handling: Optional[str] = None
    archive_rule: Optional[str] = None


class ReportItem(_Base):
    """SRS §9.1 report/file output field."""

    no: int
    output_field: str
    source_data: Optional[str] = None
    format: Optional[str] = None
    required: Optional[bool] = None
    sort_or_group: Optional[str] = None
    notes: Optional[str] = None


class Report(_Entity):
    """SRS §9 report or file output (RPT-001)."""

    id: str = Field(pattern=r"^RPT-[A-Z0-9_-]+$")
    name: str
    type: Optional[str] = None  # Report / CSV Export / PDF / Excel / Print
    output_format: Optional[str] = None  # CSV / PDF / XLSX
    trigger: Optional[str] = None  # Manual / Batch / Event
    target_user: Optional[str] = None
    data_source: Optional[str] = None
    layout_spec: Optional[str] = None
    related_fr: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    items: list[ReportItem] = Field(default_factory=list)


class AcceptanceCriterion(_Entity):
    """SRS §10.1 acceptance criterion (AC-001), Given/When/Then."""

    id: str = Field(pattern=r"^AC-[A-Z0-9_-]+$")
    criterion: str = ""
    related_fr: list[str] = Field(default_factory=list)
    related_uc: list[str] = Field(default_factory=list)
    related_test_cases: list[str] = Field(default_factory=list)
    owner: Optional[str] = None
    doc_status: Optional[DocStatus] = None


class UatCriterion(_Base):
    """SRS §10.2 UAT exit criterion."""

    id: str  # UAT-001
    criterion: str = ""
    target: Optional[str] = None
    measurement: Optional[str] = None
    owner: Optional[str] = None


class TraceabilityRow(_Base):
    """SRS §11 traceability row (FR-keyed)."""

    fr_id: str
    uc_id: Optional[str] = None
    br_id: Optional[str] = None
    screen_id: Optional[str] = None
    data_id: Optional[str] = None
    int_id: Optional[str] = None
    nfr_id: Optional[str] = None
    rpt_id: Optional[str] = None
    ac_id: Optional[str] = None
    test_case_id: Optional[str] = None
    doc_status: Optional[DocStatus] = None


class Constraint(_Base):
    """SRS §13.1 constraint (CONS-001)."""

    id: str  # CONS-001
    category: Optional[str] = None  # Tech / Ops / Compliance / Schedule / Budget
    constraint: str = ""
    impact: Optional[str] = None
    owner: Optional[str] = None


class Assumption(_Base):
    """SRS §13.2 assumption (ASM-001)."""

    id: str  # ASM-001
    assumption: str = ""
    impact_if_false: Optional[str] = None
    owner: Optional[str] = None
    validation_method: Optional[str] = None


# --- Database ---


class Column(_Base):
    name: str
    type: str
    is_pk: bool = False
    is_fk: bool = False
    is_unique: bool = False
    nullable: bool = True
    default: Optional[str] = None
    constraint: Optional[str] = None
    references: Optional[str] = None  # "users.id"
    description: Optional[str] = None


class Table(_Entity):
    id: str = Field(pattern=r"^TBL-[A-Z0-9_-]+$")
    name: str
    purpose: Optional[str] = None
    related_fr: list[str] = Field(default_factory=list)
    related_data: list[str] = Field(default_factory=list)
    columns: list[Column] = Field(default_factory=list)


class Index(_Entity):
    id: str = Field(pattern=r"^IDX-[A-Z0-9_-]+$")
    table: str
    columns: list[str]
    type: str = "B-tree"
    unique: bool = False
    where_clause: Optional[str] = None
    purpose: Optional[str] = None


class Relationship(_Entity):
    id: str = Field(pattern=r"^REL-[A-Z0-9_-]+$")
    parent_table: str
    child_table: str
    type: Literal["1:1", "1:N", "N:1", "N:N", "1:0..1"] = "1:N"
    on_delete: Literal["CASCADE", "RESTRICT", "SET_NULL", "NO_ACTION"] = "RESTRICT"
    on_update: Literal["CASCADE", "RESTRICT", "SET_NULL", "NO_ACTION"] = "CASCADE"
    label: Optional[str] = None


class EnumValue(_Base):
    value: str
    meaning: str = ""


class Enum_(_Entity):
    id: str = Field(pattern=r"^ENUM-[A-Za-z0-9_-]+$")
    name: str
    values: list[EnumValue] = Field(default_factory=list)


class Database(_Base):
    engine: str = "PostgreSQL"
    overview: str = ""
    tables: list[Table] = Field(default_factory=list)
    indexes: list[Index] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    enums: list[Enum_] = Field(default_factory=list)


# --- API ---


class AuthConfig(_Base):
    type: Literal["Bearer", "OAuth2", "OIDC", "ApiKey", "Basic", "None"] = "Bearer"
    description: Optional[str] = None
    token_url: Optional[str] = None
    scopes: list[str] = Field(default_factory=list)


class Parameter(_Base):
    name: str
    type: str
    required: bool = False
    default: Optional[str] = None
    description: Optional[str] = None


class Endpoint(_Entity):
    id: str  # ENDPOINT-METHOD-path-slug
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
    path: str
    description: str = ""
    auth_required: bool = True
    related_fr: list[str] = Field(default_factory=list)
    path_params: list[Parameter] = Field(default_factory=list)
    query_params: list[Parameter] = Field(default_factory=list)
    request_headers: list[Parameter] = Field(default_factory=list)
    request_body_schema: Optional[dict[str, Any]] = None
    request_body_example: Optional[dict[str, Any]] = None
    response_schemas: dict[str, dict[str, Any]] = Field(default_factory=dict)  # status -> schema
    response_examples: dict[str, dict[str, Any]] = Field(default_factory=dict)
    error_codes: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ErrorCode(_Entity):
    id: str  # ERR-CODE_NAME
    code: str
    http_status: int
    description: str = ""


class Webhook(_Entity):
    id: str  # WEBHOOK-event-name
    event: str
    description: str = ""
    payload_schema: Optional[dict[str, Any]] = None


class RateLimit(_Base):
    tier: str
    limit: int
    window: str  # "1 min", "1 hour"


class ApiSpec(_Base):
    base_url: Optional[str] = None
    version: str = "1.0"
    overview: str = ""
    auth: Optional[AuthConfig] = None
    endpoints: list[Endpoint] = Field(default_factory=list)
    error_codes: list[ErrorCode] = Field(default_factory=list)
    webhooks: list[Webhook] = Field(default_factory=list)
    rate_limits: list[RateLimit] = Field(default_factory=list)


# --- Misc ---


class GlossaryEntry(_Base):
    term_jp: Optional[str] = None
    term_en: Optional[str] = None
    term_vn: Optional[str] = None
    definition: str = ""


class Risk(_Base):
    id: Optional[str] = None  # RISK-001 (added in template-updated)
    description: str
    impact: Literal["High", "Mid", "Low"] = "Mid"
    likelihood: Literal["High", "Mid", "Low"] = "Mid"
    mitigation: Optional[str] = None
    owner: Optional[str] = None
    risk_status: Literal["Open", "Monitoring", "Closed"] = "Open"


class ConstraintsRisks(_Base):
    # Legacy free-text lists kept for backwards compat.
    technical: list[str] = Field(default_factory=list)
    operational: list[str] = Field(default_factory=list)
    compliance: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    # New structured lists (template §13).
    constraint_records: list[Constraint] = Field(default_factory=list)
    assumption_records: list[Assumption] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)


# --- System Architecture (arc42-lite) ---


class Component(_Entity):
    """Building block in the system — service / library / app / etc.

    Used by `generate-system-architecture` (arc42 §5 Building Block View).
    `depends_on` references other Component IDs to drive the Mermaid graph.
    """

    id: str = Field(pattern=r"^CMP-[A-Z0-9_-]+$")
    name: str
    kind: Literal[
        "service", "library", "app", "frontend", "worker", "datastore", "external"
    ] = "service"
    path: Optional[str] = None
    responsibility: str = ""
    tech: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)  # CMP-NNN refs


class Layer(_Entity):
    """Logical grouping of Components (e.g. presentation / domain / data)."""

    id: str = Field(pattern=r"^LAY-[A-Z0-9_-]+$")
    name: str
    description: str = ""
    component_ids: list[str] = Field(default_factory=list)  # CMP-NNN refs


class Interaction(_Entity):
    """Edge in the runtime view (arc42 §6) — protocol-tagged Component → Component."""

    id: str = Field(pattern=r"^INX-[A-Z0-9_-]+$")
    from_id: str  # CMP-NNN
    to_id: str  # CMP-NNN
    protocol: Literal["http", "grpc", "queue", "db", "fs", "internal"] = "http"
    description: str = ""


class QualityGoal(_Entity):
    """arc42 §1.2 quality goal (e.g. "high availability", "low latency")."""

    id: str = Field(pattern=r"^QG-[A-Z0-9_-]+$")
    name: str
    priority: Priority = Priority.MID
    description: str = ""


# --- Code Standards ---


class LintConfig(_Entity):
    """Detected lint/format tool config (eslint, ruff, prettier, ...)."""

    id: str = Field(pattern=r"^LNT-[A-Z0-9_-]+$")
    tool: str
    config_path: str
    rules_summary: dict[str, str] = Field(default_factory=dict)
    extends: list[str] = Field(default_factory=list)


class NamingConvention(_Entity):
    """Single naming rule for a code-element scope."""

    id: str = Field(pattern=r"^NAM-[A-Z0-9_-]+$")
    scope: Literal["file", "class", "function", "var", "const", "branch"] = "var"
    pattern: str = ""
    example: str = ""


class CommitPolicy(_Entity):
    """Conventional Commits / gitmoji / custom commit-message policy."""

    id: str = Field(pattern=r"^CMT-[A-Z0-9_-]+$")
    style: Literal["conventional", "gitmoji", "custom"] = "conventional"
    allowed_types: list[str] = Field(default_factory=list)
    scope_required: bool = False
    example: str = ""


class FormattingRule(_Entity):
    """One key-value formatting setting (e.g. ruff line-length=100)."""

    id: str = Field(pattern=r"^FMT-[A-Z0-9_-]+$")
    tool: str
    option: str
    value: str
    source_path: Optional[str] = None


# --- Codebase Summary ---


class RepoOverview(_Entity):
    """Singleton — top-level repo facts. Always uses ID `RPO-001`."""

    id: str = Field(default="RPO-001", pattern=r"^RPO-001$")
    name: str = ""
    description: str = ""
    primary_language: Optional[str] = None
    loc_total: int = 0
    vcs: str = "git"
    license: Optional[str] = None


class TechStackItem(_Entity):
    """One detected/declared tech-stack entry."""

    id: str = Field(pattern=r"^TCH-[A-Z0-9_-]+$")
    category: Literal[
        "language", "framework", "db", "infra", "ci", "test", "build"
    ] = "framework"
    name: str = ""
    version: Optional[str] = None
    confidence: Literal["detected", "declared"] = "detected"


class PackageInfo(_Entity):
    """One package/workspace (npm/pip/cargo/go/maven/gem)."""

    id: str = Field(pattern=r"^PKG-[A-Z0-9_-]+$")
    name: str = ""
    path: str = ""
    manager: str = ""
    version: Optional[str] = None
    dep_count: int = 0


class ModuleEntry(_Entity):
    """One module/file in the codebase summary."""

    id: str = Field(pattern=r"^MOD-[A-Z0-9_-]+$")
    path: str = ""
    loc: int = 0
    language: Optional[str] = None
    is_entry_point: bool = False
    purpose: Optional[str] = None


# --- Design Guidelines ---


class DesignPrinciple(_Entity):
    """High-level design principle (e.g. "fail fast", "single source of truth")."""

    id: str = Field(pattern=r"^DPR-[A-Z0-9_-]+$")
    name: str
    statement: str = ""
    rationale: str = ""
    examples: list[str] = Field(default_factory=list)


class PatternGuideline(_Entity):
    """A pattern (creational/structural/behavioral/arch/domain) with usage guidance."""

    id: str = Field(pattern=r"^PTN-[A-Z0-9_-]+$")
    name: str
    category: Literal[
        "creational", "structural", "behavioral", "arch", "domain"
    ] = "arch"
    when_to_use: str = ""
    when_to_avoid: str = ""


class ADR(_Entity):
    """Architecture Decision Record (MADR-style)."""

    id: str = Field(pattern=r"^ADR-[A-Z0-9_-]+$")
    title: str
    status: Literal["proposed", "accepted", "deprecated", "superseded"] = "accepted"
    date: Optional[str] = None
    context: str = ""
    decision: str = ""
    consequences: str = ""
    superseded_by: Optional[str] = None  # ADR-NNN ref


# --- Top-level ---


class ProjectModel(_Base):
    meta: ProjectMeta
    overview: Overview = Field(default_factory=Overview)
    business_flow: BusinessFlow = Field(default_factory=BusinessFlow)
    functional_requirements: list[FunctionalRequirement] = Field(default_factory=list)
    business_rules: list[BusinessRule] = Field(default_factory=list)
    roles: list[Role] = Field(default_factory=list)
    permission_matrix: list[PermissionEntry] = Field(default_factory=list)
    non_functional_requirements: list[NonFunctionalRequirement] = Field(default_factory=list)
    security_pii: list[SecurityPiiItem] = Field(default_factory=list)
    entities: list[EntityDef] = Field(default_factory=list)
    screens: list[Screen] = Field(default_factory=list)
    data_items: list[DataItem] = Field(default_factory=list)
    data_retention: list[DataRetention] = Field(default_factory=list)
    external_interfaces: list[ExternalInterface] = Field(default_factory=list)
    reports: list[Report] = Field(default_factory=list)
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    uat_criteria: list[UatCriterion] = Field(default_factory=list)
    traceability: list[TraceabilityRow] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)
    database: Database = Field(default_factory=Database)
    api: ApiSpec = Field(default_factory=ApiSpec)
    constraints_risks: ConstraintsRisks = Field(default_factory=ConstraintsRisks)
    glossary: list[GlossaryEntry] = Field(default_factory=list)
    # System Architecture (arc42-lite)
    components: list[Component] = Field(default_factory=list)
    layers: list[Layer] = Field(default_factory=list)
    interactions: list[Interaction] = Field(default_factory=list)
    quality_goals: list[QualityGoal] = Field(default_factory=list)
    # Code Standards
    lint_configs: list[LintConfig] = Field(default_factory=list)
    naming_conventions: list[NamingConvention] = Field(default_factory=list)
    commit_policies: list[CommitPolicy] = Field(default_factory=list)
    formatting_rules: list[FormattingRule] = Field(default_factory=list)
    # Codebase Summary
    repo_overview: Optional[RepoOverview] = None  # singleton RPO-001
    tech_stack: list[TechStackItem] = Field(default_factory=list)
    packages: list[PackageInfo] = Field(default_factory=list)
    modules: list[ModuleEntry] = Field(default_factory=list)
    # Design Guidelines
    design_principles: list[DesignPrinciple] = Field(default_factory=list)
    pattern_guidelines: list[PatternGuideline] = Field(default_factory=list)
    adrs: list[ADR] = Field(default_factory=list)


# --- Delta ---


class Change(_Base):
    op: Literal["ADD", "UPDATE", "DEPRECATE"]
    entity_type: Literal[
        # SRS core
        "FR", "NFR", "SCREEN", "DATA", "INT",
        # SRS extended (template-updated)
        "UC", "BR", "ROLE", "ENT", "RPT", "AC", "ISSUE", "CONS", "ASM", "Q", "REF", "RISK",
        # DB
        "TABLE", "INDEX", "REL", "ENUM",
        # API
        "ENDPOINT", "ERROR_CODE", "WEBHOOK", "AUTH_CONFIG", "RATE_LIMIT",
        # System Architecture
        "CMP", "LAY", "INX", "QG",
        # Code Standards
        "LNT", "NAM", "CMT", "FMT",
        # Codebase Summary
        "RPO", "TCH", "PKG", "MOD",
        # Design Guidelines
        "DPR", "PTN", "ADR",
    ]
    entity_id: str
    payload: Optional[dict[str, Any]] = None
    reason: Optional[str] = None


class Delta(_Base):
    source_type: Literal["openspec", "plan", "codebase-sync"]
    source_path: str
    changes: list[Change] = Field(default_factory=list)


# --- IO helpers ---


def load_project_model(path: str | Path) -> ProjectModel:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ProjectModel.model_validate(data)


def save_project_model(model: ProjectModel, path: str | Path) -> None:
    Path(path).write_text(
        model.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
    )


def load_delta(path: str | Path) -> Delta:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Delta.model_validate(data)


def save_delta(delta: Delta, path: str | Path) -> None:
    Path(path).write_text(
        delta.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
    )
