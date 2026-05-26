#!/usr/bin/env bash
# test-git-skill-integrity.sh — validates git skill frontmatter, required files,
# and that every "Activate <name> skill" reference resolves to a real skill.

set -uo pipefail

TEST_NAME="git-skill-integrity"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

GIT_SKILL_DIR="$TEST_PLUGIN_ROOT/skills/git"
AGENTS_DIR="$TEST_PLUGIN_ROOT/agents"

# ---------------------------------------------------------------------------
# 1. SKILL.md exists and has required frontmatter keys
# ---------------------------------------------------------------------------
case_1_skill_md_exists() {
    [[ -f "$GIT_SKILL_DIR/SKILL.md" ]] \
        && _pass "1.1 skills/git/SKILL.md exists" \
        || _fail "1.1 skills/git/SKILL.md missing"
}

case_1_frontmatter_name() {
    grep -q '^name:' "$GIT_SKILL_DIR/SKILL.md" \
        && _pass "1.2 SKILL.md has 'name:' key" \
        || _fail "1.2 SKILL.md missing 'name:' key"
}

case_1_frontmatter_description() {
    grep -q '^description:' "$GIT_SKILL_DIR/SKILL.md" \
        && _pass "1.3 SKILL.md has 'description:' key" \
        || _fail "1.3 SKILL.md missing 'description:' key"
}

# ---------------------------------------------------------------------------
# 2. All reference files exist
# ---------------------------------------------------------------------------
case_2_references() {
    local refs=(
        workflow-commit.md
        workflow-push.md
        workflow-pr.md
        workflow-merge.md
        commit-standards.md
        safety-protocols.md
        branch-management.md
        gh-cli-guide.md
    )
    local i=1
    for ref in "${refs[@]}"; do
        local path="$GIT_SKILL_DIR/references/$ref"
        [[ -f "$path" ]] \
            && _pass "2.$i references/$ref exists" \
            || _fail "2.$i references/$ref missing"
        i=$((i + 1))
    done
}

# ---------------------------------------------------------------------------
# 3. git-manager agent exists and has required frontmatter
# ---------------------------------------------------------------------------
case_3_agent_exists() {
    [[ -f "$AGENTS_DIR/git-manager.md" ]] \
        && _pass "3.1 agents/git-manager.md exists" \
        || _fail "3.1 agents/git-manager.md missing"
}

case_3_agent_frontmatter() {
    local agent="$AGENTS_DIR/git-manager.md"
    grep -q '^name:' "$agent" && _pass "3.2 agent has 'name:'" || _fail "3.2 agent missing 'name:'"
    grep -q '^model:' "$agent" && _pass "3.3 agent has 'model:'" || _fail "3.3 agent missing 'model:'"
    grep -q '^tools:' "$agent" && _pass "3.4 agent has 'tools:'" || _fail "3.4 agent missing 'tools:'"
}

case_3_agent_no_team_mode() {
    local agent="$AGENTS_DIR/git-manager.md"
    if grep -q 'Team Mode' "$agent"; then
        _fail "3.5 agent still contains Team Mode section (should be removed)"
    else
        _pass "3.5 agent has no Team Mode section"
    fi
}

# ---------------------------------------------------------------------------
# 4. "Activate <name> skill" references resolve to actual skills
# ---------------------------------------------------------------------------
case_4_skill_activations() {
    local i=1
    while IFS= read -r line; do
        # Extract skill name from: Activate `<name>` skill
        local skill_name
        skill_name=$(echo "$line" | grep -oP 'Activate `\K[^`]+')
        [[ -z "$skill_name" ]] && continue
        local skill_path="$TEST_PLUGIN_ROOT/skills/$skill_name/SKILL.md"
        if [[ -f "$skill_path" ]]; then
            _pass "4.$i Activate '$skill_name' resolves to $skill_path"
        else
            _fail "4.$i Activate '$skill_name' — no skill at skills/$skill_name/SKILL.md"
        fi
        i=$((i + 1))
    done < <(grep -r 'Activate `' "$GIT_SKILL_DIR" "$AGENTS_DIR/git-manager.md" 2>/dev/null)
}

# ---------------------------------------------------------------------------
# 5. No dangerous patterns in reference files
# ---------------------------------------------------------------------------
case_5_no_git_add_dash_A_in_commit() {
    # workflow-commit.md should not blindly stage with git add -A as primary step
    local file="$GIT_SKILL_DIR/references/workflow-commit.md"
    # It's ok if mentioned as fallback with a guard; fail only if it's the primary staging cmd
    if grep -q '^git add -A' "$file"; then
        _fail "5.1 workflow-commit.md has bare 'git add -A' as primary command"
    else
        _pass "5.1 workflow-commit.md does not use bare 'git add -A'"
    fi
}

case_5_no_auto_merge_pattern() {
    local file="$GIT_SKILL_DIR/references/gh-cli-guide.md"
    if grep -q 'gh pr merge --auto' "$file"; then
        _fail "5.2 gh-cli-guide.md still contains auto-merge pattern"
    else
        _pass "5.2 gh-cli-guide.md has no auto-merge pattern"
    fi
}

case_5_no_bulk_pr_close() {
    local file="$GIT_SKILL_DIR/references/gh-cli-guide.md"
    if grep -q 'xargs.*gh pr close' "$file"; then
        _fail "5.3 gh-cli-guide.md still contains bulk PR close command"
    else
        _pass "5.3 gh-cli-guide.md has no bulk PR close command"
    fi
}

case_5_merge_no_default_to_main() {
    local file="$GIT_SKILL_DIR/references/workflow-merge.md"
    if grep -q 'defaults to.*main\b' "$file"; then
        _fail "5.4 workflow-merge.md still has 'defaults to main'"
    else
        _pass "5.4 workflow-merge.md does not default TO_BRANCH to main"
    fi
}

# ---------------------------------------------------------------------------
# Run all cases
# ---------------------------------------------------------------------------
case_1_skill_md_exists
case_1_frontmatter_name
case_1_frontmatter_description
case_2_references
case_3_agent_exists
case_3_agent_frontmatter
case_3_agent_no_team_mode
case_4_skill_activations
case_5_no_git_add_dash_A_in_commit
case_5_no_auto_merge_pattern
case_5_no_bulk_pr_close
case_5_merge_no_default_to_main

exit_with_status
