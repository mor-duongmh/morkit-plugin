#!/usr/bin/env bash
# verify-manifest.sh
#
# Asserts that restore-manifest.txt is sane for the docs-hero restore:
#   1. Every manifest path is restorable from 4cb3d35~1 (exists in that tree).
#   2. The manifest contains the required docs-hero dirs / commands / scripts.
#   3. Reports parity of docs-hero skill dirs between 4cb3d35~1 and running cache.
#
# Exits non-zero on any assertion failure. Run from anywhere inside the repo.

set -u

REF="4cb3d35~1"
SRC_COMMIT="4cb3d35"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$SCRIPT_DIR/restore-manifest.txt"
CACHE_SKILLS="$HOME/.claude/plugins/cache/mor-duongmh/morkit/1.1.0/skills"

fail=0
pass_count=0

note_pass() { pass_count=$((pass_count + 1)); }
note_fail() { echo "FAIL: $1"; fail=$((fail + 1)); }

# --- Preconditions -----------------------------------------------------------
if [ ! -f "$MANIFEST" ]; then
  echo "FAIL: manifest not found at $MANIFEST"
  exit 1
fi
if ! git rev-parse --verify -q "$REF^{commit}" >/dev/null; then
  echo "FAIL: ref $REF does not resolve"
  exit 1
fi

# Strip comments/blank lines to get the path list.
PATHS="$(grep -v '^#' "$MANIFEST" | grep -v '^[[:space:]]*$')"
TOTAL="$(printf '%s\n' "$PATHS" | grep -c . )"

# Snapshot the ref tree once.
TREE="$(git ls-tree -r --name-only "$REF")"

# --- Check 1: every manifest path is restorable from REF ---------------------
missing=0
while IFS= read -r p; do
  [ -z "$p" ] && continue
  if ! printf '%s\n' "$TREE" | grep -qxF "$p"; then
    note_fail "manifest path not present at $REF: $p"
    missing=$((missing + 1))
  fi
done <<< "$PATHS"
if [ "$missing" -eq 0 ]; then
  note_pass
  echo "OK: all $TOTAL manifest paths exist at $REF (restorable)."
fi

# --- Check 2: required key paths present in manifest -------------------------
require() {
  local needle="$1"
  if printf '%s\n' "$PATHS" | grep -qF "$needle"; then
    note_pass
  else
    note_fail "manifest missing required entry: $needle"
  fi
}

# Orchestrator dir
require "plugins/morkit/skills/docs-hero-orchestrator/"

# The 7 generate-* skill dirs
for g in generate-api-docs generate-code-standards generate-codebase-summary \
         generate-db-design generate-design-guidelines generate-srs \
         generate-system-architecture; do
  require "plugins/morkit/skills/$g/"
done

# The 6 commands
for c in init.md sync.md doctor.md setup.md update-doc.md apply-sync.md; do
  require "plugins/morkit/commands/$c"
done

# The 2 scripts
require "plugins/morkit/scripts/doctor.sh"
require "plugins/morkit/scripts/setup-venv.sh"

# --- Check 3: parity cross-check (report only, never fails build) ------------
echo ""
echo "--- Parity cross-check: docs-hero skill dirs ($REF vs running cache) ---"
if [ -d "$CACHE_SKILLS" ]; then
  ref_skills="$(printf '%s\n' "$TREE" \
    | grep '^plugins/morkit/skills/' \
    | sed -E 's#plugins/morkit/skills/([^/]+)/.*#\1#' | sort -u)"
  cache_skills="$(ls -1 "$CACHE_SKILLS" | sort -u)"
  only_ref="$(comm -23 <(printf '%s\n' "$ref_skills") <(printf '%s\n' "$cache_skills"))"
  only_cache="$(comm -13 <(printf '%s\n' "$ref_skills") <(printf '%s\n' "$cache_skills"))"
  if [ -z "$only_ref" ] && [ -z "$only_cache" ]; then
    echo "PARITY OK: skill dirs identical between $REF and cache 1.1.0."
  else
    [ -n "$only_ref" ]   && echo "Only at $REF:"   && printf '  %s\n' $only_ref
    [ -n "$only_cache" ] && echo "Only in cache:"  && printf '  %s\n' $only_cache
  fi
else
  echo "NOTE: running cache not found at $CACHE_SKILLS — parity check skipped."
fi

# --- Summary -----------------------------------------------------------------
echo ""
echo "============================================"
echo "source commit : $SRC_COMMIT"
echo "restore ref   : $REF"
echo "manifest paths: $TOTAL"
echo "checks passed : $pass_count"
echo "checks failed : $fail"
if [ "$fail" -eq 0 ]; then
  echo "RESULT: PASS"
  echo "============================================"
  exit 0
else
  echo "RESULT: FAIL"
  echo "============================================"
  exit 1
fi
