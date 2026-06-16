#!/usr/bin/env bash
# verify-manifests.sh — Task 3 verification.
#
# The morkit plugin.json does NOT enumerate skills/commands as arrays; the
# Claude Code plugin loader auto-discovers them from skills/<name>/ dirs and
# commands/<name>.md files. So "plugin.json lists X" is verified here by the
# presence of the corresponding skill dir / command file on disk, plus the
# plugin.json description being free of writing-docs wording.
#
# Asserts:
#   - the 8 docs-hero skills are present (advertised via auto-discovery)
#   - the 6 docs-hero commands are present
#   - writing-docs skill + docs command are GONE
#   - key non-docs entries (review skill, propose/git commands) still present
#   - all three manifests are valid JSON and free of "writing-docs"
#
# Prints PASS/FAIL, exits non-zero on any failure.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd -P)"
cd "$REPO_ROOT" || { echo "FAIL: cannot cd to repo root"; exit 2; }

SKILLS="plugins/morkit/skills"
COMMANDS="plugins/morkit/commands"
PLUGIN_JSON="plugins/morkit/.claude-plugin/plugin.json"
MARKET_JSON=".claude-plugin/marketplace.json"
CODEX_JSON="plugins/morkit/.codex-plugin/plugin.json"

fail=0
note() { echo "OK: $1"; }
bad()  { echo "FAIL: $1"; fail=1; }

DOCS_HERO_SKILLS=(
  docs-hero-orchestrator
  generate-api-docs
  generate-code-standards
  generate-codebase-summary
  generate-db-design
  generate-design-guidelines
  generate-srs
  generate-system-architecture
)
DOCS_HERO_COMMANDS=(init sync doctor setup update-doc apply-sync)

# --- docs-hero skills present (8) --------------------------------------------
for s in "${DOCS_HERO_SKILLS[@]}"; do
  if [ -d "$SKILLS/$s" ]; then note "docs-hero skill present: $s"; else bad "docs-hero skill MISSING: $s"; fi
done

# --- docs-hero commands present (6) ------------------------------------------
for c in "${DOCS_HERO_COMMANDS[@]}"; do
  if [ -f "$COMMANDS/$c.md" ]; then note "docs-hero command present: $c"; else bad "docs-hero command MISSING: $c"; fi
done

# --- writing-docs / docs command GONE ----------------------------------------
if [ -e "$SKILLS/writing-docs" ]; then bad "writing-docs skill STILL present"; else note "writing-docs skill removed"; fi
if [ -e "$COMMANDS/docs.md" ]; then bad "/morkit:docs command (docs.md) STILL present"; else note "docs command removed"; fi

# --- key non-docs entries still present --------------------------------------
for s in review propose git deep-review brainstorming; do
  if [ -d "$SKILLS/$s" ]; then note "non-docs skill preserved: $s"; else bad "non-docs skill MISSING: $s"; fi
done
for c in propose git review deep-review archive; do
  if [ -f "$COMMANDS/$c.md" ]; then note "non-docs command preserved: $c"; else bad "non-docs command MISSING: $c"; fi
done

# --- manifests valid JSON + free of writing-docs -----------------------------
for f in "$PLUGIN_JSON" "$MARKET_JSON" "$CODEX_JSON"; do
  if jq -e . "$f" >/dev/null 2>&1; then note "valid JSON: $f"; else bad "INVALID JSON: $f"; fi
  if grep -q "writing-docs" "$f"; then bad "writing-docs wording still in: $f"; else note "no writing-docs wording: $f"; fi
done

# plugin.json description must mention docs-hero
if grep -q "docs-hero" "$PLUGIN_JSON"; then note "plugin.json advertises docs-hero"; else bad "plugin.json does not mention docs-hero"; fi

echo "----------------------------------------"
if [ "$fail" -eq 0 ]; then
  echo "PASS: manifests advertise docs-hero (8 skills + 6 commands), writing-docs/docs gone, non-docs preserved."
  exit 0
else
  echo "FAIL: manifest verification failed — see above."
  exit 1
fi
