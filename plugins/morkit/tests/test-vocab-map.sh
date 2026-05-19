#!/usr/bin/env bash
# test-vocab-map.sh — validates codex/vocab-map.yaml (Task 3 of
# codex-fork-skills-clone).
#
# Cases covered:
#   1. YAML parses cleanly via python3 + PyYAML
#   2. Schema — top-level `rules:` array; each rule has id/type/pattern/
#      replacement/apply_to; top-level `preserve:` array exists
#   3. Rule IDs are unique
#   4. rule.type ∈ {literal, regex}
#   5. preserve list contains the 3 reference doc paths
#   6. Apply ALL rules to fixture text; assert exact swapped output
#   7. Every path in preserve actually exists under skills/
#   8. Regex edge — pattern matches "Skill tool" alone (no "Use the " prefix)
#   9. Bare "Agent tool" (no subagent_type=) → "subagent dispatch"
#  10. Ordering — "Agent tool with subagent_type=foo" still picks the regex
#      rule (agent-tool-dispatch) over the bare literal (agent-tool-bare)
#  11. Command suffix — "Invoke the `X` skill using the Skill tool." →
#      "Invoke the `X` skill." (skill-invocation-suffix runs first, so
#      skill-tool-invoke has nothing left to swap)
#  12. Command suffix — same but with "via" instead of "using"
#  13. Bold form — "Use the **Skill tool** to invoke X" →
#      "Use skill discovery to invoke X" (skill-tool-bold first, then
#      skill-tool-invoke is a no-op because "Skill tool" already gone)
#
# Dependencies: python3 + PyYAML (already a hard dep elsewhere in plugin).

set -uo pipefail

TEST_NAME="vocab-map"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

YAML="$TEST_PLUGIN_ROOT/codex/vocab-map.yaml"
SKILLS_DIR="$TEST_PLUGIN_ROOT/skills"

# Bail early if python3 / PyYAML unavailable — record as failure rather than
# silently passing.
if ! command -v python3 >/dev/null 2>&1; then
    _fail "python3 not available — cannot validate YAML"
    exit_with_status
    exit $?
fi
if ! python3 -c 'import yaml' >/dev/null 2>&1; then
    _fail "PyYAML not installed — cannot validate YAML"
    exit_with_status
    exit $?
fi

# ---------------------------------------------------------------------------
# Case 1 — YAML file exists and parses cleanly
# ---------------------------------------------------------------------------
case_1_parses() {
    assert_file_exists "$YAML" "1. vocab-map.yaml exists"
    local rc
    python3 -c "import yaml,sys; yaml.safe_load(open('$YAML'))" >/dev/null 2>&1
    rc=$?
    assert_equal "$rc" "0" "1. YAML parses without error"
}

# ---------------------------------------------------------------------------
# Case 2 — schema: rules array + required fields per rule; preserve array
# ---------------------------------------------------------------------------
case_2_schema() {
    local result
    result=$(python3 <<PY 2>/dev/null
import yaml
data = yaml.safe_load(open("$YAML"))
errs = []
if not isinstance(data, dict):
    errs.append("top-level-not-dict")
elif "rules" not in data or not isinstance(data["rules"], list):
    errs.append("missing-rules-array")
elif "preserve" not in data or not isinstance(data["preserve"], list):
    errs.append("missing-preserve-array")
else:
    required = ("id", "type", "pattern", "replacement", "apply_to")
    for i, r in enumerate(data["rules"]):
        for k in required:
            if k not in r:
                errs.append(f"rule[{i}]-missing-{k}")
        if "apply_to" in r and not isinstance(r["apply_to"], list):
            errs.append(f"rule[{i}]-apply_to-not-list")
print("OK" if not errs else ",".join(errs))
PY
)
    assert_equal "$result" "OK" "2. schema valid (rules + preserve + required fields)"
}

# ---------------------------------------------------------------------------
# Case 3 — rule IDs are unique
# ---------------------------------------------------------------------------
case_3_unique_ids() {
    local result
    result=$(python3 <<PY 2>/dev/null
import yaml
data = yaml.safe_load(open("$YAML"))
ids = [r["id"] for r in data["rules"]]
print("OK" if len(ids) == len(set(ids)) else "DUPLICATE:" + ",".join(sorted(set(x for x in ids if ids.count(x) > 1))))
PY
)
    assert_equal "$result" "OK" "3. all rule.id are unique"
}

# ---------------------------------------------------------------------------
# Case 4 — rule.type ∈ {literal, regex}
# ---------------------------------------------------------------------------
case_4_type_enum() {
    local result
    result=$(python3 <<PY 2>/dev/null
import yaml
data = yaml.safe_load(open("$YAML"))
allowed = {"literal", "regex"}
bad = [r["id"] for r in data["rules"] if r.get("type") not in allowed]
print("OK" if not bad else "BAD:" + ",".join(bad))
PY
)
    assert_equal "$result" "OK" "4. every rule.type is literal or regex"
}

