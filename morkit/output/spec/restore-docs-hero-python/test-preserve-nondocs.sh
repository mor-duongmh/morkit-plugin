#!/usr/bin/env bash
# test-preserve-nondocs.sh — Preservation guard for Task 2 (restore docs-hero / remove writing-docs).
#
# Asserts the restore touched ONLY the intended surface vs the base commit e1ede2e:
#   (a) the 89 docs-hero paths in restore-manifest.txt  (restored)
#   (b) files under plugins/morkit/skills/writing-docs/  (removed)
#   (c) explicitly-reported orphans removed by Task 2    (NONE — see ORPHANS below)
# Any changed path outside that allow-list = FAIL.
#
# Also asserts the deferred files are UNCHANGED vs e1ede2e:
#   - plugins/morkit/.claude-plugin/plugin.json   (Task 3)
#   - .claude-plugin/marketplace.json             (Task 4)
#   - everything under docs/                        (Task 4)
#
# Prints PASS/FAIL, exits non-zero on any failure.

set -uo pipefail

BASE="e1ede2e"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd -P)"
cd "$REPO_ROOT" || { echo "FAIL: cannot cd to repo root"; exit 2; }

MANIFEST="morkit/output/spec/restore-docs-hero-python/restore-manifest.txt"
[ -f "$MANIFEST" ] || { echo "FAIL: manifest not found: $MANIFEST"; exit 2; }

# Orphans Task 2 explicitly removed beyond the writing-docs skill dir.
# Task 2 removed NONE (commands/docs.md kept-and-flagged due to references in
# kept files AGENTS.md / README.md / archive.md / brainstorming). Empty by design.
ORPHANS=()

fail=0

# --- Allow-list membership check ---------------------------------------------
# manifest real paths (strip comments + blank lines)
manifest_paths="$(grep -v '^#' "$MANIFEST" | grep -v '^[[:space:]]*$' | sort -u)"

is_allowed() {
  local path="$1"
  # (a) in manifest
  if printf '%s\n' "$manifest_paths" | grep -Fxq "$path"; then return 0; fi
  # (b) under writing-docs skill dir
  case "$path" in
    plugins/morkit/skills/writing-docs/*) return 0 ;;
  esac
  # (d) this change's own spec-folder artifacts (manifest, verify/test scripts,
  #     proposal/design/tasks). These belong to the restore-docs-hero change
  #     itself, not the protected plugin/docs surface.
  case "$path" in
    morkit/output/spec/restore-docs-hero-python/*) return 0 ;;
  esac
  # (c) explicit orphan
  local o
  for o in "${ORPHANS[@]:-}"; do
    [ -n "$o" ] && [ "$o" = "$path" ] && return 0
  done
  return 1
}

# All changed paths vs base (committed + working tree)
changed="$(git diff --name-only "$BASE" -- . | sort -u)"

violations=()
if [ -n "$changed" ]; then
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    if ! is_allowed "$p"; then
      violations+=("$p")
    fi
  done <<< "$changed"
fi

if [ "${#violations[@]}" -gt 0 ]; then
  echo "FAIL: ${#violations[@]} changed path(s) outside the allow-list:"
  printf '  - %s\n' "${violations[@]}"
  fail=1
else
  echo "OK: all changed paths are in {manifest, writing-docs/, declared orphans}"
fi

# --- Deferred-file immutability check ----------------------------------------
DEFERRED=(
  "plugins/morkit/.claude-plugin/plugin.json"
  ".claude-plugin/marketplace.json"
)
for f in "${DEFERRED[@]}"; do
  if [ -n "$(git diff --name-only "$BASE" -- "$f")" ]; then
    echo "FAIL: deferred file changed vs $BASE: $f"
    fail=1
  else
    echo "OK: deferred file unchanged: $f"
  fi
done

# docs/ tree must be untouched
docs_changed="$(git diff --name-only "$BASE" -- docs/ | sort -u)"
if [ -n "$docs_changed" ]; then
  echo "FAIL: docs/ tree changed vs $BASE:"
  printf '  - %s\n' "$docs_changed"
  fail=1
else
  echo "OK: docs/ tree unchanged"
fi

# --- Verdict -----------------------------------------------------------------
echo "----------------------------------------"
if [ "$fail" -eq 0 ]; then
  echo "PASS: non-docs-hero surface preserved (restore is surgical)."
  exit 0
else
  echo "FAIL: preservation violated — see above."
  exit 1
fi
