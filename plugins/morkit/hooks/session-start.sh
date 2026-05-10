#!/usr/bin/env bash
# morkit plugin — SessionStart hook
#
# Single responsibility:
#   First-run companion tools setup (Context7 lazy via npx; RTK ask once) → emit prompt
#
# Only EMITS suggestions — never writes files or runs installers silently.

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -x "$HOOK_DIR/first-run-tools.sh" ]; then
    "$HOOK_DIR/first-run-tools.sh" || true   # never block session
fi
