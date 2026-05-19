"""Render SRS markdown from a ProjectModel JSON.

Generates `docs/srs.md` following the BrSE template-updated standard
(13 main sections + 2 appendices). Uses language_pack for headings.

Section IDs (FR-NNN, NFR-NNN, SCREEN-NNN, DATA-NNN, INT-NNN, BR-NNN, ROLE-NNN,
RPT-NNN, AC-NNN, UC-NNN) are emitted as H3 headings so the diff engine can
anchor on them.

CLI:
    render-srs.py --project-model {path}.json --language JP --output docs/srs.md
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

# Resolve the orchestrator lib (siblings via venv-installed pythonpath OR symlink)
_ORCH_LIB = Path(__file__).resolve().parents[2] / "docs-hero-orchestrator" / "scripts"
sys.path.insert(0, str(_ORCH_LIB))

from lib.language_pack import Language, t  # noqa: E402
from lib.normalized_schema import (  # noqa: E402
    AcceptanceCriterion,
    BusinessRule,
    EntityDef,
    ExternalInterface,
    FunctionalRequirement,
    ImplStatus,
    NonFunctionalRequirement,
    ProjectModel,
    Report,
    Role,
    Screen,
    load_project_model,
)

# Visual badges for ImplStatus in markdown tables. Kept ASCII-friendly so
# rendered SRS stays readable in terminals that don't render emoji.
_IMPL_BADGE = {
    ImplStatus.NOT_STARTED: "⬜ Not Started",
    ImplStatus.IN_PROGRESS: "🟡 In Progress",
    ImplStatus.DONE: "🟢 Done",
    ImplStatus.VERIFIED: "🔵 Verified",
    ImplStatus.BLOCKED: "🔴 Blocked",
}


def _impl_badge(status: ImplStatus | None) -> str:
    return _IMPL_BADGE.get(status or ImplStatus.NOT_STARTED, "⬜ Not Started")

# --- shared helpers ---


def _h(level: int, text: str) -> str:
    return f"{'#' * level} {text}\n\n"


def _yn(v):
    if v is None:
        return "-"
    return "Y" if v else "N"


def _bullets(items: list[str]) -> str:
    return "".join(f"- {x}\n" for x in items)


def _safe(v, default: str = "-") -> str:
    if v is None or v == "":
        return default
    return str(v)


# --- 0. Document Control + Meta ---


def _render_meta(model: ProjectModel, lang: Language) -> str:
    meta = model.meta
    today = meta.date or date.today().isoformat()
    title = "要件定義書" if lang == Language.JP else (
        "Software Requirements Specification" if lang == Language.EN
        else "Tài liệu đặc tả yêu cầu"
    )
    lang_value = lang.value if hasattr(lang, "value") else str(lang)
    rows = [
        f"| Project | {meta.project_name} |",
        f"| Release | {_safe(meta.release_name)} |",
        f"| Version | {meta.version} |",
        f"| Date | {today} |",
        f"| Author | {_safe(meta.brse_name)} |",
        f"| Language | {lang_value} |",
        f"| Status | {_safe(meta.doc_status.value if meta.doc_status else None, 'Draft')} |",
        f"| Baseline Date | {_safe(meta.baseline_date)} |",
    ]
    return f"# {title}\n\n| Field | Value |\n|---|---|\n" + "\n".join(rows) + "\n\n"


def _render_revision_history(model: ProjectModel, lang: Language) -> str:
    out = _h(2, t("revision_history", lang))
    out += "| Version | Date | Author | Changes | Reviewer | Approval Status |\n"
    out += "|---|---|---|---|---|---|\n"
    today = model.meta.date or date.today().isoformat()
    out += (
        f"| {model.meta.version} | {today} | "
        f"{_safe(model.meta.brse_name, 'docs-hero (auto)')} | Initial draft | "
        f"{_safe(model.meta.reviewer)} | "
        f"{_safe(model.meta.doc_status.value if model.meta.doc_status else None, 'Draft')} |\n\n"
    )
    return out


def _render_doc_control(lang: Language) -> str:
    out = _h(2, f"0. {t('doc_control', lang)}")
    out += _h(3, f"0.1 {t('language_rule', lang)}")
    out += "- Final customer-facing output is rendered in ONE language (JP / EN / VN).\n"
    out += "- BrSE working copy may keep multilingual labels.\n\n"
    out += _h(3, f"0.2 {t('status_definition', lang)}")
    out += "| Status | Meaning | Allowed Action |\n|---|---|---|\n"
    out += "| Draft | Under preparation | BrSE / dev internal review |\n"
    out += "| In Review | Under review | Customer / stakeholder review |\n"
    out += "| Reviewed | Reviewed | Minor correction only |\n"
    out += "| Approved | Approved baseline | Change request required for scope change |\n"
    out += "| Deferred | Deferred | Move to future release or backlog |\n\n"
    out += _h(3, f"0.3 {t('priority_definition', lang)}")
    out += "| Priority | Meaning |\n|---|---|\n"
    out += "| Must | Required for release |\n"
    out += "| Should | Important but workaround exists |\n"
    out += "| Could | Nice to have |\n"
    out += "| Won't | Not included in this release |\n\n"
    return out


# --- 1. Overview ---


def _render_overview(model: ProjectModel, lang: Language) -> str:
    ov = model.overview
    out = _h(2, f"1. {t('overview', lang)}")
    out += _h(3, f"1.1 {t('purpose', lang)}")
    out += (ov.purpose or "_TBD_") + "\n\n"
    out += _h(3, f"1.2 {t('background', lang)}")
    out += (ov.background or "_TBD_") + "\n\n"

    out += _h(3, f"1.3 {t('target_release', lang)}")
    tr = ov.target_release
    out += "| Item | Value |\n|---|---|\n"
    out += f"| Release Name | {_safe(tr.release_name if tr else None)} |\n"
    out += f"| Target Date | {_safe(tr.target_date if tr else None)} |\n"
    out += f"| Target Environment | {_safe(tr.target_environment if tr else None)} |\n"
    out += f"| Target Users | {_safe(tr.target_users if tr else None)} |\n\n"

    out += _h(3, f"1.4 {t('scope', lang)}")
    out += _h(4, f"1.4.1 {t('in_scope', lang)}")
    out += (_bullets(ov.in_scope) if ov.in_scope else "- _TBD_\n") + "\n"
    out += _h(4, f"1.4.2 {t('out_of_scope', lang)}")
    out += (_bullets(ov.out_of_scope) if ov.out_of_scope else "- _TBD_\n") + "\n"
    out += _h(4, f"1.4.3 {t('future_scope', lang)}")
    out += (_bullets(ov.future_scope) if ov.future_scope else "- _TBD_\n") + "\n"
    out += _h(4, f"1.4.4 {t('pending_confirmation', lang)}")
    out += "| Q-ID | Topic | Description | Owner | Due Date | Status |\n"
    out += "|---|---|---|---|---|---|\n"
    if ov.pending_questions:
        for q in ov.pending_questions:
            out += (
                f"| {q.id} | {_safe(q.topic)} | {_safe(q.question)} | "
                f"{_safe(q.owner)} | {_safe(q.due_date)} | {q.q_status} |\n"
            )
    else:
        out += "| Q-001 | _TBD_ | _TBD_ | _TBD_ | _TBD_ | Open |\n"
    out += "\n"

    out += _h(3, f"1.5 {t('stakeholders', lang)}")
    out += "| Role | Name | Organization | Concern | Approval Authority |\n"
    out += "|---|---|---|---|---|\n"
    if ov.stakeholders:
        for s in ov.stakeholders:
            auth = "Yes" if s.approval_authority else ("No" if s.approval_authority is False else "-")
            out += f"| {s.role} | {_safe(s.name)} | {_safe(s.organization)} | {_safe(s.concern)} | {auth} |\n"
    else:
        out += "| _TBD_ | _TBD_ | _TBD_ | _TBD_ | - |\n"
    out += "\n"

    out += _h(3, f"1.6 {t('references', lang)}")
    out += "| Ref-ID | Document / Source | Version / Date | Owner | Notes |\n"
    out += "|---|---|---|---|---|\n"
    if ov.references:
        for r in ov.references:
            out += f"| {r.id} | {_safe(r.document)} | {_safe(r.version_or_date)} | {_safe(r.owner)} | {_safe(r.notes)} |\n"
    else:
        out += "| REF-001 | _TBD_ | _TBD_ | _TBD_ | _TBD_ |\n"
    out += "\n"
    return out


# --- 2. Current State & Business Flow ---


def _render_business_flow(model: ProjectModel, lang: Language) -> str:
    bf = model.business_flow
    out = _h(2, f"2. {t('current_business_flow', lang)}")
    out += _h(3, f"2.1 {t('current_process', lang)}")
    out += (bf.current_process or "_TBD_") + "\n\n"

    out += _h(3, f"2.2 {t('issues', lang)}")
    out += "| Issue-ID | Issue | Impact | Related Process | Owner |\n"
    out += "|---|---|---|---|---|\n"
    if bf.issue_records:
        for i in bf.issue_records:
            out += f"| {i.id} | {_safe(i.issue)} | {i.impact} | {_safe(i.related_process)} | {_safe(i.owner)} |\n"
    elif bf.issues:
        # Backwards compat: legacy free-text issues -> auto-numbered.
        for n, txt in enumerate(bf.issues, 1):
            out += f"| ISSUE-{n:03d} | {txt} | - | - | - |\n"
    else:
        out += "| ISSUE-001 | _TBD_ | - | - | - |\n"
    out += "\n"

    if bf.to_be_mermaid:
        out += _h(3, f"2.3 {t('to_be_flow', lang)}")
        out += "```mermaid\n" + bf.to_be_mermaid.strip() + "\n```\n\n"

    out += _h(3, f"2.4 {t('use_cases', lang)}")
    out += (
        "| UC-ID | Use Case | Actor | Trigger | Main Success Scenario | Exception | Related FR | Priority |\n"
        "|---|---|---|---|---|---|---|---|\n"
    )
    if bf.use_cases:
        for uc in bf.use_cases:
            mss = "; ".join(uc.main_success_scenario) if uc.main_success_scenario else _safe(uc.summary)
            out += (
                f"| {uc.id} | {uc.name} | {uc.actor} | {_safe(uc.trigger)} | "
                f"{mss} | {_safe(uc.exception)} | {', '.join(uc.related_fr) or '-'} | "
                f"{uc.priority.value} |\n"
            )
    else:
        out += "| UC-001 | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ | - | - |\n"
    out += "\n"

    if bf.use_cases:
        out += _h(3, f"2.5 {t('use_case_detail', lang)}")
        for uc in bf.use_cases:
            out += _h(4, f"{uc.id}: {uc.name}")
            out += "| Field | Value |\n|---|---|\n"
            out += f"| Actor | {uc.actor} |\n"
            out += f"| Goal | {_safe(uc.goal)} |\n"
            out += f"| Trigger | {_safe(uc.trigger)} |\n"
            out += f"| Pre-condition | {_safe(uc.precondition)} |\n"
            out += f"| Post-condition | {_safe(uc.postcondition)} |\n"
            out += f"| Related FR | {', '.join(uc.related_fr) or '-'} |\n"
            out += f"| Related Screen | {_safe(uc.related_screen)} |\n\n"
            if uc.main_success_scenario:
                out += f"##### {t('main_flow', lang)}\n"
                for n, step in enumerate(uc.main_success_scenario, 1):
                    out += f"{n}. {step}\n"
                out += "\n"
            if uc.alternate_scenarios or uc.exception_scenarios:
                out += "##### Alternate / Exception Scenario\n"
                for n, s in enumerate(uc.alternate_scenarios, 1):
                    out += f"- AS-{n:03d}: {s}\n"
                for n, s in enumerate(uc.exception_scenarios, 1):
                    out += f"- ES-{n:03d}: {s}\n"
                out += "\n"
    return out


# --- 3. Functional Requirements ---


def _render_fr_detail(fr: FunctionalRequirement, lang: Language) -> str:
    out = _h(3, f"{fr.id}: {fr.name}")
    out += "| Field | Value |\n|---|---|\n"
    out += f"| Doc Status | {_safe(fr.doc_status.value if fr.doc_status else None, 'Draft')} |\n"
    out += f"| Impl Status | {_impl_badge(fr.impl_status)} |\n"
    if fr.evidence_refs:
        ev = "; ".join(
            f"{e.kind}:{e.ref}" + (f" ({e.note})" if e.note else "") for e in fr.evidence_refs
        )
        out += f"| Evidence | {ev} |\n"
    out += f"| Priority | {fr.priority.value} |\n"
    out += f"| Source | {_safe(fr.source.origin if fr.source else None)} |\n"
    out += f"| Owner | {_safe(fr.owner)} |\n"
    out += f"| Related UC | {', '.join(fr.related_uc) or '-'} |\n"
    out += f"| Related Screen | {', '.join(fr.related_screens) or '-'} |\n"
    out += f"| Related Data | {', '.join(fr.related_data) or '-'} |\n"
    out += f"| Related Interface | {', '.join(fr.related_interfaces) or '-'} |\n"
    out += f"| Related NFR | {', '.join(fr.related_nfr) or '-'} |\n"
    out += f"| Related Business Rule | {', '.join(fr.business_rules) or '-'} |\n"
    out += f"| Related Test Case | {', '.join(fr.related_test_cases) or '-'} |\n\n"

    out += "##### Overview\n"
    out += (fr.description or "_TBD_") + "\n\n"
    if fr.precondition:
        out += f"##### {t('precondition', lang)}\n- {fr.precondition}\n\n"
    if fr.trigger:
        out += f"##### {t('trigger', lang)}\n- {fr.trigger}\n\n"
    if fr.main_flow:
        out += f"##### {t('main_flow', lang)}\n"
        for i, step in enumerate(fr.main_flow, 1):
            out += f"{i}. {step}\n"
        out += "\n"
    if fr.alt_flows or fr.alt_flow:
        out += f"##### {t('alt_flow', lang)}\n"
        flows = fr.alt_flows or ([fr.alt_flow] if fr.alt_flow else [])
        for i, af in enumerate(flows, 1):
            out += f"- AF-{i:03d}: {af}\n"
        out += "\n"
    if fr.exception_flows:
        out += f"##### {t('exception_flow', lang)}\n"
        out += "| EF-ID | Error / Condition | System Behavior | User Message | Log Required |\n"
        out += "|---|---|---|---|---|\n"
        for ef in fr.exception_flows:
            out += (
                f"| {ef.id} | {_safe(ef.error_condition)} | {_safe(ef.system_behavior)} | "
                f"{_safe(ef.user_message)} | {_yn(ef.log_required)} |\n"
            )
        out += "\n"
    if fr.business_rules:
        out += f"##### {t('business_rules', lang)}\n"
        for br in fr.business_rules:
            out += f"- {br}\n"
        out += "\n"
    if fr.validation_rules:
        out += f"##### {t('validation_rules', lang)}\n"
        out += "| Field | Rule | Error Message | Timing |\n|---|---|---|---|\n"
        for vr in fr.validation_rules:
            out += f"| {vr.field} | {_safe(vr.rule)} | {_safe(vr.error_message)} | {_safe(vr.timing)} |\n"
        out += "\n"
    if fr.permissions:
        out += f"##### {t('permission', lang)}\n"
        out += "| Role | View | Create | Update | Delete | Approve | Export | Notes |\n"
        out += "|---|---|---|---|---|---|---|---|\n"
        for p in fr.permissions:
            out += (
                f"| {p.role} | {_yn(p.view)} | {_yn(p.create)} | {_yn(p.update)} | "
                f"{_yn(p.delete)} | {_yn(p.approve)} | {_yn(p.export)} | {_safe(p.notes)} |\n"
            )
        out += "\n"
    if fr.audit_logs:
        out += f"##### {t('audit_log', lang)}\n"
        out += "| Event | Logged Items | Retention | Related NFR |\n|---|---|---|---|\n"
        for al in fr.audit_logs:
            out += (
                f"| {al.event} | {_safe(al.logged_items)} | {_safe(al.retention)} | "
                f"{', '.join(al.related_nfr) or '-'} |\n"
            )
        out += "\n"
    if fr.acceptance_criteria:
        out += f"##### {t('acceptance_criteria', lang)}\n"
        for ac in fr.acceptance_criteria:
            out += f"- {ac}\n"
        out += "\n"
    if fr.test_viewpoints:
        tv = fr.test_viewpoints
        out += f"##### {t('test_viewpoints', lang)}\n"
        if tv.normal:
            out += f"- Normal case: {tv.normal}\n"
        if tv.boundary:
            out += f"- Boundary case: {tv.boundary}\n"
        if tv.exception:
            out += f"- Exception case: {tv.exception}\n"
        if tv.permission:
            out += f"- Permission case: {tv.permission}\n"
        out += "\n"
    if fr.postcondition:
        out += f"##### {t('postcondition', lang)}\n- {fr.postcondition}\n\n"
    if fr.notes:
        out += f"##### {t('notes_questions', lang)}\n"
        for n in fr.notes:
            out += f"- {n}\n"
        out += "\n"
    return out


def _render_impl_dashboard(items: list[FunctionalRequirement]) -> str:
    """Implementation Status snapshot table (counts + percentage by ImplStatus).

    Rendered above the FR list so BrSE/PM see at-a-glance progress without
    scanning every FR row.
    """
    if not items:
        return ""
    total = len(items)
    counts: dict[ImplStatus, int] = dict.fromkeys(ImplStatus, 0)
    for fr in items:
        counts[fr.impl_status or ImplStatus.NOT_STARTED] += 1

    out = "> **Implementation Status Snapshot** (auto-derived from openspec/, codebase scan, and manual overrides)\n\n"
    out += "| Status | Count | % |\n|---|---|---|\n"
    for status in (
        ImplStatus.VERIFIED,
        ImplStatus.DONE,
        ImplStatus.IN_PROGRESS,
        ImplStatus.BLOCKED,
        ImplStatus.NOT_STARTED,
    ):
        c = counts[status]
        pct = (c * 100 // total) if total else 0
        out += f"| {_IMPL_BADGE[status]} | {c} | {pct}% |\n"
    out += f"| **Total** | **{total}** | **100%** |\n\n"
    return out


def _render_fr_section(items: list[FunctionalRequirement], lang: Language) -> str:
    out = _h(2, f"3. {t('functional_requirements', lang)}")
    out += _render_impl_dashboard(items)
    out += _h(3, f"3.1 {t('fr_list', lang)}")
    out += (
        "| FR-ID | Function | Summary | UC | Screen | Role | Priority | Doc Status | Impl Status | Source |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
    )
    if items:
        for fr in items:
            screens = ", ".join(fr.related_screens) or "-"
            ucs = ", ".join(fr.related_uc) or "-"
            src = fr.source.origin if fr.source else "-"
            doc_status = fr.doc_status.value if fr.doc_status else "Draft"
            impl = _impl_badge(fr.impl_status)
            out += (
                f"| {fr.id} | {fr.name} | {_safe(fr.summary or fr.description[:60] if fr.description else None)} | "
                f"{ucs} | {screens} | {_safe(fr.role)} | {fr.priority.value} | {doc_status} | {impl} | {src} |\n"
            )
    else:
        out += "| FR-001 | _TBD_ | _TBD_ | - | - | - | - | Draft | ⬜ Not Started | - |\n"
    out += "\n"

    if items:
        out += _h(3, f"3.2 {t('fr_detail', lang)}")
        for fr in items:
            out += _render_fr_detail(fr, lang)
    return out


# --- 4. Business Rules ---


def _render_business_rules(items: list[BusinessRule], lang: Language) -> str:
    out = _h(2, f"4. {t('business_rules', lang)}")
    out += "| BR-ID | Rule | Related FR | Priority | Source | Owner | Notes |\n"
    out += "|---|---|---|---|---|---|---|\n"
    if items:
        for br in items:
            src = br.source.origin if br.source else "-"
            out += (
                f"| {br.id} | {_safe(br.rule)} | {', '.join(br.related_fr) or '-'} | "
                f"{br.priority.value} | {src} | {_safe(br.owner)} | {_safe(br.notes)} |\n"
            )
    else:
        out += "| BR-001 | _TBD_ | - | - | - | - | - |\n"
    out += "\n"
    if items:
        for br in items:
            out += _h(3, f"{br.id}: {_safe(br.rule)[:60]}")
            out += f"- **Rule:** {_safe(br.rule)}\n"
            if br.related_fr:
                out += f"- **Related FR:** {', '.join(br.related_fr)}\n"
            out += f"- **Priority:** {br.priority.value}\n\n"
    return out


# --- 5. Roles & Permissions ---


def _render_roles(model: ProjectModel, lang: Language) -> str:
    out = _h(2, f"5. {t('roles_permissions', lang)}")
    out += _h(3, f"5.1 {t('role_definition', lang)}")
    out += "| Role-ID | Role Name | Description | User Type | Notes |\n"
    out += "|---|---|---|---|---|\n"
    if model.roles:
        for r in model.roles:
            out += f"| {r.id} | {r.name} | {_safe(r.description)} | {_safe(r.user_type)} | {_safe(r.notes)} |\n"
    else:
        out += "| ROLE-001 | _TBD_ | _TBD_ | - | - |\n"
    out += "\n"
    if model.roles:
        for r in model.roles:
            out += _h(3, f"{r.id}: {r.name}")
            if r.description:
                out += f"- **Description:** {r.description}\n"
            if r.user_type:
                out += f"- **User Type:** {r.user_type}\n"
            out += "\n"

    out += _h(3, f"5.2 {t('permission_matrix', lang)}")
    out += "| Role | FR-ID | Screen | View | Create | Update | Delete | Approve | Export | Import | Notes |\n"
    out += "|---|---|---|---|---|---|---|---|---|---|---|\n"
    if model.permission_matrix:
        for p in model.permission_matrix:
            out += (
                f"| {p.role} | {_safe(p.fr_id)} | {_safe(p.screen)} | "
                f"{_yn(p.view)} | {_yn(p.create)} | {_yn(p.update)} | "
                f"{_yn(p.delete)} | {_yn(p.approve)} | {_yn(p.export)} | "
                f"{_yn(p.import_)} | {_safe(p.notes)} |\n"
            )
    else:
        out += "| _TBD_ | - | - | - | - | - | - | - | - | - | - |\n"
    out += "\n"
    return out


# --- 6. Non-Functional Requirements ---


def _render_nfr_section(model: ProjectModel, lang: Language) -> str:
    items = model.non_functional_requirements
    out = _h(2, f"6. {t('non_functional_requirements', lang)}")
    out += "> NFR categories follow an IPA-like 6-category structure.\n\n"
    out += _h(3, f"6.1 {t('nfr_list', lang)}")
    out += (
        "| NFR-ID | Category | Requirement | Target / Metric | Measurement Condition | "
        "Priority | Owner | Status |\n"
        "|---|---|---|---|---|---|---|---|\n"
    )
    if items:
        for nfr in items:
            status = nfr.doc_status.value if nfr.doc_status else "Draft"
            out += (
                f"| {nfr.id} | {nfr.category} | {_safe(nfr.requirement)} | "
                f"{_safe(nfr.metric)} | {_safe(nfr.measurement_condition)} | "
                f"{nfr.priority.value} | {_safe(nfr.owner)} | {status} |\n"
            )
    else:
        out += "| NFR-001 | Availability | _TBD_ | - | - | - | - | Draft |\n"
    out += "\n"
    # Per-NFR H3 anchors for diff engine
    if items:
        for nfr in items:
            out += _h(3, f"{nfr.id}: {nfr.category}")
            out += f"- **Requirement:** {_safe(nfr.requirement)}\n"
            if nfr.metric:
                out += f"- **Metric:** {nfr.metric}\n"
            if nfr.measurement_condition:
                out += f"- **Measurement:** {nfr.measurement_condition}\n"
            out += "\n"

    out += _h(3, f"6.2 {t('security_pii', lang)}")
    out += "| Item | Requirement | Related Data | Related FR | Notes |\n"
    out += "|---|---|---|---|---|\n"
    if model.security_pii:
        for s in model.security_pii:
            out += (
                f"| {s.item} | {_safe(s.requirement)} | {', '.join(s.related_data) or '-'} | "
                f"{', '.join(s.related_fr) or '-'} | {_safe(s.notes)} |\n"
            )
    else:
        for item in ("Authentication", "Authorization", "Encryption in transit",
                     "Encryption at rest", "Audit log"):
            out += f"| {item} | _TBD_ | - | - | - |\n"
    out += "\n"
    return out


# --- 7. Data Items ---


def _render_data_section(model: ProjectModel, lang: Language) -> str:
    out = _h(2, f"7. {t('data_items', lang)}")
    out += _h(3, f"7.1 {t('main_entities', lang)}")
    out += "Detailed ERD: see `database-design.md`.\n\n"
    out += "| Entity-ID | Entity | Business Meaning | Owner | Notes |\n"
    out += "|---|---|---|---|---|\n"
    if model.entities:
        for e in model.entities:
            out += f"| {e.id} | {e.entity} | {_safe(e.business_meaning)} | {_safe(e.owner)} | {_safe(e.notes)} |\n"
    else:
        out += "| ENT-001 | _TBD_ | _TBD_ | - | - |\n"
    out += "\n"

    out += _h(3, f"7.2 {t('data_item_list', lang)}")
    out += (
        "| DATA-ID | Entity | Field | Business Meaning | Example | Type | Length | Null | "
        "Validation | Constraint | PII | Source | Update Timing | Notes |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    )
    if model.data_items:
        for d in model.data_items:
            out += (
                f"| {d.id} | {d.entity} | {d.field_name} | {_safe(d.business_meaning)} | "
                f"{_safe(d.example)} | {d.field_type} | {_safe(d.length)} | "
                f"{'N' if not d.nullable else 'Y'} | {_safe(d.validation)} | "
                f"{_safe(d.constraint)} | {_yn(d.pii)} | {_safe(d.data_source)} | "
                f"{_safe(d.update_timing)} | {_safe(d.notes)} |\n"
            )
    else:
        out += "| DATA-001 | _TBD_ | _TBD_ | - | - | - | - | - | - | - | - | - | - | - |\n"
    out += "\n"

    out += _h(3, f"7.3 {t('data_retention', lang)}")
    out += "| Data / Entity | Retention Period | Deletion Trigger | Backup Handling | Legal / Compliance Notes |\n"
    out += "|---|---|---|---|---|\n"
    if model.data_retention:
        for r in model.data_retention:
            out += (
                f"| {r.data_or_entity} | {_safe(r.retention_period)} | "
                f"{_safe(r.deletion_trigger)} | {_safe(r.backup_handling)} | "
                f"{_safe(r.compliance_notes)} |\n"
            )
    else:
        out += "| _TBD_ | - | - | - | - |\n"
    out += "\n"
    return out


# --- 8. External Interfaces ---


def _render_interfaces(items: list[ExternalInterface], lang: Language) -> str:
    out = _h(2, f"8. {t('external_interfaces', lang)}")
    out += "Detailed API: see `api-docs.md`.\n\n"
    out += (
        "| INT-ID | Name | Direction | Type | Target | Protocol | Auth | Format | "
        "Timing | Retry | Timeout | Error Handling | Owner | Related FR |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    )
    if items:
        for it in items:
            out += (
                f"| {it.id} | {it.name} | {_safe(it.direction)} | {it.type} | "
                f"{_safe(it.target)} | {_safe(it.protocol)} | {_safe(it.auth)} | "
                f"{_safe(it.format)} | {_safe(it.timing)} | {_safe(it.retry)} | "
                f"{_safe(it.timeout)} | {_safe(it.error_handling)} | "
                f"{_safe(it.owner)} | {', '.join(it.related_fr) or '-'} |\n"
            )
    else:
        out += "| INT-001 | _TBD_ | - | REST | - | - | - | - | - | - | - | - | - | - |\n"
    out += "\n"

    # Per-interface H3 anchors
    if items:
        for it in items:
            out += _h(3, f"{it.id}: {it.name}")
            out += f"- **Type:** {it.type}\n"
            if it.target:
                out += f"- **Target:** {it.target}\n"
            if it.method and it.endpoint_path:
                out += f"- **Endpoint:** `{it.method} {it.endpoint_path}`\n"
            if it.summary:
                out += f"- **Summary:** {it.summary}\n"
            out += "\n"

    # 8.1 file detail (only if any file-type interface exists)
    file_ints = [i for i in (items or []) if i.file_name_pattern]
    if file_ints:
        out += _h(3, f"8.1 {t('file_interface_detail', lang)}")
        out += "| INT-ID | File Name Pattern | Charset | Delimiter | Header | Compression | Duplicate Handling | Archive Rule |\n"
        out += "|---|---|---|---|---|---|---|---|\n"
        for it in file_ints:
            out += (
                f"| {it.id} | {it.file_name_pattern} | {_safe(it.charset)} | "
                f"{_safe(it.delimiter)} | {_yn(it.header)} | "
                f"{_safe(it.compression)} | {_safe(it.duplicate_handling)} | "
                f"{_safe(it.archive_rule)} |\n"
            )
        out += "\n"
    return out


# --- 9. Reports & Files ---


def _render_reports(items: list[Report], lang: Language) -> str:
    out = _h(2, f"9. {t('reports_files', lang)}")
    out += (
        "| RPT-ID | Name | Type | Output Format | Trigger | Target User | "
        "Data Source | Layout Spec | Related FR | Notes |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
    )
    if items:
        for r in items:
            out += (
                f"| {r.id} | {r.name} | {_safe(r.type)} | {_safe(r.output_format)} | "
                f"{_safe(r.trigger)} | {_safe(r.target_user)} | "
                f"{_safe(r.data_source)} | {_safe(r.layout_spec)} | "
                f"{', '.join(r.related_fr) or '-'} | {_safe(r.notes)} |\n"
            )
    else:
        out += "| RPT-001 | _TBD_ | - | - | - | - | - | - | - | - |\n"
    out += "\n"

    if items and any(r.items for r in items):
        out += _h(3, f"9.1 {t('report_items', lang)}")
        out += "| RPT-ID | No. | Output Field | Source Data | Format | Required | Sort / Group | Notes |\n"
        out += "|---|---|---|---|---|---|---|---|\n"
        for r in items:
            for ri in r.items:
                out += (
                    f"| {r.id} | {ri.no} | {ri.output_field} | "
                    f"{_safe(ri.source_data)} | {_safe(ri.format)} | "
                    f"{_yn(ri.required)} | {_safe(ri.sort_or_group)} | "
                    f"{_safe(ri.notes)} |\n"
                )
        out += "\n"
    return out


# --- 10. Acceptance Criteria & UAT ---


def _render_acceptance(model: ProjectModel, lang: Language) -> str:
    out = _h(2, f"10. {t('acceptance_uat', lang)}")
    out += _h(3, f"10.1 {t('acceptance_list', lang)}")
    out += (
        "| AC-ID | Acceptance Criterion | Related FR | Related UC | "
        "Related Test Case | Owner | Status |\n"
        "|---|---|---|---|---|---|---|\n"
    )
    if model.acceptance_criteria:
        for ac in model.acceptance_criteria:
            status = ac.doc_status.value if ac.doc_status else "Draft"
            out += (
                f"| {ac.id} | {_safe(ac.criterion)} | "
                f"{', '.join(ac.related_fr) or '-'} | "
                f"{', '.join(ac.related_uc) or '-'} | "
                f"{', '.join(ac.related_test_cases) or '-'} | "
                f"{_safe(ac.owner)} | {status} |\n"
            )
    else:
        out += "| AC-001 | _TBD_ | - | - | - | - | Draft |\n"
    out += "\n"

    out += _h(3, f"10.2 {t('uat_exit_criteria', lang)}")
    out += "| Criteria-ID | Criteria | Target | Measurement / Evidence | Owner |\n"
    out += "|---|---|---|---|---|\n"
    if model.uat_criteria:
        for u in model.uat_criteria:
            out += (
                f"| {u.id} | {_safe(u.criterion)} | {_safe(u.target)} | "
                f"{_safe(u.measurement)} | {_safe(u.owner)} |\n"
            )
    else:
        out += "| UAT-001 | Must-priority FR completed | 100% | Traceability matrix | _TBD_ |\n"
        out += "| UAT-002 | Critical / High defects closed | 100% | Defect report | _TBD_ |\n"
        out += "| UAT-003 | Customer approval completed | Yes | Approval record | _TBD_ |\n"
    out += "\n"
    return out


# --- 11. Traceability ---


def _render_traceability(model: ProjectModel, lang: Language) -> str:
    out = _h(2, f"11. {t('traceability', lang)}")
    out += (
        "| FR-ID | UC-ID | BR-ID | Screen ID | DATA-ID | INT-ID | NFR-ID | "
        "RPT-ID | AC-ID | Test Case ID | Status |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|\n"
    )
    if model.traceability:
        for tr in model.traceability:
            status = tr.doc_status.value if tr.doc_status else "Draft"
            out += (
                f"| {tr.fr_id} | {_safe(tr.uc_id)} | {_safe(tr.br_id)} | "
                f"{_safe(tr.screen_id)} | {_safe(tr.data_id)} | {_safe(tr.int_id)} | "
                f"{_safe(tr.nfr_id)} | {_safe(tr.rpt_id)} | {_safe(tr.ac_id)} | "
                f"{_safe(tr.test_case_id)} | {status} |\n"
            )
    elif model.functional_requirements:
        # Auto-derive from FR cross-refs
        for fr in model.functional_requirements:
            out += (
                f"| {fr.id} | {', '.join(fr.related_uc) or '-'} | "
                f"{', '.join(fr.business_rules) or '-'} | "
                f"{', '.join(fr.related_screens) or '-'} | "
                f"{', '.join(fr.related_data) or '-'} | "
                f"{', '.join(fr.related_interfaces) or '-'} | "
                f"{', '.join(fr.related_nfr) or '-'} | - | "
                f"{', '.join(fr.acceptance_criteria) or '-'} | "
                f"{', '.join(fr.related_test_cases) or '-'} | "
                f"{(fr.doc_status.value if fr.doc_status else 'Draft')} |\n"
            )
    else:
        out += "| FR-001 | - | - | - | - | - | - | - | - | - | Draft |\n"
    out += "\n"
    return out


# --- 12. Open Issues / Q&A ---


def _render_open_qa(model: ProjectModel, lang: Language) -> str:
    out = _h(2, f"12. {t('open_qa', lang)}")
    out += (
        "| Q-ID | Date | Category | Question / Issue | Answer / Decision | "
        "Owner | Due Date | Status | Related ID |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )
    qs = model.open_questions
    if qs:
        for q in qs:
            out += (
                f"| {q.id} | {_safe(q.date)} | {_safe(q.category)} | "
                f"{_safe(q.question)} | {_safe(q.answer)} | {_safe(q.owner)} | "
                f"{_safe(q.due_date)} | {q.q_status} | {_safe(q.related_id)} |\n"
            )
    else:
        out += "| Q-001 | - | - | _TBD_ | - | - | - | Open | - |\n"
    out += "\n"
    return out


# --- 13. Constraints, Assumptions & Risks ---


def _render_constraints_risks(model: ProjectModel, lang: Language) -> str:
    cr = model.constraints_risks
    out = _h(2, f"13. {t('constraints_risks', lang)}")

    out += _h(3, f"13.1 {t('constraints', lang)}")
    out += "| Constraint-ID | Category | Constraint | Impact | Owner |\n"
    out += "|---|---|---|---|---|\n"
    if cr.constraint_records:
        for c in cr.constraint_records:
            out += f"| {c.id} | {_safe(c.category)} | {_safe(c.constraint)} | {_safe(c.impact)} | {_safe(c.owner)} |\n"
    elif cr.technical or cr.operational or cr.compliance:
        n = 0
        for cat, items in (("Tech", cr.technical), ("Ops", cr.operational), ("Compliance", cr.compliance)):
            for txt in items:
                n += 1
                out += f"| CONS-{n:03d} | {cat} | {txt} | - | - |\n"
    else:
        out += "| CONS-001 | - | _TBD_ | - | - |\n"
    out += "\n"

    out += _h(3, f"13.2 {t('assumptions', lang)}")
    out += "| Assumption-ID | Assumption | Impact if False | Owner | Validation Method |\n"
    out += "|---|---|---|---|---|\n"
    if cr.assumption_records:
        for a in cr.assumption_records:
            out += f"| {a.id} | {_safe(a.assumption)} | {_safe(a.impact_if_false)} | {_safe(a.owner)} | {_safe(a.validation_method)} |\n"
    elif cr.assumptions:
        for n, txt in enumerate(cr.assumptions, 1):
            out += f"| ASM-{n:03d} | {txt} | - | - | - |\n"
    else:
        out += "| ASM-001 | _TBD_ | - | - | - |\n"
    out += "\n"

    out += _h(3, f"13.3 {t('risks', lang)}")
    out += "| Risk-ID | Risk | Impact | Likelihood | Mitigation | Owner | Status |\n"
    out += "|---|---|---|---|---|---|---|\n"
    if cr.risks:
        for n, r in enumerate(cr.risks, 1):
            rid = r.id or f"RISK-{n:03d}"
            out += (
                f"| {rid} | {r.description} | {r.impact} | {r.likelihood} | "
                f"{_safe(r.mitigation)} | {_safe(r.owner)} | {r.risk_status} |\n"
            )
    else:
        out += "| RISK-001 | _TBD_ | - | - | - | - | Open |\n"
    out += "\n"
    return out


# --- Appendix A: Screen index ---


def _render_screen_index(screens: list[Screen], lang: Language) -> str:
    out = _h(2, f"Appendix A: {t('screen_design_index', lang)}")
    out += "Per-screen detail in `screen-specs/SCREEN-XXX-{slug}.md`.\n\n"
    out += _h(3, f"A.1 {t('screen_list', lang)}")
    out += "| Screen ID | Screen Name | Related FR | Role | File | Status |\n"
    out += "|---|---|---|---|---|---|\n"
    if screens:
        for s in screens:
            link = f"[screen-specs/{s.id}-{s.slug}.md](./screen-specs/{s.id}-{s.slug}.md)"
            out += (
                f"| {s.id} | {s.name} | {', '.join(s.related_fr) or '-'} | "
                f"{s.role} | {link} | Draft |\n"
            )
    else:
        out += "| SCREEN-001 | _TBD_ | - | - | - | Draft |\n"
    out += "\n"

    # Per-screen H3 anchors for diff engine
    if screens:
        for s in screens:
            out += _h(3, f"{s.id}: {s.name}")
            out += f"- **Slug:** {s.slug}\n"
            out += f"- **Role:** {s.role}\n"
            if s.url_path:
                out += f"- **URL:** `{s.url_path}`\n"
            if s.related_fr:
                out += f"- **Related FR:** {', '.join(s.related_fr)}\n"
            out += f"- **Detail:** [screen-specs/{s.id}-{s.slug}.md](./screen-specs/{s.id}-{s.slug}.md)\n\n"
    return out


# --- Appendix B: Glossary ---


def _render_glossary(model: ProjectModel, lang: Language) -> str:
    out = _h(2, f"Appendix B: {t('glossary', lang)}")
    out += "| JP | EN | VN | Definition |\n|---|---|---|---|\n"
    if model.glossary:
        for g in model.glossary:
            out += f"| {_safe(g.term_jp)} | {_safe(g.term_en)} | {_safe(g.term_vn)} | {g.definition} |\n"
    else:
        out += "| _TBD_ | _TBD_ | _TBD_ | _TBD_ |\n"
    out += "\n"
    return out


# --- Top-level orchestrator ---


def render_srs(model: ProjectModel, lang: Language) -> str:
    """Render full SRS markdown from a validated ProjectModel (template-updated, 13 sections)."""
    parts = [
        _render_meta(model, lang),
        _render_revision_history(model, lang),
        _render_doc_control(lang),
        _render_overview(model, lang),
        _render_business_flow(model, lang),
        _render_fr_section(model.functional_requirements, lang),
        _render_business_rules(model.business_rules, lang),
        _render_roles(model, lang),
        _render_nfr_section(model, lang),
        _render_data_section(model, lang),
        _render_interfaces(model.external_interfaces, lang),
        _render_reports(model.reports, lang),
        _render_acceptance(model, lang),
        _render_traceability(model, lang),
        _render_open_qa(model, lang),
        _render_constraints_risks(model, lang),
        _render_screen_index(model.screens, lang),
        _render_glossary(model, lang),
    ]
    return "".join(parts)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--project-model", required=True)
    p.add_argument("--language", default="EN", choices=["JP", "EN", "VN"])
    p.add_argument("--output", required=True)
    args = p.parse_args()

    model = load_project_model(args.project_model)
    lang = Language(args.language)
    text = render_srs(model, lang)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Rendered SRS -> {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
