#!/usr/bin/env bash
# morkit deep-review — Codex CLI parallel wrapper
#
# Mimics Claude Code's /morkit:deep-review by spawning N `codex exec` processes
# in parallel, each running one specialist agent prompt against the same diff.
# Aggregates YAML-Markdown findings into a unified Markdown or JSON report.
#
# Usage:
#   codex-deep-review.sh                    # default: git diff HEAD
#   codex-deep-review.sh --diff             # same as above
#   codex-deep-review.sh --diff <ref>       # git diff <ref>...HEAD
#   codex-deep-review.sh '#123'             # PR #123 via gh
#   codex-deep-review.sh 123                # PR #123 (number alone)
#   codex-deep-review.sh --json             # emit JSON instead of Markdown
#   codex-deep-review.sh --agents=a,b,c     # subset of specialists
#
# Requirements:
#   - codex CLI ≥ 0.120.0
#   - git (always); gh (only for PR targets)
#   - python3 (aggregator)
#
# Exit codes:
#   0  review completed (regardless of findings severity)
#   1  bad input / missing tool
#   2  empty diff
#   3  all specialists failed

set -euo pipefail

# ---------- Resolve plugin root ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AGGREGATOR="$SCRIPT_DIR/codex-deep-review-aggregate.py"

# ---------- Defaults ----------
TARGET=""
OUTPUT_FORMAT="markdown"
AGENTS_FILTER=""
DEFAULT_AGENTS=(
  risk-impact-analyst
  security-auditor
  pattern-architecture-critic
  test-coverage-auditor
  convention-checker
  performance-auditor
  documentation-auditor
)

# ---------- Parse args ----------
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --json)        OUTPUT_FORMAT="json"; shift ;;
      --agents=*)    AGENTS_FILTER="${1#*=}"; shift ;;
      --diff)        TARGET="--diff"; shift
                     if [[ $# -gt 0 && ! "$1" =~ ^-- ]]; then
                       TARGET="--diff $1"; shift
                     fi ;;
      -h|--help)     usage; exit 0 ;;
      \#*|[0-9]*)    TARGET="$1"; shift ;;
      *)             echo "Unknown arg: $1" >&2; usage; exit 1 ;;
    esac
  done
  [[ -z "$TARGET" ]] && TARGET="--diff"
  return 0
}

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \?//'
}

# ---------- Resolve diff ----------
resolve_diff() {
  local diff_text
  case "$TARGET" in
    \#[0-9]*|[0-9]*)
      local pr_num="${TARGET#\#}"
      command -v gh >/dev/null 2>&1 || {
        echo "❌ PR target requires gh CLI: brew install gh && gh auth login" >&2
        exit 1
      }
      diff_text="$(gh pr diff "$pr_num" 2>/dev/null)" || {
        echo "❌ Failed to fetch PR #$pr_num diff" >&2
        exit 1
      }
      ;;
    "--diff")
      diff_text="$(git diff HEAD 2>/dev/null)"
      ;;
    "--diff "*)
      local ref="${TARGET#--diff }"
      diff_text="$(git diff "$ref...HEAD" 2>/dev/null)" || {
        echo "❌ Failed to compute git diff $ref...HEAD" >&2
        exit 1
      }
      ;;
    *)
      echo "❌ Unsupported target: $TARGET" >&2; exit 1
      ;;
  esac
  [[ -z "$diff_text" ]] && { echo "No changes to review." >&2; exit 2; }
  echo "$diff_text"
}

# ---------- Build specialist list ----------
build_agent_list() {
  if [[ -n "$AGENTS_FILTER" ]]; then
    IFS=',' read -ra AGENTS <<< "$AGENTS_FILTER"
  else
    AGENTS=("${DEFAULT_AGENTS[@]}")
  fi
  for a in "${AGENTS[@]}"; do
    [[ -f "$PLUGIN_ROOT/agents/$a.md" ]] || {
      echo "❌ Unknown agent: $a (no $PLUGIN_ROOT/agents/$a.md)" >&2; exit 1
    }
  done
}

# ---------- Detect languages from diff ----------
detect_languages() {
  local diff="$1"
  echo "$diff" | grep -oE '^[+-]{3} [ab]/.+\.[a-zA-Z]+' | \
    sed 's/.*\.//' | sort -u | tr '\n' ',' | sed 's/,$//'
}

