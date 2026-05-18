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

case_1_parses
case_2_schema
case_3_unique_ids
case_4_type_enum
case_5_preserve_list
case_6_apply_fixture
case_7_preserve_paths_exist
case_8_regex_optional_prefix

exit_with_status
