#!/usr/bin/env bash
# test-e2e-codex-fork.sh — end-to-end verification for the codex-fork-skills-clone
# pipeline (Task 10 of codex-fork-skills-clone).
#
# Verifies the full pipeline against the REAL repo artifacts (read-only, no
# writes to ~/, no actual install). Sandboxes any state via mktemp.
#
# Cases covered:
#   1. skills-codex/   regenerates identically from skills/   (no drift)
#   2. commands-codex/ regenerates identically from commands/ (no drift)
#   3. skills-codex/   contains no forbidden Claude-vocab tokens
#                      (preserve-listed reference docs excluded)
#   4. commands-codex/ contains no Skill-tool vocab
#   5. check-codex-drift.sh reports a clean exit + no WARN drift line
#   6. AGENTS.md mentions commands-codex/ and .codex/INSTALL.md mentions
#      skills-codex/ (docs in sync with the fork layout)
#   7. doctor-codex.sh runs to completion against a sandboxed HOME
#      (we don't enforce rc — sandbox is intentionally incomplete; we only
#      require it doesn't crash with rc > 1)
#
# Why a separate E2E suite:
#   Existing test-sync-codex-fork.sh / test-skills-codex-vocab.sh /
#   test-commands-codex.sh each cover one slice in isolation with synthetic
#   fixtures. This test wires the real artifacts together and asserts the
#   pipeline output is internally consistent and free of regressions a
#   contributor would notice mid-PR.

set -uo pipefail

TEST_NAME="e2e-codex-fork"
HELPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HELPER_DIR/test-helper.sh"

SYNC="$TEST_PLUGIN_ROOT/scripts/sync-codex-fork.sh"
DRIFT="$TEST_PLUGIN_ROOT/scripts/check-codex-drift.sh"
# Doctor now lives in sibling morkit-codex plugin (post-fix/codex-separate-plugin).
DOCTOR="$TEST_PLUGIN_ROOT/../morkit-codex/scripts/doctor-codex.sh"

# Quick preflight — fail fast with a useful message if any required artifact
# is missing rather than letting subsequent assertions emit cryptic errors.
for f in "$SYNC" "$DRIFT" "$DOCTOR"; do
    if [[ ! -f "$f" ]]; then
        _fail "preflight: missing script $f"
        exit_with_status
        exit $?
    fi
done

# Source dirs (CC plugin)
for d in skills commands; do
    if [[ ! -d "$TEST_PLUGIN_ROOT/$d" ]]; then
        _fail "preflight: missing dir $TEST_PLUGIN_ROOT/$d"
        exit_with_status
        exit $?
    fi
done
# Target dirs (Codex plugin sibling)
for d in skills commands .codex; do
    if [[ ! -d "$TEST_PLUGIN_ROOT/../morkit-codex/$d" ]]; then
        _fail "preflight: missing dir $TEST_PLUGIN_ROOT/../morkit-codex/$d"
        exit_with_status
        exit $?
    fi
done

# -----------------------------------------------------------------------------
# Case 1 — skills-codex/ regeneration is byte-identical to committed
# -----------------------------------------------------------------------------
# Regenerate into a tmp dir using a /dev/null baseline (we don't want to touch
# .codex/.drift-baseline). If diff reports any difference, the committed
# skills-codex/ is stale relative to skills/ — sync wasn't run.
#
# Exception — `--exclude SKILL.md` is NOT applied broadly; we only exempt the
# two files that carry a deliberate Codex-only manual edit (R1 fix: exporting
# MORKIT_CURRENT_CHANGE so pre-tool-checklist-gate.sh engages on apply_patch /
# Edit / Write under Codex). Those files are validated by Case 8 instead. All
# other SKILL.md files must still regenerate identically.
tmp_skills="$(mktemp -d)"
bash "$SYNC" \
    --source "$TEST_PLUGIN_ROOT/skills" \
    --target "$tmp_skills" \
    --baseline /dev/null \
    >/dev/null 2>&1 || true

# diff -r doesn't support per-path excludes, so we filter the brief output
# instead. Lines mentioning the two preserved-manual-edit files are dropped
# before checking for any remaining diff signal.
diff_raw="$(diff -r "$TEST_PLUGIN_ROOT/../morkit-codex/skills" "$tmp_skills" \
    --brief --exclude='.DS_Store' 2>&1 || true)"
diff_filtered="$(printf '%s\n' "$diff_raw" \
    | grep -v 'executing-plans/SKILL.md' \
    | grep -v 'subagent-driven-development/SKILL.md' \
    | sed '/^$/d')"

