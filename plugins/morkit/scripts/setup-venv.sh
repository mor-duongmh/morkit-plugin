#!/usr/bin/env bash
# setup-venv.sh — create + populate docs-hero Python venv at user-shared location.
#
# Usage (from /morkit:setup slash command):
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/setup-venv.sh"
#
# Idempotent: re-running upgrades pinned deps to match requirements.txt.

set -euo pipefail

VENV="${HOME}/.claude/plugins/data/docs-hero/.venv"
REQ="${CLAUDE_PLUGIN_ROOT}/requirements.txt"

# --- Verify Python ≥ 3.9 ---
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found in PATH. Install Python 3.9+ first." >&2
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
    echo "ERROR: Python ≥ 3.9 required, found $PY_VER" >&2
    exit 1
fi

# --- Verify requirements.txt present ---
if [ ! -f "$REQ" ]; then
    echo "ERROR: requirements.txt not found at $REQ" >&2
    echo "Hint: \$CLAUDE_PLUGIN_ROOT must point to the docs-hero plugin root" >&2
    exit 1
fi

# --- Create venv if absent ---
mkdir -p "$(dirname "$VENV")"
if [ ! -d "$VENV" ]; then
    echo "[docs-hero] creating venv at $VENV ..."
    python3 -m venv "$VENV"
else
    echo "[docs-hero] venv exists, upgrading deps ..."
fi

# --- Install / upgrade deps ---
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r "$REQ"

# --- Verify imports ---
"$VENV/bin/python3" -c "
import pydantic, markdown_it
from PIL import Image
import openpyxl, docx, pypdf, pdfplumber, pytest
" || { echo "ERROR: dependency import verification failed" >&2; exit 1; }

echo "[docs-hero] venv ready: $VENV"
echo "[docs-hero] verify with /morkit:doctor"
