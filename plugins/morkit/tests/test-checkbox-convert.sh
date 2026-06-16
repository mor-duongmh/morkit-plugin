#!/usr/bin/env bash
# test-checkbox-convert.sh — tests for bullets_to_checkboxes() in lib/common.sh.
# The function turns Google-Doc-exported bullet items ("* foo") into markdown
# task-list checkboxes ("- [ ] foo") while leaving headings, bold, tables, and
# plain text untouched. Used by generate-checklist.sh so review-checklist.md has
# real tickable checkboxes.

set -uo pipefail

TEST_NAME="checkbox-convert"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

# shellcheck source=../scripts/lib/common.sh
. "$TEST_PLUGIN_ROOT/scripts/lib/common.sh"

# A bullet item becomes a checkbox
case_bullet_to_checkbox() {
    local out
    out="$(printf '%s\n' '* Goal rõ, SMART' | bullets_to_checkboxes)"
    assert_equal "$out" "- [ ] Goal rõ, SMART" "bullet '* ' → '- [ ] '"
}

# Indentation is preserved on nested bullets
case_indent_preserved() {
    local out
    out="$(printf '%s\n' '  * nested item' | bullets_to_checkboxes)"
    assert_equal "$out" "  - [ ] nested item" "indented bullet keeps leading spaces"
}

# Headings are left untouched
case_heading_untouched() {
    local out
    out="$(printf '%s\n' '### 1\. Yêu cầu & phạm vi' | bullets_to_checkboxes)"
    assert_equal "$out" '### 1\. Yêu cầu & phạm vi' "### heading unchanged"
}

# Bold lines (start with **) must NOT become checkboxes
case_bold_untouched() {
    local out
    out="$(printf '%s\n' '**Authentication** *(bỏ qua nếu task không đụng auth)*' | bullets_to_checkboxes)"
    assert_equal "$out" '**Authentication** *(bỏ qua nếu task không đụng auth)*' "bold line unchanged"
}

# Table rows untouched
case_table_untouched() {
    local out
    out="$(printf '%s\n' '| Mức | Khi nào | Hành động |' | bullets_to_checkboxes)"
    assert_equal "$out" '| Mức | Khi nào | Hành động |' "table row unchanged"
}

# Plain text untouched
case_text_untouched() {
    local out
    out="$(printf '%s\n' 'Fail bất kỳ ở đây ≥ Major.' | bullets_to_checkboxes)"
    assert_equal "$out" 'Fail bất kỳ ở đây ≥ Major.' "plain text unchanged"
}

# Mixed block: only bullets convert; counts are right
case_mixed_block() {
    local input out
    input="$(printf '%s\n' \
        '### 1\. Yêu cầu & phạm vi' \
        '' \
        '* Goal rõ' \
        '* IN / OUT scope rõ' \
        '' \
        '**Authentication** *(bỏ qua)*' \
        '' \
        '* Login không leak \[A1\]')"
    out="$(printf '%s\n' "$input" | bullets_to_checkboxes)"
    local boxes; boxes="$(printf '%s\n' "$out" | grep -cE '^- \[ \] ')"
    assert_equal "$boxes" "3" "exactly 3 checkboxes from 3 bullets"
    assert_contains "$out" '### 1\. Yêu cầu & phạm vi' "heading survived"
    assert_contains "$out" '**Authentication**' "bold survived"
    assert_not_contains "$out" '* Goal rõ' "no raw bullet left"
}

case_bullet_to_checkbox
case_indent_preserved
case_heading_untouched
case_bold_untouched
case_table_untouched
case_text_untouched
case_mixed_block

exit_with_status