if [[ -z "$diff_filtered" ]]; then
    _pass "1. skills-codex/ regenerates identically from skills/ (modulo 2 preserved manual edits, checked in Case 8)"
else
    _fail "1. regenerated skills-codex/ differs from committed (drift detected)
        run: bash scripts/sync-codex-fork.sh
        diff sample:
$(printf '%s\n' "$diff_filtered" | head -10)"
fi
rm -rf "$tmp_skills"

# -----------------------------------------------------------------------------
# Case 2 — commands-codex/ regeneration is byte-identical to committed
# -----------------------------------------------------------------------------
# Note: commands/ has no preserve list — every .md is a SWAP candidate.
tmp_cmds="$(mktemp -d)"
bash "$SYNC" \
    --source "$TEST_PLUGIN_ROOT/commands" \
    --target "$tmp_cmds" \
    --baseline /dev/null \
    --exclude .claude-flow \
    >/dev/null 2>&1 || true

if diff -r "$TEST_PLUGIN_ROOT/../morkit-codex/commands" "$tmp_cmds" \
        --brief --exclude='.DS_Store' >/dev/null 2>&1; then
    _pass "2. commands-codex/ regenerates identically from commands/"
else
    diff_out="$(diff -r "$TEST_PLUGIN_ROOT/../morkit-codex/commands" "$tmp_cmds" \
        --brief --exclude='.DS_Store' 2>&1 | head -10)"
    _fail "2. regenerated commands-codex/ differs from committed (drift)
        run: bash scripts/sync-codex-fork.sh --source commands --target commands-codex
        diff sample:
$diff_out"
fi
rm -rf "$tmp_cmds"

# -----------------------------------------------------------------------------
# Case 3 — skills-codex/ vocab cleanliness (preserve list excluded)
# -----------------------------------------------------------------------------
# Forbidden tokens are Claude-only vocab that should never survive a swap.
# The using-morkit/references/ subtree is intentionally preserved verbatim
# (Codex-tools reference docs need original CC vocab for comparison), so we
# exclude it from this check.
hits="$(grep -rn -E "Skill tool|TodoWrite|ExitPlanMode" \
        "$TEST_PLUGIN_ROOT/../morkit-codex/skills" --include='*.md' 2>/dev/null \
        | grep -v 'using-morkit/references' \
        || true)"
if [[ -z "$hits" ]]; then
    _pass "3. skills-codex/ vocab clean (preserve list excluded)"
else
    _fail "3. forbidden vocab found in skills-codex/ (non-preserve files):
$(printf '%s\n' "$hits" | head -5)"
fi

# -----------------------------------------------------------------------------
# Case 4 — commands-codex/ vocab cleanliness (no preserve list at all)
# -----------------------------------------------------------------------------
hits="$(grep -rn -E "Skill tool|using the Skill tool|via the Skill tool" \
        "$TEST_PLUGIN_ROOT/../morkit-codex/commands" --include='*.md' 2>/dev/null \
        || true)"
if [[ -z "$hits" ]]; then
    _pass "4. commands-codex/ vocab clean"
else
    _fail "4. forbidden vocab found in commands-codex/:
$(printf '%s\n' "$hits" | head -5)"
fi

# -----------------------------------------------------------------------------
# Case 5 — check-codex-drift.sh reports a clean state
# -----------------------------------------------------------------------------
# Drift detector ALWAYS exits 0 by contract (WARN-only). Real signal is whether
# the output contains a "WARN" line about drift.
drift_out="$(bash "$DRIFT" 2>&1)"
drift_rc=$?
if [[ "$drift_rc" -eq 0 ]] && ! printf '%s\n' "$drift_out" | grep -qi "WARN.*drift"; then
    _pass "5. check-codex-drift.sh reports clean state (rc=$drift_rc, no WARN drift)"
else
    _fail "5. drift detector flagged issues (rc=$drift_rc):
$(printf '%s\n' "$drift_out" | head -10)"
fi

# -----------------------------------------------------------------------------
# Case 6 — docs reference the fork layout
# -----------------------------------------------------------------------------
# AGENTS.md is the Codex bridge — it must point at commands-codex/ so the
# bridge bullets resolve correctly.
# .codex/INSTALL.md is the Codex install guide — it must mention skills-codex/
# so users know which directory the symlink points at.
agents_ok=0
install_ok=0
if [[ -f "$TEST_PLUGIN_ROOT/../morkit-codex/AGENTS.md" ]] \
        && grep -q "morkit-codex/commands" "$TEST_PLUGIN_ROOT/../morkit-codex/AGENTS.md"; then
    agents_ok=1