# ---------------------------------------------------------------------------
# Case 5 — preserve has the 3 reference doc paths
# ---------------------------------------------------------------------------
case_5_preserve_list() {
    local result
    result=$(python3 <<PY 2>/dev/null
import yaml
data = yaml.safe_load(open("$YAML"))
need = {
    "using-morkit/references/codex-tools.md",
    "using-morkit/references/copilot-tools.md",
    "using-morkit/references/gemini-tools.md",
}
have = set(data["preserve"])
missing = need - have
print("OK" if not missing else "MISSING:" + ",".join(sorted(missing)))
PY
)
    assert_equal "$result" "OK" "5. preserve list contains 3 reference doc paths"
}

# ---------------------------------------------------------------------------
# Case 6 — apply all rules to fixture; assert exact swapped output
#
# Note on expected output: the literal rules `ExitPlanMode` and `NotebookEdit`
# match only the bare tool token, NOT the preceding "Use ". This is faithful
# to the YAML schema (type: literal, pattern: 'ExitPlanMode'). The "Use "
# prefix in the fixture intentionally remains in the expected output to
# exercise that boundary.
# ---------------------------------------------------------------------------
case_6_apply_fixture() {
    local result
    result=$(python3 <<PY 2>/dev/null
import yaml, re
data = yaml.safe_load(open("$YAML"))
text = ("Use the Skill tool to invoke X. "
        "Use the Agent tool with subagent_type=reviewer. "
        "Create TodoWrite per item. "
        "Use ExitPlanMode. "
        "Use NotebookEdit for notebooks.")
expected = ("skill discovery X. "
            "delegate to a reviewer specialist. "
            "Create task list per item. "
            "Use present plan and pause for confirmation. "
            "Use (no equivalent — skip) for notebooks.")
out = text
for r in data["rules"]:
    if r["type"] == "literal":
        out = out.replace(r["pattern"], r["replacement"])
    else:
        repl = re.sub(r"\\\$(\d+)", r"\\\\\1", r["replacement"])
        out = re.sub(r["pattern"], repl, out)
if out == expected:
    print("OK")
else:
    print("MISMATCH")
    print("GOT:", repr(out))
    print("EXP:", repr(expected))
PY
)
    local first_line
    first_line=$(printf '%s\n' "$result" | head -1)
    if [[ "$first_line" == "OK" ]]; then
        _pass "6. all rules applied → fixture swaps to expected output"
    else
        _fail "6. fixture swap mismatch — $result"
    fi
}

