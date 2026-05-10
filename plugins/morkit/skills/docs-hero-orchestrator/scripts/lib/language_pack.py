"""Heading translations for SRS / API / DB docs across JP / EN / VN.

Single source of truth for localized headings used by renderers.
Renderers call `t(key, lang)` instead of hardcoding strings.

Public API:
    Language: enum (JP, EN, VN)
    t(key, lang) -> str           # Lookup, returns key as-is if missing (with warning)
    available_keys() -> list[str] # All registered keys (for QA/coverage tests)
"""
from __future__ import annotations

import logging
from enum import Enum

log = logging.getLogger(__name__)


class Language(str, Enum):
    JP = "JP"
    EN = "EN"
    VN = "VN"


HEADINGS: dict[str, dict[str, str]] = {
    # --- SRS top-level sections (template-updated, 13 sections + appendices) ---
    "doc_control": {
        "JP": "ドキュメント運用ルール",
        "EN": "Document Control Rules",
        "VN": "Quy tắc kiểm soát tài liệu",
    },
    "language_rule": {"JP": "言語ルール", "EN": "Language Rule", "VN": "Quy tắc ngôn ngữ"},
    "status_definition": {"JP": "ステータス定義", "EN": "Status Definition", "VN": "Định nghĩa trạng thái"},
    "priority_definition": {"JP": "優先度定義", "EN": "Priority Definition", "VN": "Định nghĩa độ ưu tiên"},
    "overview": {"JP": "概要", "EN": "Overview", "VN": "Tổng quan"},
    "purpose": {"JP": "目的", "EN": "Purpose", "VN": "Mục đích"},
    "background": {"JP": "背景", "EN": "Background", "VN": "Bối cảnh"},
    "target_release": {"JP": "対象リリース", "EN": "Target Release", "VN": "Bản phát hành đích"},
    "scope": {"JP": "スコープ", "EN": "Scope", "VN": "Phạm vi"},
    "in_scope": {"JP": "今回対象範囲", "EN": "In-scope for This Release", "VN": "Trong phạm vi"},
    "out_of_scope": {"JP": "対象外", "EN": "Out-of-scope", "VN": "Ngoài phạm vi"},
    "future_scope": {"JP": "将来対応", "EN": "Future Scope", "VN": "Phạm vi tương lai"},
    "pending_confirmation": {
        "JP": "未確定・要確認",
        "EN": "Pending Confirmation",
        "VN": "Chờ xác nhận",
    },
    "stakeholders": {"JP": "ステークホルダー", "EN": "Stakeholders", "VN": "Bên liên quan"},
    "references": {"JP": "参考資料", "EN": "References", "VN": "Tài liệu tham khảo"},
    "current_business_flow": {
        "JP": "現状・業務フロー",
        "EN": "Current State & Business Flow",
        "VN": "Hiện trạng & Luồng nghiệp vụ",
    },
    "current_process": {
        "JP": "現状業務",
        "EN": "Current Business Process",
        "VN": "Nghiệp vụ hiện tại",
    },
    "issues": {"JP": "現状課題", "EN": "Current Issues", "VN": "Vấn đề hiện tại"},
    "to_be_flow": {"JP": "To-Be 業務フロー", "EN": "To-Be Business Flow", "VN": "Luồng nghiệp vụ mục tiêu"},
    "use_cases": {"JP": "ユースケース一覧", "EN": "Use Case List", "VN": "Danh sách ca sử dụng"},
    "use_case_detail": {
        "JP": "ユースケース詳細",
        "EN": "Use Case Detail",
        "VN": "Chi tiết ca sử dụng",
    },
    "functional_requirements": {
        "JP": "機能要件",
        "EN": "Functional Requirements",
        "VN": "Yêu cầu chức năng",
    },
    "fr_list": {
        "JP": "機能一覧",
        "EN": "Functional Requirements List",
        "VN": "Danh sách yêu cầu chức năng",
    },
    "fr_detail": {"JP": "機能詳細", "EN": "Functional Details", "VN": "Chi tiết chức năng"},
    "main_flow": {"JP": "メインフロー", "EN": "Main Flow", "VN": "Luồng chính"},
    "alt_flow": {"JP": "代替フロー", "EN": "Alternate Flow", "VN": "Luồng thay thế"},
    "exception_flow": {"JP": "例外フロー", "EN": "Exception Flow", "VN": "Luồng ngoại lệ"},
    "validation_rules": {
        "JP": "バリデーションルール",
        "EN": "Validation Rules",
        "VN": "Quy tắc kiểm tra",
    },
    "permission": {"JP": "権限", "EN": "Permission", "VN": "Phân quyền"},
    "audit_log": {"JP": "監査ログ", "EN": "Audit Log", "VN": "Nhật ký kiểm toán"},
    "acceptance_criteria": {
        "JP": "受入条件",
        "EN": "Acceptance Criteria",
        "VN": "Tiêu chí nghiệm thu",
    },
    "test_viewpoints": {"JP": "テスト観点", "EN": "Test Viewpoints", "VN": "Quan điểm kiểm thử"},
    "precondition": {"JP": "事前条件", "EN": "Pre-condition", "VN": "Điều kiện trước"},
    "postcondition": {"JP": "事後条件", "EN": "Post-condition", "VN": "Điều kiện sau"},
    "trigger": {"JP": "トリガー", "EN": "Trigger", "VN": "Kích hoạt"},
    "notes_questions": {
        "JP": "備考・未決事項",
        "EN": "Notes / Open Questions",
        "VN": "Ghi chú / Câu hỏi",
    },
    "business_rules": {"JP": "業務ルール", "EN": "Business Rules", "VN": "Quy tắc nghiệp vụ"},
    "roles_permissions": {
        "JP": "権限",
        "EN": "Roles & Permissions",
        "VN": "Vai trò & Phân quyền",
    },
    "role_definition": {"JP": "ロール定義", "EN": "Role Definition", "VN": "Định nghĩa vai trò"},
    "permission_matrix": {
        "JP": "権限マトリクス",
        "EN": "Permission Matrix",
        "VN": "Ma trận phân quyền",
    },
    "non_functional_requirements": {
        "JP": "非機能要件",
        "EN": "Non-Functional Requirements",
        "VN": "Yêu cầu phi chức năng",
    },
    "nfr_list": {"JP": "非機能要件一覧", "EN": "NFR List", "VN": "Danh sách yêu cầu phi chức năng"},
    "security_pii": {
        "JP": "セキュリティ・個人情報",
        "EN": "Security & PII",
        "VN": "Bảo mật & Thông tin cá nhân",
    },
    "data_items": {"JP": "データ項目定義", "EN": "Data Item Definitions", "VN": "Định nghĩa dữ liệu"},
    "main_entities": {"JP": "主要エンティティ", "EN": "Main Entities", "VN": "Thực thể chính"},
    "data_item_list": {"JP": "データ項目一覧", "EN": "Data Item List", "VN": "Danh sách mục dữ liệu"},
    "data_retention": {
        "JP": "データ保持・削除",
        "EN": "Data Retention & Deletion",
        "VN": "Lưu trữ & Xoá dữ liệu",
    },
    "external_interfaces": {
        "JP": "外部インターフェース",
        "EN": "External Interfaces",
        "VN": "Giao diện ngoại vi",
    },
    "file_interface_detail": {
        "JP": "ファイル連携詳細",
        "EN": "File Interface Detail",
        "VN": "Chi tiết tích hợp tệp",
    },
    "reports_files": {"JP": "帳票・ファイル", "EN": "Reports & Files", "VN": "Báo cáo & Tệp"},
    "report_items": {
        "JP": "帳票・ファイル項目",
        "EN": "Report / File Items",
        "VN": "Mục báo cáo / tệp",
    },
    "acceptance_uat": {
        "JP": "受入条件・UAT",
        "EN": "Acceptance Criteria & UAT",
        "VN": "Tiêu chí nghiệm thu & UAT",
    },
    "acceptance_list": {
        "JP": "受入条件一覧",
        "EN": "Acceptance Criteria List",
        "VN": "Danh sách tiêu chí nghiệm thu",
    },
    "uat_exit_criteria": {
        "JP": "UAT 判定基準",
        "EN": "UAT Exit Criteria",
        "VN": "Tiêu chí kết thúc UAT",
    },
    "traceability": {
        "JP": "トレーサビリティ",
        "EN": "Traceability Matrix",
        "VN": "Ma trận truy vết",
    },
    "open_qa": {
        "JP": "未決事項・Q&A",
        "EN": "Open Issues & Q&A",
        "VN": "Vấn đề mở & Q&A",
    },
    "constraints_risks": {
        "JP": "制約・前提・リスク",
        "EN": "Constraints, Assumptions & Risks",
        "VN": "Ràng buộc, Giả định & Rủi ro",
    },
    "constraints": {"JP": "制約", "EN": "Constraints", "VN": "Ràng buộc"},
    "assumptions": {"JP": "前提", "EN": "Assumptions", "VN": "Giả định"},
    "risks": {"JP": "リスク", "EN": "Risks", "VN": "Rủi ro"},
    "screen_design_index": {
        "JP": "画面設計書 一覧",
        "EN": "Screen Design Spec Index",
        "VN": "Danh sách thiết kế màn hình",
    },
    "screen_list": {"JP": "画面一覧", "EN": "Screen List", "VN": "Danh sách màn hình"},
    "screen_transition_map": {
        "JP": "画面遷移マップ",
        "EN": "Global Screen Transition Map",
        "VN": "Sơ đồ chuyển màn hình",
    },
    "glossary": {"JP": "用語集", "EN": "Glossary", "VN": "Bảng thuật ngữ"},
    "approval": {"JP": "承認", "EN": "Approval", "VN": "Phê duyệt"},
    "revision_history": {"JP": "改訂履歴", "EN": "Revision History", "VN": "Lịch sử sửa đổi"},
    "deprecated_items": {"JP": "廃止項目", "EN": "Deprecated Items", "VN": "Mục đã loại bỏ"},
    # --- Screen spec ---
    "layout": {"JP": "レイアウト", "EN": "Layout", "VN": "Bố cục"},
    "wireframe": {"JP": "ワイヤーフレーム", "EN": "Wireframe", "VN": "Khung giao diện"},
    "input_items": {"JP": "入力項目", "EN": "Input Items", "VN": "Các mục đầu vào"},
    "output_items": {"JP": "出力項目", "EN": "Output Items", "VN": "Các mục đầu ra"},
    "actions": {"JP": "アクション", "EN": "Actions", "VN": "Thao tác"},
    "transitions": {"JP": "画面遷移", "EN": "Screen Transitions", "VN": "Chuyển màn hình"},
    "business_logic": {"JP": "業務ロジック", "EN": "Business Logic", "VN": "Logic nghiệp vụ"},
    "error_handling": {"JP": "エラーハンドリング", "EN": "Error Handling", "VN": "Xử lý lỗi"},
    "test_considerations": {
        "JP": "テスト観点",
        "EN": "Test Considerations",
        "VN": "Cân nhắc kiểm thử",
    },
    "related_files": {"JP": "関連ファイル", "EN": "Related Files", "VN": "Tệp liên quan"},
    # --- API docs ---
    "authentication": {"JP": "認証", "EN": "Authentication", "VN": "Xác thực"},
    "endpoints": {"JP": "エンドポイント", "EN": "Endpoints", "VN": "Endpoints"},
    "error_codes": {"JP": "エラーコード", "EN": "Error Codes", "VN": "Mã lỗi"},
    "rate_limiting": {"JP": "レート制限", "EN": "Rate Limiting", "VN": "Giới hạn truy cập"},
    "webhooks": {"JP": "ウェブフック", "EN": "Webhooks", "VN": "Webhooks"},
    "request_headers": {"JP": "リクエストヘッダー", "EN": "Request Headers", "VN": "Header yêu cầu"},
    "request_body": {"JP": "リクエストボディ", "EN": "Request Body", "VN": "Body yêu cầu"},
    "response": {"JP": "レスポンス", "EN": "Response", "VN": "Phản hồi"},
    "path_parameters": {"JP": "パスパラメータ", "EN": "Path Parameters", "VN": "Tham số đường dẫn"},
    "query_parameters": {"JP": "クエリパラメータ", "EN": "Query Parameters", "VN": "Tham số truy vấn"},
    # --- DB design ---
    "tables": {"JP": "テーブル定義", "EN": "Tables", "VN": "Bảng dữ liệu"},
    "indexes": {"JP": "インデックス", "EN": "Indexes", "VN": "Chỉ mục"},
    "relationships": {"JP": "リレーション", "EN": "Relationships", "VN": "Quan hệ"},
    "enums": {"JP": "列挙型", "EN": "Enums", "VN": "Kiểu liệt kê"},
    "triggers_procedures": {
        "JP": "トリガー・ストアドプロシージャ",
        "EN": "Triggers & Stored Procedures",
        "VN": "Trigger & Stored Procedure",
    },
    "migration_strategy": {
        "JP": "マイグレーション戦略",
        "EN": "Migration Strategy",
        "VN": "Chiến lược migration",
    },
    "backup_retention": {"JP": "バックアップ", "EN": "Backup & Retention", "VN": "Sao lưu"},
    "performance_notes": {"JP": "性能備考", "EN": "Performance Notes", "VN": "Ghi chú hiệu năng"},
    "security": {"JP": "セキュリティ", "EN": "Security", "VN": "Bảo mật"},
    "erd": {"JP": "ER図", "EN": "Entity Relationship Diagram", "VN": "Sơ đồ ERD"},
}


