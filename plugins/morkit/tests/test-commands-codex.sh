#!/usr/bin/env bash
# test-commands-codex.sh — assert plugins/morkit-codex/commands/ is a clean
# Codex-flavored mirror of commands/ (Task 6 of codex-fork-skills-clone).
#
# Invariants:
#   1. commands-codex/ exists and has the same .md file count as commands/
#   2. Every commands/X.md has a matching commands-codex/X.md
#   3. No file under commands-codex/ contains Claude-only vocab tokens
#      ("Skill tool", "Agent tool", "TodoWrite", "ExitPlanMode",
#      "NotebookEdit", " using the Skill tool", " via the Skill tool")
#   4. Spot-check: commands-codex/propose.md matches expected swap of the
#      known commands/propose.md phrase.
#   5. Spot-check: commands-codex/deep-review.md handles "via the Skill tool"
#      cleanup (different conjunction than propose.md).
#   6. Spot-check: commands-codex/init.md handles the bolded "**Skill tool**"
#      form correctly.
#
# Why a separate test from skills-codex-vocab:
#   commands/ has no preserve list (no reference docs about Claude). The
#   invariant is simpler: NO file should carry the legacy vocab. A dedicated
#   test keeps assertions targeted and failure messages specific to commands.
#
# Dependencies: bash, find, grep, diff/cmp.

set -uo pipefail

TEST_NAME="commands-codex"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

SRC_DIR="$TEST_PLUGIN_ROOT/commands"
CODEX_DIR="$TEST_PLUGIN_ROOT/../morkit-codex/commands"

# Bail early with a clear message if commands-codex/ wasn't built yet.
if [[ ! -d "$CODEX_DIR" ]]; then
    _fail "commands-codex/ not bootstrapped — run scripts/sync-codex-fork.sh \
--source <root>/commands --target <root>/commands-codex \
--baseline <root>/.codex/.drift-baseline-commands"
    exit_with_status
    exit $?
fi

# -----------------------------------------------------------------------------
# Assertion 1 — file count parity
# -----------------------------------------------------------------------------
src_count=$(find "$SRC_DIR" -maxdepth 1 -type f -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
tgt_count=$(find "$CODEX_DIR" -maxdepth 1 -type f -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
assert_equal "$tgt_count" "$src_count" "1. commands-codex/ has same .md count as commands/ ($src_count)"

# -----------------------------------------------------------------------------
# Assertion 2 — every commands/X.md has a matching commands-codex/X.md
# -----------------------------------------------------------------------------
missing=0
while IFS= read -r src; do
    base="$(basename "$src")"
    if [[ ! -f "$CODEX_DIR/$base" ]]; then
        missing=$((missing + 1))
        _fail "2. missing in commands-codex/: $base"
    fi
done < <(find "$SRC_DIR" -maxdepth 1 -type f -name '*.md' 2>/dev/null | sort)
if [[ "$missing" -eq 0 ]]; then
    _pass "2. every commands/*.md has a commands-codex/ counterpart"
fi

# -----------------------------------------------------------------------------
# Assertion 3 — no forbidden Claude vocab in any commands-codex/*.md
#
# Note: commands/ has no preserve list, so every file must be clean. The
# extended token list includes both the bare proper-noun tokens (caught by
# the generic skill-tool-invoke rule) AND the longer phrases that the new
# skill-invocation-suffix / skill-tool-bold rules strip (Task 6 additions).
# If any of these appear, either a rule regressed or sync wasn't re-run.
# -----------------------------------------------------------------------------
FORBIDDEN_TOKENS=(
    'Skill tool'
    'Agent tool'
    'TodoWrite'
    'ExitPlanMode'
    'NotebookEdit'
    ' using the Skill tool'
    ' via the Skill tool'
    '**Skill tool**'
)

violations=0
violation_details=""
files_checked=0

while IFS= read -r f; do
    files_checked=$((files_checked + 1))
    for tok in "${FORBIDDEN_TOKENS[@]}"; do
        if grep -Fq "$tok" "$f" 2>/dev/null; then
            violations=$((violations + 1))
            sample=$(grep -Fn "$tok" "$f" 2>/dev/null | head -1)
            rel="${f#"$CODEX_DIR/"}"
            violation_details+="    $rel:[$tok] $sample"$'\n'
        fi
    done
done < <(find "$CODEX_DIR" -maxdepth 1 -type f -name '*.md' 2>/dev/null | sort)

if [[ "$violations" -eq 0 ]]; then
    _pass "3. no forbidden Claude vocab in $files_checked commands-codex/*.md"
else
    _fail "3. found $violations vocab violations:
$violation_details"
fi

# -----------------------------------------------------------------------------
# Assertion 4 — spot-check propose.md content (uses " using the Skill tool")
# Expected swap: "Invoke the `propose` skill using the Skill tool. Pass..."
#             →  "Invoke the `propose` skill. Pass..."
# -----------------------------------------------------------------------------
propose_codex="$CODEX_DIR/propose.md"
if [[ -f "$propose_codex" ]]; then
    if grep -Fq 'Invoke the `propose` skill. Pass through any arguments' "$propose_codex"; then
        _pass "4. commands-codex/propose.md has clean swap (' using the Skill tool' stripped)"
    else
        sample=$(grep -F 'Invoke the' "$propose_codex" | head -1)
        _fail "4. commands-codex/propose.md missing expected clean swap. Got: $sample"
    fi
fi

# -----------------------------------------------------------------------------
# Assertion 5 — spot-check deep-review.md (uses " via the Skill tool")
# Expected swap: "Invoke the `deep-review` skill via the Skill tool. Pass..."
#             →  "Invoke the `deep-review` skill. Pass..."
# -----------------------------------------------------------------------------
dr_codex="$CODEX_DIR/deep-review.md"
if [[ -f "$dr_codex" ]]; then
    if grep -Fq 'Invoke the `deep-review` skill. Pass through any arguments' "$dr_codex"; then
        _pass "5. commands-codex/deep-review.md has clean swap (' via the Skill tool' stripped)"
    else
        sample=$(grep -F 'Invoke the' "$dr_codex" | head -1)
        _fail "5. commands-codex/deep-review.md missing expected clean swap. Got: $sample"
    fi
fi

# -----------------------------------------------------------------------------
# Assertion 6 — spot-check init.md (uses bolded "**Skill tool**")
# Expected swap: "Use the **Skill tool** to invoke `docs-hero-orchestrator`..."
#             →  "Use skill discovery to invoke `docs-hero-orchestrator`..."
# -----------------------------------------------------------------------------
init_codex="$CODEX_DIR/init.md"
if [[ -f "$init_codex" ]]; then
    if grep -Fq 'Use skill discovery to invoke `docs-hero-orchestrator`' "$init_codex"; then
        _pass "6. commands-codex/init.md has clean swap (bold **Skill tool** handled)"
    else
        sample=$(grep -F 'to invoke `docs-hero-orchestrator`' "$init_codex" | head -1)
        _fail "6. commands-codex/init.md missing expected clean swap. Got: $sample"
    fi
fi

exit_with_status
