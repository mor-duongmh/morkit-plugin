#!/usr/bin/env bash
# test-codex-marketplace.sh — verify Codex plugin manifest (plugin.json) + CC marketplace.json
# dual-discoverability without duplicate plugin registration.
#
# Background: Codex CLI requires .agents/plugins/marketplace.json with its own schema
# (source/policy as objects) to discover marketplace plugins. CC uses
# .claude-plugin/marketplace.json with a different schema. Single-source: both
# marketplaces point at the one `plugins/morkit/` plugin (the morkit-codex fork is
# retired). The Codex marketplace lists `morkit` (source ./plugins/morkit), and the
# Codex plugin manifest lives at plugins/morkit/.codex-plugin/plugin.json.
#
# Coverage:
#   1. plugin.json exists + valid JSON + required fields
#   2. plugin.json paths (skills, hooks) resolve to real files/dirs
#   3. .agents/plugins/marketplace.json present + valid Codex schema, lists morkit only
#   4. CC marketplace.json present + parseable
#   5. README + INSTALL.md mention the `codex plugin marketplace add` command

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/../.." && pwd)"

PASSED=0
FAILED=0
TOTAL=0

_pass() { PASSED=$((PASSED+1)); TOTAL=$((TOTAL+1)); echo "  ✓ $1"; }
_fail() { FAILED=$((FAILED+1)); TOTAL=$((TOTAL+1)); echo "  ✗ $1" >&2; }
_case() { echo; echo "Case: $1"; }

PLUGIN_JSON="$PLUGIN_ROOT/.codex-plugin/plugin.json"
CC_MARKETPLACE="$REPO_ROOT/.claude-plugin/marketplace.json"
CODEX_MARKETPLACE="$REPO_ROOT/.agents/plugins/marketplace.json"

# --- Case 1: plugin.json present + valid ---
_case "plugin.json in plugin folder"
if [[ -f "$PLUGIN_JSON" ]]; then
    _pass "file exists at $PLUGIN_JSON"
else
    _fail "missing: $PLUGIN_JSON"
fi

if python3 -c "import json; json.load(open('$PLUGIN_JSON'))" 2>/dev/null; then
    _pass "valid JSON"
else
    _fail "invalid JSON"
fi

# Required top-level fields per Codex plugin.json spec
for field in name version description author repository license skills hooks interface; do
    if python3 -c "
import json, sys
d = json.load(open('$PLUGIN_JSON'))
sys.exit(0 if '$field' in d else 1)
" 2>/dev/null; then
        _pass "has required field '$field'"
    else
        _fail "missing field '$field'"
    fi
done

# --- Case 2: plugin.json paths resolve ---
_case "plugin.json paths resolve to real files/dirs"

SKILLS_PATH=$(python3 -c "import json; print(json.load(open('$PLUGIN_JSON'))['skills'])" 2>/dev/null)
HOOKS_PATH=$(python3 -c "import json; print(json.load(open('$PLUGIN_JSON'))['hooks'])" 2>/dev/null)

if [[ -d "$PLUGIN_ROOT/${SKILLS_PATH#./}" ]]; then
    _pass "skills path resolves: $SKILLS_PATH"
else
    _fail "skills path missing: $SKILLS_PATH (resolved: $PLUGIN_ROOT/${SKILLS_PATH#./})"
fi

if [[ -f "$PLUGIN_ROOT/${HOOKS_PATH#./}" ]]; then
    _pass "hooks path resolves: $HOOKS_PATH"
else
    _fail "hooks path missing: $HOOKS_PATH (resolved: $PLUGIN_ROOT/${HOOKS_PATH#./})"
fi

# --- Case 3: Codex marketplace.json present + valid + lists the single morkit plugin ---
_case "Codex marketplace.json at .agents/plugins/"
if [[ -f "$CODEX_MARKETPLACE" ]]; then
    _pass "file exists at $CODEX_MARKETPLACE"
else
    _fail "missing: $CODEX_MARKETPLACE — Codex marketplace discovery requires this file"
fi

if python3 -c "import json; json.load(open('$CODEX_MARKETPLACE'))" 2>/dev/null; then
    _pass "valid JSON"
else
    _fail "invalid JSON"
fi

# Lists the single `morkit` plugin (source ./plugins/morkit). Source must be Codex
# object schema (path field), not a bare string.
if python3 -c "
import json, sys
d = json.load(open('$CODEX_MARKETPLACE'))
plugins = d.get('plugins', [])
names = sorted(p.get('name','') for p in plugins)
if names != ['morkit']:
    print(f'  expected [morkit], got {names}', file=sys.stderr)
    sys.exit(1)
# source must be object, not string (Codex schema requirement)
src = plugins[0].get('source')
if not isinstance(src, dict) or 'path' not in src:
    print(f'  source must be object with path field, got: {src!r}', file=sys.stderr)
    sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
    _pass "lists ONLY morkit with Codex object-schema source"
else
    _fail "wrong plugins list or invalid source schema"
fi

# --- Case 4: CC marketplace.json (used by both CC and Codex) ---
_case "Claude Code marketplace.json (also read by Codex)"
if [[ -f "$CC_MARKETPLACE" ]]; then
    _pass "file exists at $CC_MARKETPLACE"
else
    _fail "missing: $CC_MARKETPLACE — both CC and Codex install paths would break"
fi

if python3 -c "import json; json.load(open('$CC_MARKETPLACE'))" 2>/dev/null; then
    _pass "valid JSON"
else
    _fail "invalid JSON"
fi

if python3 -c "
import json, sys
d = json.load(open('$CC_MARKETPLACE'))
plugins = d.get('plugins', [])
names = [p.get('name') for p in plugins]
sys.exit(0 if 'morkit' in names else 1)
" 2>/dev/null; then
    _pass "contains morkit plugin entry"
else
    _fail "morkit not found in plugins array"
fi

# --- Case 5: docs mention the marketplace command ---
_case "docs mention 'codex plugin marketplace add'"

if grep -q "codex plugin marketplace add" "$PLUGIN_ROOT/README.md"; then
    _pass "README.md mentions the marketplace add command"
else
    _fail "README.md missing 'codex plugin marketplace add'"
fi

if grep -q "codex plugin marketplace add" "$PLUGIN_ROOT/.codex/INSTALL.md"; then
    _pass "INSTALL.md mentions the marketplace add command"
else
    _fail "INSTALL.md missing 'codex plugin marketplace add'"
fi

# --- Summary ---
echo
echo "================================================"
if [[ $FAILED -eq 0 ]]; then
    echo "✓ codex-marketplace — $PASSED/$TOTAL passed"
    exit 0
else
    echo "✗ codex-marketplace — $FAILED/$TOTAL FAILED ($PASSED passed)"
    exit 1
fi
