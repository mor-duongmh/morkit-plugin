#!/usr/bin/env bash
# Mor spec plugin — SessionStart hook
#
# Two responsibilities:
#   1. Detect missing superpowers-driven schema in a project with openspec/ → prompt /spec:setup
#   2. First-run companion tools setup (Context7 lazy via npx; RTK ask once) → emit prompt
# Both responsibilities only EMIT suggestions — never write files or run installers silently.

set -euo pipefail

CWD="$(pwd)"
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ----------------------------------------------------------------------------
# Responsibility 1: Schema detection (existing behaviour)
# ----------------------------------------------------------------------------
if [ -d "$CWD/openspec" ] \
   && [ ! -d "$CWD/openspec/schemas/superpowers-driven" ] \
   && [ ! -f "$CWD/openspec/.spec-setup-skip" ]; then
    cat <<'EOF'
<spec-setup-suggestion>
This project has `openspec/` but the Mor `superpowers-driven` schema is not installed.

In your first reply, ask the user:
"Mor spec plugin phát hiện dự án này có OpenSpec nhưng chưa cài schema `superpowers-driven`. Chạy `/spec:setup` để cài không? (Reply 'skip' or create `openspec/.spec-setup-skip` to mute.)"

Only suggest — do not invoke /spec:setup or copy anything automatically.
</spec-setup-suggestion>
EOF
fi

# ----------------------------------------------------------------------------
# Responsibility 2: Companion tools first-run check
# ----------------------------------------------------------------------------
if [ -x "$HOOK_DIR/first-run-tools.sh" ]; then
    "$HOOK_DIR/first-run-tools.sh" || true   # never block session
fi
