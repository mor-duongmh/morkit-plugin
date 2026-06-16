#!/usr/bin/env bash
# session-start.sh — detect-only hint when docs-hero venv missing.
# Never auto-creates venv (would block session startup with 30-60s pip install).

set -uo pipefail

VENV="${HOME}/.claude/plugins/data/docs-hero/.venv"
STATE_DIR="${HOME}/.claude/plugins/data/docs-hero"
HINT_SHOWN="${STATE_DIR}/.first-run-hint-shown"

mkdir -p "$STATE_DIR"

if [ ! -d "$VENV" ] && [ ! -f "$HINT_SHOWN" ]; then
    echo "[docs-hero] venv not initialized. Run /morkit:setup to bootstrap (~30-60s)." >&2
    touch "$HINT_SHOWN"
fi

exit 0