# ---------------------------------------------------------------------------
# Case 7 — every preserved path actually exists under skills/
# ---------------------------------------------------------------------------
case_7_preserve_paths_exist() {
    local paths
    paths=$(python3 -c "
import yaml
data = yaml.safe_load(open('$YAML'))
print('\n'.join(data['preserve']))
" 2>/dev/null)
    while IFS= read -r rel; do
        [[ -z "$rel" ]] && continue
        assert_file_exists "$SKILLS_DIR/$rel" "7. preserved path exists in skills/: $rel"
    done <<< "$paths"
}

# ---------------------------------------------------------------------------
# Case 8 — regex edge: "Skill tool" alone (no "Use the " prefix) still matches
# ---------------------------------------------------------------------------
case_8_regex_optional_prefix() {
    local result
    result=$(python3 <<PY 2>/dev/null
import yaml, re
data = yaml.safe_load(open("$YAML"))
rule = next(r for r in data["rules"] if r["id"] == "skill-tool-invoke")
text = "Skill tool"
expected = "skill discovery"
out = re.sub(rule["pattern"], rule["replacement"], text)
print("OK" if out == expected else f"MISMATCH:{out!r}")
PY
)
    assert_equal "$result" "OK" "8. regex matches bare 'Skill tool' (optional prefix)"
}

# ---------------------------------------------------------------------------
# Case 9 — bare "Agent tool" (no subagent_type=) → "subagent dispatch".
# This covers the agent-tool-bare literal rule added in Task 5. Applies all
# rules in declared order to reproduce realistic sync behavior.
# ---------------------------------------------------------------------------
case_9_agent_tool_bare() {
    local result
    result=$(python3 <<PY 2>/dev/null
import yaml, re
data = yaml.safe_load(open("$YAML"))
text = "Make multiple Agent tool calls in one message."
expected = "Make multiple subagent dispatch calls in one message."
out = text
for r in data["rules"]:
    if r["type"] == "literal":
        out = out.replace(r["pattern"], r["replacement"])
    else:
        repl = re.sub(r"\\\$(\d+)", r"\\\\\1", r["replacement"])
        out = re.sub(r["pattern"], repl, out)
print("OK" if out == expected else f"MISMATCH:{out!r}")
PY
)
    assert_equal "$result" "OK" "9. bare 'Agent tool' → 'subagent dispatch'"
}

# ---------------------------------------------------------------------------
# Case 10 — ordering regression guard: "Agent tool with subagent_type=foo"
# MUST be consumed by the regex rule (agent-tool-dispatch) BEFORE the bare
# literal (agent-tool-bare) can run. If the literal fired first, the output
# would be "subagent dispatch with subagent_type=foo" — wrong.
# ---------------------------------------------------------------------------
case_10_ordering_regex_wins() {
    local result
    result=$(python3 <<PY 2>/dev/null
import yaml, re
data = yaml.safe_load(open("$YAML"))
text = "Use the Agent tool with subagent_type=tester to verify."
expected = "delegate to a tester specialist to verify."
out = text
for r in data["rules"]:
    if r["type"] == "literal":
        out = out.replace(r["pattern"], r["replacement"])
    else:
        repl = re.sub(r"\\\$(\d+)", r"\\\\\1", r["replacement"])
        out = re.sub(r["pattern"], repl, out)
print("OK" if out == expected else f"MISMATCH:{out!r}")
PY
)
    assert_equal "$result" "OK" "10. regex rule wins over bare literal when qualifier present"
}

# ---------------------------------------------------------------------------
# Case 11 — command-file phrase: "Invoke the `X` skill using the Skill tool."
# must become "Invoke the `X` skill." The skill-invocation-suffix rule strips
# the trailing " using the Skill tool" so the bare-noun cleanup is unneeded
# and skill-tool-invoke has nothing left to match.
# ---------------------------------------------------------------------------
case_11_skill_suffix_using() {
    local result
    result=$(python3 <<PY 2>/dev/null
import yaml, re
data = yaml.safe_load(open("$YAML"))
text = "Invoke the \`propose\` skill using the Skill tool. Pass through any arguments."
expected = "Invoke the \`propose\` skill. Pass through any arguments."
out = text
for r in data["rules"]:
    if r["type"] == "literal":
        out = out.replace(r["pattern"], r["replacement"])
    else:
        repl = re.sub(r"\\\$(\d+)", r"\\\\\1", r["replacement"])
        out = re.sub(r["pattern"], repl, out)
print("OK" if out == expected else f"MISMATCH:{out!r}")
PY
)
    assert_equal "$result" "OK" "11. '... skill using the Skill tool.' → '... skill.'"
}

# ---------------------------------------------------------------------------
# Case 12 — same as 11 but with "via" instead of "using". The regex alternation
# (?:using|via) inside skill-invocation-suffix MUST handle both.
# ---------------------------------------------------------------------------
case_12_skill_suffix_via() {
    local result
    result=$(python3 <<PY 2>/dev/null
import yaml, re
data = yaml.safe_load(open("$YAML"))
text = "Invoke the \`deep-review\` skill via the Skill tool. Pass through args."
expected = "Invoke the \`deep-review\` skill. Pass through args."
out = text
for r in data["rules"]:
    if r["type"] == "literal":
        out = out.replace(r["pattern"], r["replacement"])
    else:
        repl = re.sub(r"\\\$(\d+)", r"\\\\\1", r["replacement"])
        out = re.sub(r["pattern"], repl, out)
print("OK" if out == expected else f"MISMATCH:{out!r}")
PY
)
    assert_equal "$result" "OK" "12. '... skill via the Skill tool.' → '... skill.'"
}

# ---------------------------------------------------------------------------
# Case 13 — bolded form: "Use the **Skill tool** to invoke X" must become
# "Use skill discovery to invoke X". skill-tool-bold consumes "the **Skill
# tool**" as a single unit, leaving "Use skill discovery to invoke X".
# Without this rule, skill-tool-invoke would only replace "Skill tool" and
# leave the asterisks behind.
# ---------------------------------------------------------------------------
case_13_skill_tool_bold() {
    local result
    result=$(python3 <<PY 2>/dev/null
import yaml, re
data = yaml.safe_load(open("$YAML"))
text = "Use the **Skill tool** to invoke \`docs-hero-orchestrator\` with mode init."
expected = "Use skill discovery to invoke \`docs-hero-orchestrator\` with mode init."
out = text
for r in data["rules"]:
    if r["type"] == "literal":
        out = out.replace(r["pattern"], r["replacement"])
    else:
        repl = re.sub(r"\\\$(\d+)", r"\\\\\1", r["replacement"])
        out = re.sub(r["pattern"], repl, out)
print("OK" if out == expected else f"MISMATCH:{out!r}")
PY
)
    assert_equal "$result" "OK" "13. 'Use the **Skill tool** to invoke X' → 'Use skill discovery to invoke X'"
}

case_1_parses
case_2_schema
case_3_unique_ids
case_4_type_enum
case_5_preserve_list
case_6_apply_fixture
case_7_preserve_paths_exist
case_8_regex_optional_prefix
case_9_agent_tool_bare
case_10_ordering_regex_wins
case_11_skill_suffix_using
case_12_skill_suffix_via
case_13_skill_tool_bold

exit_with_status
