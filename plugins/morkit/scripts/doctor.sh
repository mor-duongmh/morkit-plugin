#!/usr/bin/env bash
# doctor.sh — verify docs-hero installation health.

set -uo pipefail
# (no -e: we want to report all checks even if some fail)

VENV="${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data}}/docs-hero/.venv"
PLUGIN_ROOT="${MORKIT_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"

echo "=== docs-hero doctor ==="

# --- Python ---
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 9 ]; then
        echo "Python: OK ($PY_VER)"
    else
        echo "Python: FAIL (need 3.9+, found $PY_VER)"
    fi
else
    echo "Python: FAIL (python3 not in PATH)"
fi

# --- Venv ---
if [ -d "$VENV" ] && [ -x "$VENV/bin/python3" ]; then
    echo "venv: OK ($VENV)"
else
    echo "venv: MISSING — run /morkit:setup"
fi

# --- Deps ---
if [ -x "$VENV/bin/python3" ]; then
    if "$VENV/bin/python3" -c "import pydantic, markdown_it; from PIL import Image; import openpyxl, docx, pypdf, pdfplumber, pytest" 2>/dev/null; then
        echo "deps: OK (8 packages importable)"
    else
        echo "deps: FAIL — re-run /morkit:setup"
    fi
else
    echo "deps: SKIP (venv missing)"
fi

# --- Schema ---
if [ -x "$VENV/bin/python3" ] && [ -n "$PLUGIN_ROOT" ]; then
    SCHEMA="$PLUGIN_ROOT/skills/docs-hero-orchestrator/scripts/lib/normalized_schema.py"
    if [ -f "$SCHEMA" ] && "$VENV/bin/python3" -c "
import sys
sys.path.insert(0, '$PLUGIN_ROOT/skills/docs-hero-orchestrator/scripts')
from lib.normalized_schema import ProjectModel, Delta
" 2>/dev/null; then
        echo "schema: OK (ProjectModel + Delta importable)"
    else
        echo "schema: FAIL"
    fi
else
    echo "schema: SKIP (venv or MORKIT_PLUGIN_ROOT missing)"
fi

# --- mmdc (optional) ---
if command -v mmdc >/dev/null 2>&1; then
    MMDC_VER=$(mmdc --version 2>/dev/null || echo "?")
    echo "mmdc: OK ($MMDC_VER) — Mermaid validation will use CLI"
else
    echo "mmdc: not installed (optional) — agent uses syntax sanity check fallback"
fi

echo "=== done ==="