fi
if [[ -f "$TEST_PLUGIN_ROOT/../morkit-codex/.codex/INSTALL.md" ]] \
        && grep -q "morkit-codex/skills" "$TEST_PLUGIN_ROOT/../morkit-codex/.codex/INSTALL.md"; then
    install_ok=1
fi
if [[ "$agents_ok" -eq 1 ]] && [[ "$install_ok" -eq 1 ]]; then
    _pass "6. AGENTS.md + .codex/INSTALL.md reference fork dirs"
else
    msg="6. docs missing fork references:"
    [[ "$agents_ok" -eq 0 ]] && msg="$msg AGENTS.md lacks 'morkit-codex/commands';"
    [[ "$install_ok" -eq 0 ]] && msg="$msg .codex/INSTALL.md lacks 'morkit-codex/skills';"
    _fail "$msg"
fi

# -----------------------------------------------------------------------------
# Case 7 — doctor-codex.sh smoke test against a sandboxed HOME
# -----------------------------------------------------------------------------
# Build a minimal fake install layout:
#   $sandbox/.agents/skills/morkit -> $PLUGIN_ROOT/../morkit-codex/skills
#   $sandbox/.codex/AGENTS.md      -> $PLUGIN_ROOT/../morkit-codex/AGENTS.md
# Then run doctor with HOME overridden. We don't enforce a specific rc — the
# sandbox is intentionally missing the shell rc block + codex CLI, so doctor
# WILL report FAILs and exit non-zero. Goal of this case is to assert the
# script runs to completion without a hard crash (rc < 100, no stack trace).
sandbox="$(mktemp -d)"
mkdir -p "$sandbox/.agents/skills" "$sandbox/.codex"
ln -s "$TEST_PLUGIN_ROOT/../morkit-codex/skills" "$sandbox/.agents/skills/morkit"
ln -s "$TEST_PLUGIN_ROOT/../morkit-codex/AGENTS.md"    "$sandbox/.codex/AGENTS.md"

doctor_out="$(HOME="$sandbox" \
    AGENTS_HOME="$sandbox/.agents" \
    CODEX_HOME="$sandbox/.codex" \
    MORKIT_PLUGIN_ROOT="$TEST_PLUGIN_ROOT" \
    bash "$DOCTOR" 2>&1)"
doctor_rc=$?

# Accept any rc 0..99 — sandbox is incomplete by design so non-zero is
# expected. We just verify the script ran (produced its banner) and didn't
# blow up with a bash error.
if [[ "$doctor_rc" -lt 100 ]] \
        && printf '%s\n' "$doctor_out" | grep -q "morkit Codex doctor"; then
    _pass "7. doctor-codex.sh runs to completion in sandbox (rc=$doctor_rc)"
else
    _fail "7. doctor-codex.sh crashed or produced no output (rc=$doctor_rc):
$(printf '%s\n' "$doctor_out" | head -10)"
fi
rm -rf "$sandbox"

# -----------------------------------------------------------------------------
# Case 8 — R1 fix: executing-plans skills export MORKIT_CURRENT_CHANGE
# -----------------------------------------------------------------------------
# pre-tool-checklist-gate.sh narrows the Codex matcher (apply_patch|Edit|Write)
# by checking MORKIT_CURRENT_CHANGE — if unset, the gate fails open. The
# executing-plans + subagent-driven-development skills are responsible for
# exporting it before any file mutation. If either skill stops mentioning the
# env var, the gate becomes structurally inert under Codex (R1 regression).
exec_skill="$TEST_PLUGIN_ROOT/../morkit-codex/skills/executing-plans/SKILL.md"
sub_skill="$TEST_PLUGIN_ROOT/../morkit-codex/skills/subagent-driven-development/SKILL.md"
missing=()
if ! grep -q 'MORKIT_CURRENT_CHANGE' "$exec_skill" 2>/dev/null; then
    missing+=("executing-plans/SKILL.md")
fi
if ! grep -q 'MORKIT_CURRENT_CHANGE' "$sub_skill" 2>/dev/null; then
    missing+=("subagent-driven-development/SKILL.md")
fi
if [[ ${#missing[@]} -eq 0 ]]; then
    _pass "8. Codex executing-plans skills export MORKIT_CURRENT_CHANGE (gate engages)"
else
    _fail "8. R1 regression — MORKIT_CURRENT_CHANGE missing from: ${missing[*]}
        Without it, pre-tool-checklist-gate.sh fails open on apply_patch/Edit/Write
        under Codex and the checklist gate is structurally inert."
fi

exit_with_status