# Vague-term lists per language for QA agent (phase 8 §1.1)
VAGUE_TERMS: dict[str, list[str]] = {
    "EN": [
        "fast", "slow", "good", "bad", "easy", "hard",
        "user-friendly", "scalable", "robust", "secure", "modern",
    ],
    "JP": ["速い", "遅い", "良い", "悪い", "簡単", "難しい", "使いやすい", "セキュア", "堅牢"],
    "VN": ["nhanh", "chậm", "tốt", "xấu", "dễ", "khó", "thân thiện", "bảo mật", "bền vững"],
}


def _resolve_lang(lang) -> str:
    """Accept Language enum from any module / plain string. Returns canonical 'JP'|'EN'|'VN'."""
    if hasattr(lang, "value"):
        return str(lang.value).upper()
    return str(lang).upper()


def t(key: str, lang) -> str:
    """Lookup a heading translation. Returns key as-is if missing (with warning)."""
    lang_value = _resolve_lang(lang)
    bucket = HEADINGS.get(key)
    if bucket is None:
        log.warning("language-pack: unknown key '%s' (returning as-is)", key)
        return key
    translation = bucket.get(lang_value)
    if translation is None:
        log.warning("language-pack: missing %s translation for '%s'", lang_value, key)
        return bucket.get("EN", key)
    return translation


def available_keys() -> list[str]:
    """Return all registered translation keys (for coverage tests)."""
    return sorted(HEADINGS.keys())


def vague_terms(lang) -> list[str]:
    """Return vague-term list for QA detection."""
    return VAGUE_TERMS.get(_resolve_lang(lang), VAGUE_TERMS["EN"])
