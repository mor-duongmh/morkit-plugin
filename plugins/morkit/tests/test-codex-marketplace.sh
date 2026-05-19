#!/usr/bin/env bash
# test-codex-marketplace.sh — verify Codex native plugin marketplace files exist + valid.
#
# Coverage:
#   1. .agents/plugins/marketplace.json (repo root) exists + valid JSON + has morkit entry
#   2. plugins/morkit/.codex-plugin/plugin.json exists + valid JSON + skills/hooks paths exist
#   3. plugin.json schema sanity (required top-level fields)
#   4. README + INSTALL.md mention the new `codex plugin marketplace add` command

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

MARKETPLACE_JSON="$REPO_ROOT/.agents/plugins/marketplace.json"
PLUGIN_JSON="$PLUGIN_ROOT/.codex-plugin/plugin.json"

# --- Case 1: marketplace.json ---
_case "marketplace.json at repo root"
if [[ -f "$MARKETPLACE_JSON" ]]; then
    _pass "file exists at $MARKETPLACE_JSON"
else
    _fail "missing: $MARKETPLACE_JSON"
fi

if python3 -c "import json; json.load(open('$MARKETPLACE_JSON'))" 2>/dev/null; then
    _pass "valid JSON"
else
    _fail "invalid JSON"
fi

if python3 -c "
import json, sys
d = json.load(open('$MARKETPLACE_JSON'))
plugins = d.get('plugins', [])
names = [p.get('name') for p in plugins]
sys.exit(0 if 'morkit' in names else 1)
" 2>/dev/null; then
    _pass "contains morkit plugin entry"
else
    _fail "morkit not found in plugins array"
fi

if python3 -c "
import json, sys
d = json.load(open('$MARKETPLACE_JSON'))
morkit = next((p for p in d.get('plugins', []) if p.get('name') == 'morkit'), {})
src = morkit.get('source', {})
sys.exit(0 if src.get('source') == 'local' and src.get('path') == './plugins/morkit' else 1)
" 2>/dev/null; then
    _pass "morkit source.path = ./plugins/morkit"
else
    _fail "morkit source mismatch"
fi

# --- Case 2: plugin.json ---
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

# --- Case 3: paths declared in plugin.json actually exist ---
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

# --- Case 4: docs mention the new command ---
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
