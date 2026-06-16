#!/usr/bin/env bash
# test-finishing-report-step.sh — validates the Implementation Report template
# and the "Generate Implementation Report" step inserted into
# finishing-a-development-branch/SKILL.md (between Verify Tests and Present Options).

set -uo pipefail

TEST_NAME="finishing-report-step"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

SKILL_DIR="$TEST_PLUGIN_ROOT/skills/finishing-a-development-branch"
SKILL_MD="$SKILL_DIR/SKILL.md"
TEMPLATE="$SKILL_DIR/references/implementation-report-template.md"

# ---------------------------------------------------------------------------
# 1. Template exists and contains all 6 section headings
# ---------------------------------------------------------------------------
case_1_template_exists() {
    assert_file_exists "$TEMPLATE" "1.1 implementation-report-template.md exists"
}

case_1_template_headings() {
    local headings=(
        "## 1. Tóm tắt điều hành"
        "## 2. Công việc đã thực hiện"
        "## 3. Tests & review"
        "## 4. Ảnh hưởng đến dự án"
        "## 5. Rủi ro / nợ kỹ thuật & follow-up"
        "## 6. Truy vết"
    )
    local body i=1
    body="$(cat "$TEMPLATE" 2>/dev/null)"
    for h in "${headings[@]}"; do
        assert_contains "$body" "$h" "1.1.$i template has heading: $h"
        i=$((i + 1))
    done
}

case_1_template_note() {
    local body
    body="$(cat "$TEMPLATE" 2>/dev/null)"
    assert_contains "$body" "In chat" "1.2 template states chat-default in top note"
    assert_contains "$body" "mục trống ghi —" "1.3 template states empty sections collapse to —"
    assert_contains "$body" "plans/reports/" "1.4 template suggests plans/reports/ path"
}

# ---------------------------------------------------------------------------
# 2. SKILL.md has the report step in the correct position
# ---------------------------------------------------------------------------
case_2_skill_has_report_step() {
    local body
    body="$(cat "$SKILL_MD" 2>/dev/null)"
    assert_contains "$body" "Generate Implementation Report" \
        "2.1 SKILL.md has 'Generate Implementation Report' step"
}

# Line ordering: Verify Tests < Generate Implementation Report < Present Options
case_2_step_order() {
    local ln_verify ln_report ln_options
    ln_verify=$(grep -n 'Verify Tests' "$SKILL_MD" | head -1 | cut -d: -f1)
    ln_report=$(grep -n 'Generate Implementation Report' "$SKILL_MD" | head -1 | cut -d: -f1)
    ln_options=$(grep -n 'Present Options' "$SKILL_MD" | head -1 | cut -d: -f1)

    if [[ -n "$ln_verify" && -n "$ln_report" && "$ln_verify" -lt "$ln_report" ]]; then
        _pass "2.2 report step appears AFTER Verify Tests (L$ln_verify < L$ln_report)"
    else
        _fail "2.2 report step not after Verify Tests (verify=L$ln_verify report=L$ln_report)"
    fi

    if [[ -n "$ln_report" && -n "$ln_options" && "$ln_report" -lt "$ln_options" ]]; then
        _pass "2.3 report step appears BEFORE Present Options (L$ln_report < L$ln_options)"
    else
        _fail "2.3 report step not before Present Options (report=L$ln_report options=L$ln_options)"
    fi
}

case_2_references_template() {
    local body
    body="$(cat "$SKILL_MD" 2>/dev/null)"
    assert_contains "$body" "references/implementation-report-template.md" \
        "2.4 SKILL.md references the template path"
}

case_2_chat_default_and_file_optional() {
    local body
    body="$(cat "$SKILL_MD" 2>/dev/null)"
    assert_contains "$body" "in chat" "2.5 SKILL.md states chat default"
    # "only write file if user asks" — match intent (case-insensitive on key words)
    if grep -qi 'only write.*file.*user asks\|chỉ ghi file.*user yêu cầu\|write a file only if\|only.*if the user asks' "$SKILL_MD"; then
        _pass "2.6 SKILL.md states file is written only if user asks"
    else
        _fail "2.6 SKILL.md missing 'only write file if user asks' statement"
    fi
}

# ---------------------------------------------------------------------------
# 3. The 4 options remain intact (intent unchanged)
# ---------------------------------------------------------------------------
case_3_options_intact() {
    local body
    body="$(cat "$SKILL_MD" 2>/dev/null)"
    assert_contains "$body" "Merge back to" "3.1 option 1 (merge) intact"
    assert_contains "$body" "create a Pull Request" "3.2 option 2 (PR) intact"
    assert_contains "$body" "Keep the branch as-is" "3.3 option 3 (keep) intact"
    assert_contains "$body" "Discard this work" "3.4 option 4 (discard) intact"
}

# ---------------------------------------------------------------------------
# Run all cases
# ---------------------------------------------------------------------------
case_1_template_exists
case_1_template_headings
case_1_template_note
case_2_skill_has_report_step
case_2_step_order
case_2_references_template
case_2_chat_default_and_file_optional
case_3_options_intact

exit_with_status
