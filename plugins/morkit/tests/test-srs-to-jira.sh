#!/usr/bin/env bash
# Run the srs-to-jira pytest suite from run-all.sh's `test-*.sh` glob.
#
# Why a shim: CI only discovers test-*.sh, so the plugin's Python suites never run.
# For a renderer that is survivable. This skill holds a credential and writes to a
# live external system, and its guarantees — a refused approval sends zero requests,
# the token never reaches an error message, a re-run creates nothing — are pytest
# assertions. Unwatched, they rot into decoration.
#
# Scope is deliberately this skill only. The other suites collide on a shared `tests`
# package name and fixing that is not this change's job.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SUITE="${REPO_ROOT}/plugins/morkit/skills/srs-to-jira/tests"
VENV="${MORKIT_DATA:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data}}/docs-hero/.venv"
PY="${VENV}/bin/python3"

if [[ ! -x "$PY" ]]; then
    echo "test-srs-to-jira: SKIP (docs-hero venv not built — run /morkit:setup)"
    exit 0
fi

"$PY" -m pytest "$SUITE" -q
rc=$?

if [[ $rc -eq 0 ]]; then
    echo "test-srs-to-jira: PASS"
else
    echo "test-srs-to-jira: FAIL"
fi
exit $rc
