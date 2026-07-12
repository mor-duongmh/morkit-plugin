#!/usr/bin/env bash
# Run the srs-to-jira pytest suite from run-all.sh's `test-*.sh` glob.
#
# Why a shim: CI only discovers test-*.sh, so the plugin's Python suites never run.
# For a renderer that is survivable. This skill holds a credential and writes to a
# live external system, and its guarantees — a refused approval sends zero requests,
# the token never reaches an error message, a re-run creates nothing — are pytest
# assertions. Unwatched, they rot into decoration.
#
# The interpreter is whichever one actually has the dependencies: the docs-hero venv
# on a developer's machine, the runner's python in CI. We *test* for pydantic rather
# than assume it, because a shim that silently skips is worse than no shim — it
# reports "pass" while checking nothing, which is the failure it exists to prevent.
#
# Scope is deliberately this skill only. The other suites collide on a shared `tests`
# package name and fixing that is not this change's job.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SUITE="${REPO_ROOT}/plugins/morkit/skills/srs-to-jira/tests"
VENV="${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data}}/docs-hero/.venv"

usable() {
    [ -x "$1" ] && "$1" -c "import pydantic, pytest" >/dev/null 2>&1
}

PY=""
for candidate in "${VENV}/bin/python3" "$(command -v python3 || true)" "$(command -v python || true)"; do
    if [ -n "$candidate" ] && usable "$candidate"; then
        PY="$candidate"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "test-srs-to-jira: SKIP (no interpreter with pydantic + pytest — run /morkit:setup)"
    exit 0
fi

"$PY" -m pytest "$SUITE" -q
rc=$?

if [ $rc -eq 0 ]; then
    echo "test-srs-to-jira: PASS ($("$PY" -V 2>&1))"
else
    echo "test-srs-to-jira: FAIL"
fi
exit $rc