# ---------- Spawn one specialist ----------
run_specialist() {
  local agent="$1"
  local diff="$2"
  local langs="$3"
  local outfile="$4"
  local agent_md="$PLUGIN_ROOT/agents/$agent.md"
  local promptfile="$outfile.prompt"

  # Build prompt without any shell expansion of agent_md / diff contents
  {
    printf '%s\n' "You are running as the \"$agent\" specialist subagent for a morkit deep-review."
    printf '%s\n\n' ""
    printf '%s\n' "Your role definition follows (between AGENT_DEF markers):"
    printf '%s\n' "==== AGENT_DEF START ===="
    cat "$agent_md"
    printf '\n%s\n\n' "==== AGENT_DEF END ===="
    printf '%s\n' "Detected languages in this diff: $langs"
    printf '%s\n\n' "Universal Tier-3 rules apply (SOLID/DRY/KISS/YAGNI)."
    printf '%s\n' "Codex environment notes:"
    printf '%s\n' "- code-review-graph MCP may not be available; fall back to Read/Grep"
    printf '%s\n' "- CLAUDE.md (if present in repo) is the highest source of truth (Tier 1)"
    printf '%s\n\n' "- Output MUST be a single YAML-Markdown findings block, nothing else"
    printf '%s\n\n' "Output format (MANDATORY — emit exactly this YAML, no prose, no markdown headers):"
    cat <<'YAML_BLOCK'
```yaml
findings:
  - id: <category-letter><n>          # S1, R1, P1, T1, C1, Pf1, D1
    category: Security|Risk|Pattern|Tests|Convention|Performance|Documentation
    severity: Critical|High|Medium|Low|Info
    file: path/to/file
    line: <number>
    title: <short>
    detail: <longer>
    source: <CLAUDE.md:L<n>|profile:<lang>|universal:<rule>|graph:<query>|OWASP:<id>>
    suggested_fix: <code or text>
    confidence: <0-100>
```

If you find nothing in your category, emit:
```yaml
findings: []
```

YAML_BLOCK
    printf '%s\n' "Review this diff:"
    printf '%s\n' "==== DIFF START ===="
    printf '%s\n' "$diff"
    printf '%s\n' "==== DIFF END ===="
  } > "$promptfile"

  codex exec \
    --skip-git-repo-check \
    --sandbox read-only \
    --output-last-message "$outfile" \
    -c 'suppress_unstable_features_warning=true' \
    - <"$promptfile" >"$outfile.log" 2>&1
}

# ---------- Main ----------
main() {
  parse_args "$@"
  build_agent_list

  command -v codex >/dev/null 2>&1 || { echo "❌ codex CLI not found" >&2; exit 1; }
  command -v python3 >/dev/null 2>&1 || { echo "❌ python3 not found" >&2; exit 1; }
  [[ -f "$AGGREGATOR" ]] || { echo "❌ Aggregator missing: $AGGREGATOR" >&2; exit 1; }

  echo "🔍 morkit deep-review (Codex) — target: $TARGET" >&2
  local diff
  diff="$(resolve_diff)"
  local langs
  langs="$(detect_languages "$diff")"
  echo "📝 Languages detected: ${langs:-none}" >&2
  echo "👥 Specialists: ${AGENTS[*]}" >&2

  WORKDIR="$(mktemp -d -t morkit-deep-review-XXXXXX)"
  trap 'rm -rf "$WORKDIR"' EXIT
  local workdir="$WORKDIR"

  # Fan out specialists
  local pids=()
  for agent in "${AGENTS[@]}"; do
    echo "  ⏳ dispatching $agent..." >&2
    run_specialist "$agent" "$diff" "$langs" "$workdir/$agent.out" &
    pids+=($!)
  done

  # Wait, count survivors
  local survivors=0
  for i in "${!pids[@]}"; do
    if wait "${pids[$i]}" 2>/dev/null; then
      survivors=$((survivors + 1))
      echo "  ✅ ${AGENTS[$i]} done" >&2
    else
      echo "  ⚠️  ${AGENTS[$i]} failed (see $workdir/${AGENTS[$i]}.out.log)" >&2
    fi
  done

  [[ $survivors -eq 0 ]] && { echo "❌ All specialists failed" >&2; exit 3; }

  # Aggregate
  echo "📊 Aggregating $survivors specialist outputs..." >&2
  python3 "$AGGREGATOR" \
    --format="$OUTPUT_FORMAT" \
    --target="$TARGET" \
    --workdir="$workdir" \
    --agents="$(IFS=,; echo "${AGENTS[*]}")"
}

main "$@"
