#!/usr/bin/env bash
# test-env-cascade.sh
#
# Verifies that every active reference to CLAUDE_PLUGIN_ROOT, CLAUDE_PLUGIN_DATA,
# and the hardcoded `~/.claude/plugins/data` data path inside in-scope files is
# wrapped in the MORKIT_PLUGIN_ROOT / MORKIT_DATA cascade introduced by Task 1
# of the codex-fork-skills-clone change.
#
# Cascade patterns expected:
#   bash:   ${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}
#           ${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data...}}
#   python: os.environ.get("MORKIT_PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")
#
# A reference is considered "active" if it is NOT:
#   - inside a shell/python comment line (after stripping leading whitespace)
#   - already inside a MORKIT_PLUGIN_ROOT / MORKIT_DATA cascade
#   - a CLAUDE_PLUGIN_DATA reference that is the inner fallback of a MORKIT_DATA
#     cascade (counted as cascaded)
#   - inside a known excluded reference doc (using-morkit/references/*-tools.md)
#
# Standalone — not sourced by run-all.sh by default. Run directly:
#   bash plugins/morkit/tests/test-env-cascade.sh

set -uo pipefail

TEST_NAME="env-cascade"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/../.." && pwd)"

PASS_COUNT=0
FAIL_COUNT=0
OFFENDERS=()

# ---------------------------------------------------------------------------
# Scope: files that MUST use the cascade.
# Paths are relative to repo root for stable reporting.
# ---------------------------------------------------------------------------
SCOPE_FILES=(
    # scripts (8)
    "plugins/morkit/scripts/doctor.sh"
    "plugins/morkit/scripts/scaffold-change.sh"
    "plugins/morkit/scripts/setup-venv.sh"
    "plugins/morkit/scripts/migrate-from-openspec.sh"
    "plugins/morkit/scripts/install-codex.sh"
    "plugins/morkit/scripts/doctor-codex.sh"
    "plugins/morkit/scripts/lib/common.sh"
    "plugins/morkit/scripts/fetch-checklist.sh"

    # hooks (5)
    "plugins/morkit/hooks/hooks.json"
    "plugins/morkit/hooks/pre-tool-checklist-gate.sh"
    "plugins/morkit/hooks/dh-session-start.sh"
    "plugins/morkit/hooks/first-run-tools.sh"
    "plugins/morkit/hooks/session-start.sh"

    # skills SKILL.md (auto-discovered below — kept dynamic so newly-added
    # skills also get linted)

    # python (1)
    "plugins/morkit/skills/docs-hero-orchestrator/scripts/dispatch_coordinator.py"
)

# Dynamic skill discovery (every SKILL.md under plugins/morkit/skills/)
while IFS= read -r f; do
    SCOPE_FILES+=("$f")
done < <(cd "$REPO_ROOT" && find plugins/morkit/skills -maxdepth 3 -name SKILL.md -type f 2>/dev/null | sort)

# Files that are documentation describing the OLD vocab on purpose — skip.
EXCLUDE_PATTERNS=(
    "plugins/morkit/skills/using-morkit/references/codex-tools.md"
    "plugins/morkit/skills/using-morkit/references/copilot-tools.md"
    "plugins/morkit/skills/using-morkit/references/gemini-tools.md"
)

is_excluded() {
    local f="$1" p
    for p in "${EXCLUDE_PATTERNS[@]}"; do
        [[ "$f" == "$p" ]] && return 0
    done
    return 1
}

