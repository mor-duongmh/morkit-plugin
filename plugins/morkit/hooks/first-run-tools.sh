#!/usr/bin/env bash
# morkit plugin — first-run companion tools check.
#
# Behaviour:
#   - Context7: nothing to install ahead of time. Skills invoke `npx -y ctx7 library`
#     and `npx -y ctx7 docs` lazily; npm caches the package on first use.
#     We just acknowledge readiness.
#   - RTK: cannot be installed silently (system binary, modifies user's
#     ~/.claude/settings.json via `rtk init -g`). We emit a one-time prompt
#     for Claude to ask the user; we never run the installer ourselves.
#
# State is tracked in plugin data dir (sentinel files):
#   - .tools-setup-done   : setup acknowledged (silent next time)
#   - .tools-setup-skip   : user said "don't ask again"
#
# This script never blocks: any failure exits 0 so the session continues.

set -euo pipefail

# Resolve plugin data dir. Claude Code exports CLAUDE_PLUGIN_DATA when running
# hooks; fall back to a deterministic path when invoked manually.
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data/spec}"
mkdir -p "$PLUGIN_DATA" 2>/dev/null || true

DONE_FLAG="$PLUGIN_DATA/.tools-setup-done"
SKIP_FLAG="$PLUGIN_DATA/.tools-setup-skip"

# Already finished or muted → nothing to emit.
[ -f "$DONE_FLAG" ] && exit 0
[ -f "$SKIP_FLAG" ] && exit 0

# Detect what's already there (so we tailor the prompt).
have_rtk=0
have_ctx7_mcp=0
command -v rtk >/dev/null 2>&1 && have_rtk=1
# Heuristic: settings.json mentions context7 MCP server URL → considered set up.
if [ -f "$HOME/.claude/settings.json" ] \
   && grep -q "mcp.context7.com" "$HOME/.claude/settings.json" 2>/dev/null; then
    have_ctx7_mcp=1
fi

# If everything is already in place, mark done quietly.
if [ "$have_rtk" -eq 1 ] && [ "$have_ctx7_mcp" -eq 1 ]; then
    touch "$DONE_FLAG" 2>/dev/null || true
    exit 0
fi

# Emit a single prompt block. Claude shows this once; the user replies; Claude
# then either runs the install commands explicitly or marks the prompt skipped.
cat <<EOF
<mor-companion-tools-first-run>
Mor plugin lần đầu chạy — kiểm tra companion tools:

- **Context7** (research API/library docs): $([ "$have_ctx7_mcp" -eq 1 ] && echo '✓ MCP đã cấu hình' || echo 'sẵn sàng dùng lazy qua \`npx -y ctx7 library\` + \`npx -y ctx7 docs\` (không cần setup trước)')
- **RTK** (giảm 60-90% tokens trên bash): $([ "$have_rtk" -eq 1 ] && echo '✓ đã cài' || echo '✗ chưa cài')

$( [ "$have_rtk" -eq 0 ] && cat <<'INNER'
Trong reply đầu tiên, hãy hỏi user qua AskUserQuestion:
"Cài RTK ngay? Lệnh sẽ chạy: \`curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh && rtk init -g\` (cài binary + add Claude Code hook)."
Options:
  - "Yes, install now" → chạy lệnh trên và touch \`$PLUGIN_DATA/.tools-setup-done\`
  - "Skip for now" → touch \`$PLUGIN_DATA/.tools-setup-done\` (không hỏi lại session sau)
  - "Don't ask again" → touch \`$PLUGIN_DATA/.tools-setup-skip\`

Quan trọng: KHÔNG tự chạy lệnh install; CHỈ chạy nếu user xác nhận "Yes, install now".
INNER
)
$( [ "$have_rtk" -eq 1 ] && [ "$have_ctx7_mcp" -eq 0 ] && cat <<'INNER'
Context7 đã ready dạng lazy (không cần action). Đánh dấu setup xong:
\`touch $PLUGIN_DATA/.tools-setup-done\`
INNER
)
</mor-companion-tools-first-run>
EOF
