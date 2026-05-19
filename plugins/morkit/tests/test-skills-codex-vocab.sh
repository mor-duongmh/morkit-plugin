#!/usr/bin/env bash
# test-skills-codex-vocab.sh — assert plugins/morkit-codex/skills/ is clean of
# Claude-specific vocab (Task 5 of codex-fork-skills-clone).
#
# Two-sided invariant:
#   - Every non-preserved *.md under skills-codex/ MUST NOT contain Claude-only
#     tokens (Skill tool / Agent tool / TodoWrite / ExitPlanMode / NotebookEdit).
#     If it does, the vocab-map swap is incomplete or sync wasn't re-run.
#   - Every preserved file (preserve list in vocab-map.yaml) MUST still contain
#     the legacy vocab — confirms PRESERVE actually preserved.
#
# Why this lives outside test-vocab-map.sh:
#   test-vocab-map.sh validates the YAML rules in isolation (Task 3). This test
#   validates the END STATE of the synced tree (Task 5). They catch different
#   classes of regression: one breaks if rules malform, the other breaks if
#   anyone hand-edits skills-codex/ or forgets to re-sync after a vocab change.

set -uo pipefail

TEST_NAME="skills-codex-vocab"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

CODEX_DIR="$TEST_PLUGIN_ROOT/../morkit-codex/skills"
VOCAB_MAP="$TEST_PLUGIN_ROOT/codex/vocab-map.yaml"

# Bail with clear message if skills-codex/ is missing (e.g. running pre-bootstrap).
if [[ ! -d "$CODEX_DIR" ]]; then
    _fail "skills-codex/ not bootstrapped — run scripts/sync-codex-fork.sh first"
    exit_with_status
    exit $?
fi

# Tokens that MUST NOT appear in swapped output. Case-sensitive on purpose:
# "skill" lowercase is fine (e.g. "skill discovery"), only the proper-noun
# "Skill tool" / "Agent tool" / TodoWrite etc are Claude-specific.
FORBIDDEN_TOKENS=(
    'Skill tool'
    'Agent tool'
    'TodoWrite'
    'ExitPlanMode'
    'NotebookEdit'
)

# Load preserve list from vocab-map.yaml — these files are EXPECTED to keep
# the legacy vocab (they're reference docs about Claude).
PRESERVE_LIST=()
if command -v python3 >/dev/null 2>&1 && python3 -c 'import yaml' >/dev/null 2>&1; then
    while IFS= read -r line; do
        [[ -n "$line" ]] && PRESERVE_LIST+=("$line")
    done < <(python3 -c "
import yaml, sys
with open('$VOCAB_MAP') as fh:
    data = yaml.safe_load(fh) or {}
for p in (data.get('preserve') or []):
    print(p)
" 2>/dev/null)
else
    _fail "python3 + PyYAML required to load preserve list"
    exit_with_status
    exit $?
fi

# Is a relative path in the preserve list?
_is_preserved() {
    local rel="$1" p
    for p in "${PRESERVE_LIST[@]}"; do
        [[ "$rel" == "$p" ]] && return 0
    done
    return 1
}

# -----------------------------------------------------------------------------
# Assertion 1 — every non-preserved *.md is free of forbidden tokens.
# -----------------------------------------------------------------------------
violations=0
violation_details=""
files_checked=0

while IFS= read -r f; do
    rel="${f#"$CODEX_DIR/"}"
    if _is_preserved "$rel"; then
        continue
    fi
    files_checked=$((files_checked + 1))
    for tok in "${FORBIDDEN_TOKENS[@]}"; do
        # grep -F fixed-string, -q quiet — exit 0 on match
        if grep -Fq "$tok" "$f" 2>/dev/null; then
            violations=$((violations + 1))
            # Capture first matching line for the report
            sample=$(grep -Fn "$tok" "$f" 2>/dev/null | head -1)
            violation_details+="    $rel:[$tok] $sample"$'\n'
        fi
    done
done < <(find "$CODEX_DIR" -type f -name '*.md' 2>/dev/null | sort)

if [[ "$violations" -eq 0 ]]; then
    _pass "1. no forbidden Claude vocab in $files_checked non-preserved *.md file(s)"
else
    _fail "1. found $violations vocab violations across non-preserved files:
$violation_details"
fi

# -----------------------------------------------------------------------------
# Assertion 2 — preserve list files still carry legacy vocab (sanity check
# that PRESERVE action actually preserved, didn't accidentally swap).
# -----------------------------------------------------------------------------
preserved_checked=0
preserve_sanity_failures=0

for rel in "${PRESERVE_LIST[@]}"; do
    f="$CODEX_DIR/$rel"
    if [[ ! -f "$f" ]]; then
        # Preserved file listed in map but absent from target — only flag if
        # source actually has the file (otherwise the preserve entry is stale).
        if [[ -f "$TEST_PLUGIN_ROOT/skills/$rel" ]]; then
            preserve_sanity_failures=$((preserve_sanity_failures + 1))
            _fail "2. preserved file missing from skills-codex/: $rel"
        fi
        continue
    fi
    preserved_checked=$((preserved_checked + 1))
    # At least one legacy token should appear — these files document Claude tools.
    found_any=0
    for tok in "${FORBIDDEN_TOKENS[@]}"; do
        if grep -Fq "$tok" "$f" 2>/dev/null; then
            found_any=1
            break
        fi
    done
    if [[ "$found_any" -ne 1 ]]; then
        # Some preserve files may legitimately not mention any forbidden token
        # (e.g. copilot-tools.md describes Copilot, not Claude). Don't fail —
        # just note. Real sanity is byte-equality with source, checked next.
        :
    fi

    # Byte-for-byte equality with source — the strongest preserve invariant.
    src="$TEST_PLUGIN_ROOT/skills/$rel"
    if [[ -f "$src" ]]; then
        if ! cmp -s "$src" "$f"; then
            preserve_sanity_failures=$((preserve_sanity_failures + 1))
            _fail "2. preserved file diverged from source: $rel"
        fi
    fi
done

if [[ "$preserve_sanity_failures" -eq 0 ]]; then
    _pass "2. all $preserved_checked preserved file(s) byte-identical to source"
fi

exit_with_status