# ---------------------------------------------------------------------------
# Per-line classifier — returns 0 if line is OK, 1 if it's an offender.
# Args:
#   $1 — file extension hint (sh/json/md/py)
#   $2 — raw line content
# ---------------------------------------------------------------------------
line_is_ok() {
    local ext="$1" line="$2"

    # Strip leading whitespace for comment detection.
    local trimmed="${line#"${line%%[![:space:]]*}"}"

    # Comment line in bash/json/python — skip.
    if [[ "$ext" == "sh" || "$ext" == "json" ]]; then
        [[ "$trimmed" == \#* ]] && return 0
    fi
    if [[ "$ext" == "py" ]]; then
        [[ "$trimmed" == \#* ]] && return 0
    fi

    # Does this line contain any flagged reference?
    local has_pr_ref=0 has_pd_ref=0 has_data_path=0
    [[ "$line" == *CLAUDE_PLUGIN_ROOT* ]] && has_pr_ref=1
    [[ "$line" == *CLAUDE_PLUGIN_DATA* ]] && has_pd_ref=1
    [[ "$line" == *".claude/plugins/data"* ]] && has_data_path=1

    if (( has_pr_ref == 0 && has_pd_ref == 0 && has_data_path == 0 )); then
        return 0
    fi

    # Python rule: must be cascaded via MORKIT_PLUGIN_ROOT or be a comment-like
    # docstring (handled above). The cascaded form contains
    #   os.environ.get("MORKIT_PLUGIN_ROOT")
    # and CLAUDE_PLUGIN_ROOT may legitimately appear later on the same line.
    if [[ "$ext" == "py" ]]; then
        if (( has_pr_ref == 1 )); then
            [[ "$line" == *"MORKIT_PLUGIN_ROOT"* ]] && return 0
            return 1
        fi
        return 0
    fi

    # Bash / json / markdown rules.
    if (( has_pr_ref == 1 )); then
        # Acceptable forms (any one is sufficient):
        #   ${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}
        #   ${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-...}}  (extended fallback)
        if [[ "$line" == *'${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT'* ]]; then
            :
        # Also accept "CLAUDE_PLUGIN_ROOT" appearing inside an echo / error
        # message that itself references the cascade (rare) — match by also
        # accepting lines that contain MORKIT_PLUGIN_ROOT somewhere.
        elif [[ "$line" == *"MORKIT_PLUGIN_ROOT"* ]]; then
            :
        else
            return 1
        fi
    fi

    if (( has_pd_ref == 1 )); then
        # CLAUDE_PLUGIN_DATA must live inside the MORKIT_DATA cascade.
        if [[ "$line" == *'${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA'* ]]; then
            :
        elif [[ "$line" == *"MORKIT_DATA"* ]]; then
            :
        else
            return 1
        fi
    fi

    if (( has_data_path == 1 )); then
        # Hardcoded ~/.claude/plugins/data must live inside MORKIT_DATA cascade
        # OR be the inner default of one. Accept any line that mentions
        # MORKIT_DATA. Bare HOME-based paths without cascade are offenders.
        if [[ "$line" == *"MORKIT_DATA"* ]]; then
            :
        else
            return 1
        fi
    fi

    return 0
}

# ---------------------------------------------------------------------------
# Lint a single file.
# ---------------------------------------------------------------------------
lint_file() {
    local rel="$1"
    local abs="$REPO_ROOT/$rel"

    if [[ ! -f "$abs" ]]; then
        # Not all files in scope may exist (e.g. python file optional). Skip silently.
        return 0
    fi

    local ext="${rel##*.}"
    case "$ext" in
        sh|json|py|md) ;;
        *) ext="sh" ;;
    esac

    local lineno=0 line
    local file_offenders=()
    while IFS= read -r line; do
        lineno=$((lineno + 1))
        if ! line_is_ok "$ext" "$line"; then
            file_offenders+=("$rel:$lineno: $line")
        fi
    done < "$abs"

    if (( ${#file_offenders[@]} == 0 )); then
        PASS_COUNT=$((PASS_COUNT + 1))
        return 0
    fi

    FAIL_COUNT=$((FAIL_COUNT + 1))
    local o
    for o in "${file_offenders[@]}"; do
        OFFENDERS+=("$o")
    done
}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
printf '== %s ==\n' "$TEST_NAME"

for f in "${SCOPE_FILES[@]}"; do
    if is_excluded "$f"; then
        continue
    fi
    lint_file "$f"
done

if (( FAIL_COUNT == 0 )); then
    printf 'PASS  %d files clean\n' "$PASS_COUNT"
    exit 0
fi

printf 'FAIL  %d clean, %d files with offending lines (total %d violations)\n' \
    "$PASS_COUNT" "$FAIL_COUNT" "${#OFFENDERS[@]}"
printf -- '---\n'
for o in "${OFFENDERS[@]}"; do
    printf '  %s\n' "$o"
done
exit 1
