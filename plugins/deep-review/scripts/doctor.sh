#!/usr/bin/env bash
# Deep Review plugin: health diagnostic.
set -u

ok()  { printf "  ✅ %s\n" "$*"; }
bad() { printf "  ❌ %s\n" "$*"; }
warn(){ printf "  ⚠️  %s\n" "$*"; }

echo "Deep Review — Health Check"
echo "=========================="

command -v git    >/dev/null 2>&1 && ok "git: $(git --version)"            || bad "git not found (required)"
command -v uvx    >/dev/null 2>&1 && ok "uvx: $(uvx --version 2>/dev/null)" || bad "uvx not found (required)"
command -v gh     >/dev/null 2>&1 && ok "gh: $(gh --version | head -1)"     || warn "gh not found (recommended for PR diff)"

if command -v uvx >/dev/null 2>&1; then
  CRG_VER=$(uvx --quiet code-review-graph --version 2>/dev/null || echo "")
  [ -n "${CRG_VER}" ] && ok "code-review-graph: ${CRG_VER}" || warn "code-review-graph not yet cached (will fetch on first run)"
fi

if [ -d ".git" ]; then
  ok "current dir is a git repo"
  [ -d ".code-review-graph" ] && ok "graph already built for this repo" || warn "graph not built — first /deep-review will trigger build"
  [ -f "CLAUDE.md" ] && ok "CLAUDE.md present (Tier-1 conventions will be honored)" || warn "no CLAUDE.md — falling back to language profile + universal rules"
else
  warn "current dir is not a git repo — /deep-review needs git context"
fi

echo
echo "Done."
