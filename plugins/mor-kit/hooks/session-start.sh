#!/usr/bin/env bash
# mor-kit plugin — SessionStart hook (v2)
#
# Two responsibilities:
#   1. Detect legacy openspec/changes/ residual → prompt for migration
#   2. First-run companion tools setup (Context7 lazy via npx; RTK ask once) → emit prompt
#
# Both responsibilities only EMIT suggestions — never write files or run installers silently.

set -euo pipefail

CWD="$(pwd)"
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRIMARY="${MOR_KIT_ROOT:-mor-kit/changes}"

# ----------------------------------------------------------------------------
# Responsibility 1: Migration suggestion when legacy openspec/changes/ residual
# ----------------------------------------------------------------------------
if [ -d "$CWD/openspec/changes" ] \
   && [ ! -d "$CWD/$PRIMARY" ] \
   && [ ! -f "$CWD/openspec/.spec-migration-skip" ]; then
    # Resolve absolute migration script path so the user can copy-paste directly.
    MIGRATE_SCRIPT="$(cd "$HOOK_DIR/../scripts" 2>/dev/null && pwd)/migrate-from-openspec.sh"
    cat <<EOF
<spec-migration-suggestion>
This project has legacy \`openspec/changes/\` from mor-kit plugin v1 but no \`$PRIMARY/\`.

In your first reply, ask the user:
"mor-kit plugin v2 đã đổi convention sang \`$PRIMARY/\`. Phát hiện \`openspec/changes/\` cũ.

  Preview:  bash $MIGRATE_SCRIPT --dry-run
  Execute:  bash $MIGRATE_SCRIPT

Reply 'skip' or run \`touch openspec/.spec-migration-skip\` to mute."

Only suggest — do not run migration automatically.
</spec-migration-suggestion>
EOF
fi

# ----------------------------------------------------------------------------
# Responsibility 2: Companion tools first-run check
# ----------------------------------------------------------------------------
if [ -x "$HOOK_DIR/first-run-tools.sh" ]; then
    "$HOOK_DIR/first-run-tools.sh" || true   # never block session
fi
