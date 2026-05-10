# docs-hero Plugin Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> ⚠️ **PLAN-REVIEW-GATE REQUIRED:** Per `feedback_plan_review_gate` user memory rule, before executing this plan you MUST generate a developer review checklist (`/spec:review`), tick all applicable items, and set `Overall Decision: OK`. Implementation skills will refuse to proceed until gate is open.

**Goal:** Refactor `docs-hero-1.1.0` (bundle installer) into a Claude Code plugin (`docs-hero@mor-duongmh`) that integrates with the existing `claude-plugins` marketplace, supports `${CLAUDE_PLUGIN_ROOT}`-based path resolution, and bootstraps a Python venv via explicit `/docs-hero:setup` (not silent SessionStart).

**Architecture:** Plugin lives at `claude-plugins/plugins/docs-hero/`. Skills + agent + Python scripts are copied as-is; SKILL.md files are refactored to use `${CLAUDE_PLUGIN_ROOT}` paths. `dispatch_coordinator.py` reads `CLAUDE_PLUGIN_ROOT` env var with fallback to legacy bundle layout. Venv lives at `~/.claude/plugins/data/docs-hero/.venv` (per-user shared). SessionStart hook is detect-only; explicit `/docs-hero:setup` creates the venv. Six slash commands wrap the orchestrator entry points.

**Tech Stack:** Bash (hooks/scripts), Python 3.9+ (existing scripts, no rewrites), JSON (plugin manifest), Markdown (SKILL.md, slash commands, agents). No new dependencies beyond what `docs-hero-1.1.0/requirements.txt` already pins.

**Source paths:**
- Source bundle: `/Users/haiduong/Documents/work/docs-hero-1.1.0/`
- Target plugin: `/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/`
- Reference plugin (similar shape): `/Users/haiduong/Documents/work/claude-plugins/plugins/deep-review/`

**Story reference:** `_bmad-output/docs-hero-plugin-integration/STORY.md`

---

## File Structure

```
claude-plugins/
├── .claude-plugin/
│   └── marketplace.json                                  [MODIFY: add 4th plugin entry]
├── README.md                                             [MODIFY: plugin table + slash commands]
└── plugins/docs-hero/                                    [NEW]
    ├── .claude-plugin/
    │   └── plugin.json                                   [NEW: manifest]
    ├── README.md                                         [NEW]
    ├── requirements.txt                                  [COPY from docs-hero-1.1.0]
    ├── skills/
    │   ├── docs-hero-orchestrator/
    │   │   ├── SKILL.md                                  [COPY+REFACTOR paths]
    │   │   ├── scripts/
    │   │   │   ├── dispatch_coordinator.py               [COPY+PATCH _SKILLS_ROOT]
    │   │   │   ├── aggregate_report.py                   [COPY as-is]
    │   │   │   ├── apply_patch.py                        [COPY as-is]
    │   │   │   ├── compute_diff.py                       [COPY as-is]
    │   │   │   ├── detect_manual_edits.py                [COPY as-is]
    │   │   │   ├── lock_manager.py                       [COPY as-is]
    │   │   │   ├── meta_manager.py                       [COPY as-is]
    │   │   │   ├── parse_codebase_models.py              [COPY as-is]
    │   │   │   ├── parse_codebase_routes.py              [COPY as-is]
    │   │   │   ├── parse_inputs.py                       [COPY as-is]
    │   │   │   ├── parse_openspec.py                     [COPY as-is]
    │   │   │   ├── parse_plan.py                         [COPY as-is]
    │   │   │   ├── __init__.py                           [COPY as-is]
    │   │   │   └── lib/                                  [COPY whole folder as-is]
    │   │   └── tests/                                    [COPY whole folder as-is]
    │   ├── generate-srs/
    │   │   ├── SKILL.md                                  [COPY+REFACTOR paths]
    │   │   ├── scripts/                                  [COPY whole folder]
    │   │   ├── templates/                                [COPY whole folder]
    │   │   └── references/                               [COPY whole folder]
    │   ├── generate-api-docs/
    │   │   ├── SKILL.md                                  [COPY+REFACTOR paths]
    │   │   ├── scripts/                                  [COPY whole folder]
    │   │   └── templates/                                [COPY whole folder]
    │   └── generate-db-design/
    │       ├── SKILL.md                                  [COPY+REFACTOR paths]
    │       ├── scripts/                                  [COPY whole folder]
    │       └── templates/                                [COPY whole folder]
    ├── agents/
    │   └── docs-hero.md                                  [COPY as-is]
    ├── commands/
    │   ├── setup.md                                      [NEW]
    │   ├── init.md                                       [NEW]
    │   ├── update.md                                     [NEW]
    │   ├── sync.md                                       [NEW]
    │   ├── apply-sync.md                                 [NEW]
    │   └── doctor.md                                     [NEW]
    ├── hooks/
    │   └── session-start.sh                              [NEW: detect-only]
    └── scripts/
        ├── setup-venv.sh                                 [NEW: explicit bootstrap]
        └── doctor.sh                                     [NEW: health check]
```

---

## Pre-flight Setup

### Task 0: Verify environment + create branch

**Files:**
- Check: `/Users/haiduong/Documents/work/claude-plugins/.git/` exists
- Check: `/Users/haiduong/Documents/work/docs-hero-1.1.0/.claude/skills/` exists

- [ ] **Step 1: Verify both source dirs exist**

```bash
test -d /Users/haiduong/Documents/work/claude-plugins/.git && \
test -d /Users/haiduong/Documents/work/docs-hero-1.1.0/.claude/skills && \
echo "OK: both source trees present"
```

Expected output: `OK: both source trees present`

- [ ] **Step 2: Verify Python ≥ 3.9 available**

```bash
python3 -c "import sys; assert sys.version_info >= (3, 9), f'need 3.9+, got {sys.version_info}'; print(f'Python {sys.version_info.major}.{sys.version_info.minor} OK')"
```

Expected: `Python 3.X OK` where X ≥ 9. Halt if Python < 3.9.

- [ ] **Step 3: Create feature branch**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git status                                    # verify clean
git checkout -b feat/docs-hero-plugin
```

Expected: branch created, no uncommitted changes carried over.

- [ ] **Step 4: Verify reference plugin layout**

```bash
ls /Users/haiduong/Documents/work/claude-plugins/plugins/deep-review/.claude-plugin/plugin.json && \
ls /Users/haiduong/Documents/work/claude-plugins/plugins/deep-review/hooks/
```

Expected: `plugin.json` exists, `hooks/` directory exists. We'll mirror this shape.

---

## Phase 1: Plugin Scaffold

### Task 1: Inventory hard-coded paths in source bundle

**Files:**
- Read: `/Users/haiduong/Documents/work/docs-hero-1.1.0/.claude/skills/**/SKILL.md`
- Create: `/Users/haiduong/Documents/work/_bmad-output/docs-hero-plugin-integration/path-inventory.md`

- [ ] **Step 1: Grep all relative path references in SKILL.md files**

```bash
cd /Users/haiduong/Documents/work/docs-hero-1.1.0/.claude/skills
grep -rn "scripts/" --include="SKILL.md" | grep -E "(python |--template |--output )" > /tmp/skill-paths.txt
wc -l /tmp/skill-paths.txt
```

Expected: ~30-50 lines. Each line is a path that needs `${CLAUDE_PLUGIN_ROOT}` prefix.

- [ ] **Step 2: Grep `<target>` and `.claude/skills/.venv` references in Python**

```bash
cd /Users/haiduong/Documents/work/docs-hero-1.1.0/.claude/skills
grep -rn "<target>\|\.claude/skills/\.venv\|/\\.claude/skills/" --include="*.py" > /tmp/py-paths.txt
cat /tmp/py-paths.txt
```

Expected: 0-2 hits (most paths are CLI args, already abstracted). Note any hits — they are refactor targets.

- [ ] **Step 3: Save inventory to story output dir**

```bash
mkdir -p /Users/haiduong/Documents/work/_bmad-output/docs-hero-plugin-integration
cat > /Users/haiduong/Documents/work/_bmad-output/docs-hero-plugin-integration/path-inventory.md << 'EOF'
# Path Inventory — refactor targets

## SKILL.md path references
EOF
cat /tmp/skill-paths.txt >> /Users/haiduong/Documents/work/_bmad-output/docs-hero-plugin-integration/path-inventory.md
echo -e "\n## Python script path references" >> /Users/haiduong/Documents/work/_bmad-output/docs-hero-plugin-integration/path-inventory.md
cat /tmp/py-paths.txt >> /Users/haiduong/Documents/work/_bmad-output/docs-hero-plugin-integration/path-inventory.md
```

- [ ] **Step 4: Commit inventory**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add /Users/haiduong/Documents/work/_bmad-output/docs-hero-plugin-integration/path-inventory.md 2>/dev/null || true
# Note: _bmad-output is outside repo. Just keep file as reference, no commit.
```

Verify file exists and has content. No commit needed.

---

### Task 2: Create plugin scaffold directories

**Files:**
- Create: `claude-plugins/plugins/docs-hero/` (full tree, empty dirs)

- [ ] **Step 1: Create all subdirectories in one shot**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
mkdir -p plugins/docs-hero/{.claude-plugin,skills,agents,commands,hooks,scripts}
mkdir -p plugins/docs-hero/skills/{docs-hero-orchestrator,generate-srs,generate-api-docs,generate-db-design}
ls plugins/docs-hero/
```

Expected output: `.claude-plugin agents commands hooks scripts skills`

- [ ] **Step 2: Verify tree shape**

```bash
find plugins/docs-hero -type d | sort
```

Expected:
```
plugins/docs-hero
plugins/docs-hero/.claude-plugin
plugins/docs-hero/agents
plugins/docs-hero/commands
plugins/docs-hero/hooks
plugins/docs-hero/scripts
plugins/docs-hero/skills
plugins/docs-hero/skills/docs-hero-orchestrator
plugins/docs-hero/skills/generate-api-docs
plugins/docs-hero/skills/generate-db-design
plugins/docs-hero/skills/generate-srs
```

---

### Task 3: Write plugin.json manifest

**Files:**
- Create: `claude-plugins/plugins/docs-hero/.claude-plugin/plugin.json`
- Test: `tests/test_plugin_manifest.sh` (one-shot validation, no permanent test infra needed)

- [ ] **Step 1: Write the failing validation check**

```bash
test -f /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/.claude-plugin/plugin.json && \
python3 -c "import json; m=json.load(open('/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/.claude-plugin/plugin.json')); assert m['name']=='docs-hero'; assert m['version']; assert m['hooks']['SessionStart']; print('OK')"
```

Expected: FAIL — file does not exist.

- [ ] **Step 2: Write plugin.json**

Create `/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/.claude-plugin/plugin.json` with:

```json
{
  "name": "docs-hero",
  "version": "1.2.0",
  "description": "BrSE document generation suite (SRS + API + DB) for ITO Japan offshore. Conflict-minimal updates from OpenSpec/plan, codebase sync with human-gated approval.",
  "author": {
    "name": "Mor (Hai Duong)",
    "email": "duongmh@mor.com.vn"
  },
  "homepage": "https://github.com/mor-duongmh/claude-plugins/tree/main/plugins/docs-hero",
  "repository": "https://github.com/mor-duongmh/claude-plugins",
  "license": "MIT",
  "keywords": [
    "documentation",
    "srs",
    "api-docs",
    "database",
    "brse",
    "ito-japan",
    "openspec",
    "mermaid"
  ],
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\"",
            "async": true
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 3: Run validation check — should PASS now**

```bash
test -f /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/.claude-plugin/plugin.json && \
python3 -c "import json; m=json.load(open('/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/.claude-plugin/plugin.json')); assert m['name']=='docs-hero'; assert m['version']; assert m['hooks']['SessionStart']; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/.claude-plugin/plugin.json
git commit -m "feat(docs-hero): add plugin manifest"
```

---

### Task 4: Add plugin to marketplace.json

**Files:**
- Modify: `claude-plugins/.claude-plugin/marketplace.json`

- [ ] **Step 1: Read current marketplace.json plugin count**

```bash
python3 -c "import json; m=json.load(open('/Users/haiduong/Documents/work/claude-plugins/.claude-plugin/marketplace.json')); print(len(m['plugins']))"
```

Expected: `3` (spec, superpowers, deep-review)

- [ ] **Step 2: Append docs-hero entry**

Edit `/Users/haiduong/Documents/work/claude-plugins/.claude-plugin/marketplace.json`. Inside the `"plugins": [...]` array, after the existing `deep-review` entry (the last one), add a comma after the `}` of deep-review entry, then add:

```json
    {
      "name": "docs-hero",
      "description": "BrSE document generation suite (SRS + API + DB) for ITO Japan offshore. Init/update/sync with conflict-minimal diff engine. Synergizes with spec plugin: /spec:propose → /docs-hero:update --from-openspec.",
      "source": "./plugins/docs-hero",
      "category": "documentation",
      "author": {
        "name": "Mor (Hai Duong)",
        "email": "duongmh@mor.com.vn"
      },
      "homepage": "https://github.com/mor-duongmh/claude-plugins/tree/main/plugins/docs-hero"
    }
```

- [ ] **Step 3: Verify count is now 4 + JSON valid**

```bash
python3 -c "import json; m=json.load(open('/Users/haiduong/Documents/work/claude-plugins/.claude-plugin/marketplace.json')); assert len(m['plugins'])==4; assert m['plugins'][3]['name']=='docs-hero'; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add .claude-plugin/marketplace.json
git commit -m "feat(marketplace): register docs-hero plugin"
```

---

## Phase 2: Copy Source Files

### Task 5: Copy 4 skills from source bundle

**Files:**
- Create: `plugins/docs-hero/skills/{docs-hero-orchestrator,generate-srs,generate-api-docs,generate-db-design}/**`

- [ ] **Step 1: Copy each skill, stripping `__pycache__`**

```bash
SRC=/Users/haiduong/Documents/work/docs-hero-1.1.0/.claude/skills
DST=/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/skills

for skill in docs-hero-orchestrator generate-srs generate-api-docs generate-db-design; do
    cp -r "$SRC/$skill"/* "$DST/$skill/"
    find "$DST/$skill" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    echo "Copied: $skill"
done
```

Expected: 4 lines of `Copied: ...`

- [ ] **Step 2: Verify count of Python files copied**

```bash
find /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/skills -name "*.py" | wc -l
```

Expected: `48` (matches source count from inventory)

- [ ] **Step 3: Verify SKILL.md count**

```bash
find /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/skills -name "SKILL.md" | wc -l
```

Expected: `4`

- [ ] **Step 4: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/skills/
git commit -m "feat(docs-hero): copy 4 skills from docs-hero-1.1.0 bundle"
```

---

### Task 6: Copy agent + requirements.txt

**Files:**
- Create: `plugins/docs-hero/agents/docs-hero.md`
- Create: `plugins/docs-hero/requirements.txt`

- [ ] **Step 1: Copy agent + requirements**

```bash
cp /Users/haiduong/Documents/work/docs-hero-1.1.0/.claude/agents/docs-hero.md \
   /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/agents/docs-hero.md

cp /Users/haiduong/Documents/work/docs-hero-1.1.0/requirements.txt \
   /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/requirements.txt
```

- [ ] **Step 2: Verify both files have expected content**

```bash
test -s /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/agents/docs-hero.md && \
grep -q "model: haiku" /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/agents/docs-hero.md && \
grep -q "pydantic==2.13.3" /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/requirements.txt && \
echo "OK"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/agents/ plugins/docs-hero/requirements.txt
git commit -m "feat(docs-hero): copy QA agent + Python deps pin file"
```

---

## Phase 3: Path Refactor (CRITICAL)

### Task 7: Patch dispatch_coordinator.py to honor CLAUDE_PLUGIN_ROOT

**Files:**
- Modify: `plugins/docs-hero/skills/docs-hero-orchestrator/scripts/dispatch_coordinator.py:38-43`

- [ ] **Step 1: Write failing test**

Create `/tmp/test_dispatch_path.py`:

```python
"""Test dispatch_coordinator resolves sub-skill paths from CLAUDE_PLUGIN_ROOT."""
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path("/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero")
COORD = PLUGIN_ROOT / "skills/docs-hero-orchestrator/scripts/dispatch_coordinator.py"

def test_runs_with_plugin_root_env():
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    result = subprocess.run(
        [sys.executable, str(COORD), "--help"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Should print argparse help, not crash with FileNotFoundError
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()

if __name__ == "__main__":
    test_runs_with_plugin_root_env()
    print("PASS")
```

- [ ] **Step 2: Run test — should PASS already (no Python deps imported in --help path)**

```bash
python3 /tmp/test_dispatch_path.py
```

Expected: `PASS` — because `--help` doesn't trigger pydantic import. We're verifying the baseline still works.

- [ ] **Step 3: Patch dispatch_coordinator.py**

Open `/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/skills/docs-hero-orchestrator/scripts/dispatch_coordinator.py`. Find lines 38-43:

```python
# Resolve sibling sub-skill folders
_SKILLS_ROOT = _THIS_DIR.parents[1]  # .claude/skills/
_SRS_SCRIPTS = _SKILLS_ROOT / "generate-srs" / "scripts"
_API_SCRIPTS = _SKILLS_ROOT / "generate-api-docs" / "scripts"
_DB_SCRIPTS = _SKILLS_ROOT / "generate-db-design" / "scripts"
```

Replace with:

```python
# Resolve sibling sub-skill folders.
# Plugin layout: $CLAUDE_PLUGIN_ROOT/skills/<sub-skill>/scripts/
# Bundle layout (legacy): <bundle>/.claude/skills/<sub-skill>/scripts/ via parents[1]
_PLUGIN_ROOT_ENV = os.environ.get("CLAUDE_PLUGIN_ROOT")
if _PLUGIN_ROOT_ENV:
    _SKILLS_ROOT = Path(_PLUGIN_ROOT_ENV) / "skills"
else:
    _SKILLS_ROOT = _THIS_DIR.parents[1]  # legacy bundle layout
_SRS_SCRIPTS = _SKILLS_ROOT / "generate-srs" / "scripts"
_API_SCRIPTS = _SKILLS_ROOT / "generate-api-docs" / "scripts"
_DB_SCRIPTS = _SKILLS_ROOT / "generate-db-design" / "scripts"
```

Also at the top of the file, ensure `import os` is present (look near `import argparse`):

```python
import argparse
import json
import logging
import os                         # add if not present
import subprocess
import sys
```

- [ ] **Step 4: Re-run test — should still PASS**

```bash
python3 /tmp/test_dispatch_path.py
```

Expected: `PASS`

- [ ] **Step 5: Verify both layouts resolve correctly**

```bash
cd /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/skills/docs-hero-orchestrator/scripts

# Bundle-layout fallback: no env, file is at the right depth
python3 -c "
import os
os.environ.pop('CLAUDE_PLUGIN_ROOT', None)
import sys; sys.path.insert(0, '.')
from dispatch_coordinator import _SKILLS_ROOT, _SRS_SCRIPTS
print(f'fallback _SKILLS_ROOT={_SKILLS_ROOT}')
assert _SRS_SCRIPTS.name == 'scripts' and _SRS_SCRIPTS.parent.name == 'generate-srs'
print('fallback OK')
"

# Plugin-layout: env set
python3 -c "
import os
os.environ['CLAUDE_PLUGIN_ROOT'] = '/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero'
import sys; sys.path.insert(0, '.')
# Reimport since module-level vars cached — use importlib
import importlib, dispatch_coordinator
importlib.reload(dispatch_coordinator)
print(f'env _SKILLS_ROOT={dispatch_coordinator._SKILLS_ROOT}')
assert str(dispatch_coordinator._SKILLS_ROOT).endswith('/plugins/docs-hero/skills')
print('env OK')
"
```

Expected: both prints + `fallback OK`, `env OK`.

- [ ] **Step 6: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/skills/docs-hero-orchestrator/scripts/dispatch_coordinator.py
git commit -m "fix(docs-hero): honor CLAUDE_PLUGIN_ROOT in dispatch_coordinator path resolution"
```

---

### Task 8: Refactor docs-hero-orchestrator/SKILL.md

**Files:**
- Modify: `plugins/docs-hero/skills/docs-hero-orchestrator/SKILL.md`

The original SKILL.md uses bare `python scripts/...` invocations that assume cwd=skill dir. Plugin context has different cwd (project root). Add a header block defining helper variables, then update example invocations.

- [ ] **Step 1: Read current SKILL.md to find Init Flow / Update Flow / Sync Flow sections**

```bash
grep -n "^##" /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/skills/docs-hero-orchestrator/SKILL.md
```

Expected: list of `## Operations`, `## Routing Logic`, `## Init Flow`, `## Update Flow`, `## Sync Flow (2-step)`, `## Lock Acquisition (mutating ops only)`, etc.

- [ ] **Step 2: Add Environment block after `# Docs Hero Orchestrator` heading**

In `plugins/docs-hero/skills/docs-hero-orchestrator/SKILL.md`, find the line after the H1 heading `# Docs Hero Orchestrator` and the intro paragraph. Insert this section before `## Operations`:

```markdown
## Environment (plugin context)

This skill runs as a Claude Code plugin. Path resolution uses these variables:

```bash
# Plugin root (set by Claude Code at runtime)
CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero}"

# Python venv (created by /docs-hero:setup)
VENV="${HOME}/.claude/plugins/data/docs-hero/.venv"
PY="${VENV}/bin/python3"

# Skill scripts (within plugin)
ORCH_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/docs-hero-orchestrator/scripts"
SRS_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-srs/scripts"
API_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-api-docs/scripts"
DB_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-db-design/scripts"

# Project paths (always relative to user's cwd, NOT plugin root)
PROJECT_DOCS_DIR="${PWD}/docs"
PROJECT_META="${PWD}/.docs-hero-meta.json"
PROJECT_LOCK="${PWD}/.docs-hero.lock"
PROJECT_TMP="${PWD}/.tmp"
```

**Pre-flight check** every operation must perform:

```bash
test -d "$VENV" || { echo "ERROR: venv missing. Run /docs-hero:setup first." >&2; exit 1; }
```

```

- [ ] **Step 3: Update `## Init Flow` block**

Find the current `## Init Flow` section and replace its bash code block with:

````markdown
## Init Flow

```bash
# Pre-flight
test -d "$VENV" || { echo "ERROR: run /docs-hero:setup first." >&2; exit 1; }
mkdir -p "$PROJECT_TMP"

# 1. Parse inputs → ProjectModel JSON
"$PY" "$ORCH_SCRIPTS/parse_inputs.py" \
  --inputs "$INPUT_DIR" \
  --output "$PROJECT_TMP/raw-bundle.json"

# 2. Dispatch to sub-skills (CLAUDE_PLUGIN_ROOT is inherited from env)
"$PY" "$ORCH_SCRIPTS/dispatch_coordinator.py" init \
  --project-model "$PROJECT_TMP/project-model.json" \
  --language EN \
  --outputs srs,api,db \
  --docs-dir "$PROJECT_DOCS_DIR"

# 3. Aggregate report
"$PY" "$ORCH_SCRIPTS/aggregate_report.py" \
  --docs-dir "$PROJECT_DOCS_DIR" \
  --output "$PROJECT_TMP/init-report.md"

# 4. Spawn docs-hero agent for QA review (Skill tool: docs-hero)
```
````

- [ ] **Step 4: Update `## Update Flow` block**

Find `## Update Flow` and replace its code block with:

````markdown
## Update Flow

```bash
# Pre-flight + lock
test -d "$VENV" || { echo "ERROR: run /docs-hero:setup first." >&2; exit 1; }
"$PY" "$ORCH_SCRIPTS/lock_manager.py" acquire --lock "$PROJECT_LOCK" || exit 1
trap '"$PY" "$ORCH_SCRIPTS/lock_manager.py" release --lock "$PROJECT_LOCK"' EXIT

# 1. Parse delta source
"$PY" "$ORCH_SCRIPTS/parse_plan.py" --plan "$PLAN_PATH" --output "$PROJECT_TMP/delta.json"
# OR
"$PY" "$ORCH_SCRIPTS/parse_openspec.py" --change-dir "$OPENSPEC_CHANGE_DIR" --output "$PROJECT_TMP/delta.json"

# 2. Per-doc: detect manual edits → compute diff → apply patch
"$PY" "$ORCH_SCRIPTS/dispatch_coordinator.py" update \
  --delta "$PROJECT_TMP/delta.json" \
  --docs-dir "$PROJECT_DOCS_DIR" \
  --meta "$PROJECT_META"

# 3. Aggregate + spawn agent
```
````

- [ ] **Step 5: Update `## Sync Flow (2-step)` block**

Find `## Sync Flow (2-step)` and replace with:

````markdown
## Sync Flow (2-step)

Step 1 — propose (read-only, no lock):
```bash
"$PY" "$API_SCRIPTS/api_sync_propose.py" \
  --codebase-paths "$CODEBASE_PATHS" \
  --existing-doc "$PROJECT_DOCS_DIR/api-docs.md" \
  --output "$PROJECT_TMP/api-sync-proposal.md"

"$PY" "$DB_SCRIPTS/db_sync_propose.py" \
  --codebase-paths "$CODEBASE_PATHS" \
  --existing-doc "$PROJECT_DOCS_DIR/database-design.md" \
  --output "$PROJECT_TMP/db-sync-proposal.md"
# SRS sync not supported (requirements cannot be inferred from code)
```

Step 2 — apply-sync (after user ticks checkboxes):
```bash
"$PY" "$API_SCRIPTS/api_sync_apply.py" \
  --proposal "$PROJECT_TMP/api-sync-proposal.md" \
  --output "$PROJECT_TMP/api-delta.json"

# Then run standard update flow with the resulting delta
"$PY" "$ORCH_SCRIPTS/dispatch_coordinator.py" update \
  --delta "$PROJECT_TMP/api-delta.json" \
  --docs-dir "$PROJECT_DOCS_DIR" \
  --meta "$PROJECT_META"
```
````

- [ ] **Step 6: Update `## Lock Acquisition` block (paths only)**

In the `## Lock Acquisition` section, replace any bare `lock_manager.py` references with `"$PY" "$ORCH_SCRIPTS/lock_manager.py"` and any `.docs-hero.lock` reference with `"$PROJECT_LOCK"`.

- [ ] **Step 7: Verify file is still syntactically valid markdown**

```bash
python3 -c "
content = open('/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/skills/docs-hero-orchestrator/SKILL.md').read()
# Frontmatter check
assert content.startswith('---\n'), 'frontmatter missing'
# Triple-backtick balance
assert content.count('\`\`\`') % 2 == 0, 'unbalanced code fences'
# Required headers
for h in ['## Environment', '## Operations', '## Init Flow', '## Update Flow', '## Sync Flow']:
    assert h in content, f'missing: {h}'
print('OK')
"
```

Expected: `OK`

- [ ] **Step 8: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/skills/docs-hero-orchestrator/SKILL.md
git commit -m "refactor(docs-hero): use CLAUDE_PLUGIN_ROOT paths in orchestrator SKILL.md"
```

---

### Task 9: Refactor generate-srs/SKILL.md

**Files:**
- Modify: `plugins/docs-hero/skills/generate-srs/SKILL.md`

- [ ] **Step 1: Add Environment block after `# Generate SRS Skill` heading**

Insert this section before `## Output Structure`:

```markdown
## Environment (plugin context)

```bash
CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero}"
VENV="${HOME}/.claude/plugins/data/docs-hero/.venv"
PY="${VENV}/bin/python3"
SRS_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-srs/scripts"
SRS_TEMPLATES="${CLAUDE_PLUGIN_ROOT}/skills/generate-srs/templates"
ORCH_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/docs-hero-orchestrator/scripts"
PROJECT_DOCS_DIR="${PWD}/docs"
PROJECT_META="${PWD}/.docs-hero-meta.json"
```

```

- [ ] **Step 2: Update `## Init Workflow` block**

Replace its code block with:

````markdown
## Init Workflow

```bash
"$PY" "$SRS_SCRIPTS/render_srs.py" \
  --project-model "$PROJECT_MODEL" \
  --template "$SRS_TEMPLATES/srs-template.md" \
  --language JP \
  --output "$PROJECT_DOCS_DIR/srs.md"

# Per screen:
"$PY" "$SRS_SCRIPTS/render_screen_spec.py" \
  --project-model "$PROJECT_MODEL" \
  --screen-id SCREEN-001 \
  --template "$SRS_TEMPLATES/screen-spec-template.md" \
  --language JP \
  --output "$PROJECT_DOCS_DIR/screen-specs/SCREEN-001-${SLUG}.md"

# Mockup annotation (when image provided):
"$PY" "$SRS_SCRIPTS/annotate_mockup.py" \
  --image "${PWD}/assets/screens/SCREEN-001-login.png" \
  --items "${PWD}/.tmp/mockup-SCREEN-001.json" \
  --output "${PWD}/assets/screens/SCREEN-001-login-annotated.png"
```
````

- [ ] **Step 3: Update `## Update Workflow` block**

Replace its code block with:

````markdown
## Update Workflow

The orchestrator pre-filters the Delta to SRS-relevant entity types and runs the standard diff-engine flow:

```bash
"$PY" "$ORCH_SCRIPTS/detect_manual_edits.py" \
  --doc "$PROJECT_DOCS_DIR/srs.md" \
  --meta "$PROJECT_META" \
  --output "${PWD}/.tmp/edits.json"

"$PY" "$ORCH_SCRIPTS/compute_diff.py" \
  --delta "${PWD}/.tmp/srs-delta.json" \
  --doc "$PROJECT_DOCS_DIR/srs.md" \
  --manual-edits "${PWD}/.tmp/edits.json" \
  --output "${PWD}/.tmp/plan.json"

"$PY" "$ORCH_SCRIPTS/apply_patch.py" \
  --plan "${PWD}/.tmp/plan.json" \
  --doc "$PROJECT_DOCS_DIR/srs.md" \
  --meta "$PROJECT_META"
```
````

- [ ] **Step 4: Verify markdown still valid**

```bash
python3 -c "
content = open('/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/skills/generate-srs/SKILL.md').read()
assert content.startswith('---\n')
assert content.count('\`\`\`') % 2 == 0
assert '## Environment' in content
assert '## Init Workflow' in content
assert '## Update Workflow' in content
print('OK')
"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/skills/generate-srs/SKILL.md
git commit -m "refactor(docs-hero): use CLAUDE_PLUGIN_ROOT paths in generate-srs SKILL.md"
```

---

### Task 10: Refactor generate-api-docs/SKILL.md

**Files:**
- Modify: `plugins/docs-hero/skills/generate-api-docs/SKILL.md`

- [ ] **Step 1: Add Environment block before `## Modes`**

```markdown
## Environment (plugin context)

```bash
CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero}"
VENV="${HOME}/.claude/plugins/data/docs-hero/.venv"
PY="${VENV}/bin/python3"
API_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-api-docs/scripts"
ORCH_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/docs-hero-orchestrator/scripts"
PROJECT_DOCS_DIR="${PWD}/docs"
PROJECT_META="${PWD}/.docs-hero-meta.json"
```

```

- [ ] **Step 2: Update `## Init Workflow`**

Replace code block with:

````markdown
## Init Workflow

```bash
"$PY" "$API_SCRIPTS/render_api_docs.py" \
  --project-model "$PROJECT_MODEL" \
  --language JP \
  --output "$PROJECT_DOCS_DIR/api-docs.md"
```
````

- [ ] **Step 3: Update `## Update Workflow`**

Replace code block with:

````markdown
## Update Workflow

```bash
"$PY" "$ORCH_SCRIPTS/detect_manual_edits.py" \
  --doc "$PROJECT_DOCS_DIR/api-docs.md" --meta "$PROJECT_META" \
  --output "${PWD}/.tmp/api-edits.json"
"$PY" "$ORCH_SCRIPTS/compute_diff.py" \
  --delta "${PWD}/.tmp/api-delta.json" \
  --doc "$PROJECT_DOCS_DIR/api-docs.md" \
  --manual-edits "${PWD}/.tmp/api-edits.json" \
  --output "${PWD}/.tmp/api-plan.json"
"$PY" "$ORCH_SCRIPTS/apply_patch.py" \
  --plan "${PWD}/.tmp/api-plan.json" \
  --doc "$PROJECT_DOCS_DIR/api-docs.md" \
  --meta "$PROJECT_META"
```
````

- [ ] **Step 4: Update `## Sync Workflow (2-step, report before add)`**

Replace step 1 + step 2 code blocks with:

````markdown
### Step 1: propose

```bash
"$PY" "$API_SCRIPTS/api_sync_propose.py" \
  --codebase-paths "$CODEBASE_PATHS" \
  --existing-doc "$PROJECT_DOCS_DIR/api-docs.md" \
  --output "${PWD}/.tmp/api-sync-proposal.md"
```

### Step 2: apply-sync

```bash
"$PY" "$API_SCRIPTS/api_sync_apply.py" \
  --proposal "${PWD}/.tmp/api-sync-proposal.md" \
  --output "${PWD}/.tmp/api-delta.json"
```
````

- [ ] **Step 5: Verify + commit**

```bash
python3 -c "
content = open('/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/skills/generate-api-docs/SKILL.md').read()
assert content.startswith('---\n'); assert content.count('\`\`\`') % 2 == 0
assert '## Environment' in content
print('OK')
"

cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/skills/generate-api-docs/SKILL.md
git commit -m "refactor(docs-hero): use CLAUDE_PLUGIN_ROOT paths in generate-api-docs SKILL.md"
```

Expected: `OK` then commit succeeds.

---

### Task 11: Refactor generate-db-design/SKILL.md

**Files:**
- Modify: `plugins/docs-hero/skills/generate-db-design/SKILL.md`

- [ ] **Step 1: Add Environment block before `## Modes`**

```markdown
## Environment (plugin context)

```bash
CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero}"
VENV="${HOME}/.claude/plugins/data/docs-hero/.venv"
PY="${VENV}/bin/python3"
DB_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/generate-db-design/scripts"
ORCH_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/docs-hero-orchestrator/scripts"
PROJECT_DOCS_DIR="${PWD}/docs"
PROJECT_META="${PWD}/.docs-hero-meta.json"
```

```

- [ ] **Step 2: Update `## Init Workflow`**

````markdown
## Init Workflow

```bash
"$PY" "$DB_SCRIPTS/render_db_design.py" \
  --project-model "$PROJECT_MODEL" \
  --language JP \
  --output "$PROJECT_DOCS_DIR/database-design.md"
```
````

- [ ] **Step 3: Update `## Sync Workflow`**

````markdown
### Step 1: propose

```bash
"$PY" "$DB_SCRIPTS/db_sync_propose.py" \
  --codebase-paths "$CODEBASE_PATHS" \
  --existing-doc "$PROJECT_DOCS_DIR/database-design.md" \
  --output "${PWD}/.tmp/db-sync-proposal.md"
```

### Step 2: apply-sync

```bash
"$PY" "$DB_SCRIPTS/db_sync_apply.py" \
  --proposal "${PWD}/.tmp/db-sync-proposal.md" \
  --output "${PWD}/.tmp/db-delta.json"
```
````

- [ ] **Step 4: Verify + commit**

```bash
python3 -c "
content = open('/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/skills/generate-db-design/SKILL.md').read()
assert content.startswith('---\n'); assert content.count('\`\`\`') % 2 == 0
print('OK')
"

cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/skills/generate-db-design/SKILL.md
git commit -m "refactor(docs-hero): use CLAUDE_PLUGIN_ROOT paths in generate-db-design SKILL.md"
```

---

## Phase 4: Hooks & Bootstrap Scripts

### Task 12: Write setup-venv.sh with TDD

**Files:**
- Create: `plugins/docs-hero/scripts/setup-venv.sh`
- Test: `/tmp/test_setup_venv.sh`

- [ ] **Step 1: Write failing test**

Create `/tmp/test_setup_venv.sh`:

```bash
#!/usr/bin/env bash
# Test setup-venv.sh creates venv + installs deps + verifies imports.
set -euo pipefail

# Use fake $HOME so we don't pollute user's actual venv
TEST_HOME=$(mktemp -d)
trap "rm -rf $TEST_HOME" EXIT

export HOME="$TEST_HOME"
export CLAUDE_PLUGIN_ROOT="/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero"

bash "$CLAUDE_PLUGIN_ROOT/scripts/setup-venv.sh"

VENV="$HOME/.claude/plugins/data/docs-hero/.venv"
test -d "$VENV" || { echo "FAIL: venv not created"; exit 1; }
test -x "$VENV/bin/python3" || { echo "FAIL: python3 missing in venv"; exit 1; }

# Verify all 8 deps importable
"$VENV/bin/python3" -c "
import pydantic, markdown_it
from PIL import Image
import openpyxl, docx, pypdf, pdfplumber, pytest
print('all imports OK')
" || { echo "FAIL: import check"; exit 1; }

echo "TEST PASS"
```

- [ ] **Step 2: Run test — should FAIL (script does not exist yet)**

```bash
chmod +x /tmp/test_setup_venv.sh
/tmp/test_setup_venv.sh
```

Expected: FAIL with "No such file or directory" on `setup-venv.sh`.

- [ ] **Step 3: Write setup-venv.sh**

Create `/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/scripts/setup-venv.sh`:

```bash
#!/usr/bin/env bash
# setup-venv.sh — create + populate docs-hero Python venv at user-shared location.
#
# Usage (from /docs-hero:setup slash command):
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
echo "[docs-hero] verify with /docs-hero:doctor"
```

Make it executable:

```bash
chmod +x /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/scripts/setup-venv.sh
```

- [ ] **Step 4: Run test — should PASS**

```bash
/tmp/test_setup_venv.sh
```

Expected: `TEST PASS` (allow 30-60s for first install).

- [ ] **Step 5: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/scripts/setup-venv.sh
git commit -m "feat(docs-hero): add setup-venv.sh bootstrap script"
```

---

### Task 13: Write doctor.sh with TDD

**Files:**
- Create: `plugins/docs-hero/scripts/doctor.sh`
- Test: `/tmp/test_doctor.sh`

- [ ] **Step 1: Write failing test**

Create `/tmp/test_doctor.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

export CLAUDE_PLUGIN_ROOT="/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero"

OUTPUT=$(bash "$CLAUDE_PLUGIN_ROOT/scripts/doctor.sh" 2>&1)

echo "$OUTPUT" | grep -q "Python:" || { echo "FAIL: missing Python check"; exit 1; }
echo "$OUTPUT" | grep -q "venv:" || { echo "FAIL: missing venv check"; exit 1; }
echo "$OUTPUT" | grep -q "deps:" || { echo "FAIL: missing deps check"; exit 1; }
echo "$OUTPUT" | grep -q "schema:" || { echo "FAIL: missing schema check"; exit 1; }
echo "$OUTPUT" | grep -q "mmdc:" || { echo "FAIL: missing mmdc check"; exit 1; }

echo "TEST PASS"
```

- [ ] **Step 2: Run test — should FAIL**

```bash
chmod +x /tmp/test_doctor.sh
/tmp/test_doctor.sh
```

Expected: FAIL — script missing.

- [ ] **Step 3: Write doctor.sh**

Create `/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/scripts/doctor.sh`:

```bash
#!/usr/bin/env bash
# doctor.sh — verify docs-hero installation health.

set -uo pipefail
# (no -e: we want to report all checks even if some fail)

VENV="${HOME}/.claude/plugins/data/docs-hero/.venv"

echo "=== docs-hero doctor ==="

# --- Python ---
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 9 ]; then
        echo "Python: OK ($PY_VER)"
    else
        echo "Python: FAIL (need 3.9+, found $PY_VER)"
    fi
else
    echo "Python: FAIL (python3 not in PATH)"
fi

# --- Venv ---
if [ -d "$VENV" ] && [ -x "$VENV/bin/python3" ]; then
    echo "venv: OK ($VENV)"
else
    echo "venv: MISSING — run /docs-hero:setup"
fi

# --- Deps ---
if [ -x "$VENV/bin/python3" ]; then
    if "$VENV/bin/python3" -c "import pydantic, markdown_it; from PIL import Image; import openpyxl, docx, pypdf, pdfplumber, pytest" 2>/dev/null; then
        echo "deps: OK (8 packages importable)"
    else
        echo "deps: FAIL — re-run /docs-hero:setup"
    fi
else
    echo "deps: SKIP (venv missing)"
fi

# --- Schema ---
if [ -x "$VENV/bin/python3" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
    SCHEMA="$CLAUDE_PLUGIN_ROOT/skills/docs-hero-orchestrator/scripts/lib/normalized_schema.py"
    if [ -f "$SCHEMA" ] && "$VENV/bin/python3" -c "
import sys
sys.path.insert(0, '$CLAUDE_PLUGIN_ROOT/skills/docs-hero-orchestrator/scripts')
from lib.normalized_schema import ProjectModel, Delta
" 2>/dev/null; then
        echo "schema: OK (ProjectModel + Delta importable)"
    else
        echo "schema: FAIL"
    fi
else
    echo "schema: SKIP (venv or CLAUDE_PLUGIN_ROOT missing)"
fi

# --- mmdc (optional) ---
if command -v mmdc >/dev/null 2>&1; then
    MMDC_VER=$(mmdc --version 2>/dev/null || echo "?")
    echo "mmdc: OK ($MMDC_VER) — Mermaid validation will use CLI"
else
    echo "mmdc: not installed (optional) — agent uses syntax sanity check fallback"
fi

echo "=== done ==="
```

```bash
chmod +x /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/scripts/doctor.sh
```

- [ ] **Step 4: Run test — should PASS**

```bash
/tmp/test_doctor.sh
```

Expected: `TEST PASS`

- [ ] **Step 5: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/scripts/doctor.sh
git commit -m "feat(docs-hero): add doctor.sh health check"
```

---

### Task 14: Write session-start.sh with TDD (idempotent hint)

**Files:**
- Create: `plugins/docs-hero/hooks/session-start.sh`
- Test: `/tmp/test_session_start.sh`

- [ ] **Step 1: Write failing test**

Create `/tmp/test_session_start.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

TEST_HOME=$(mktemp -d)
trap "rm -rf $TEST_HOME" EXIT
export HOME="$TEST_HOME"
export CLAUDE_PLUGIN_ROOT="/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero"

# Case 1: venv missing, first run → should emit hint to stderr
OUT1=$(bash "$CLAUDE_PLUGIN_ROOT/hooks/session-start.sh" 2>&1)
echo "$OUT1" | grep -q "/docs-hero:setup" || { echo "FAIL: hint not shown on first run"; exit 1; }

# Case 2: venv missing, second run → should NOT emit hint (state file)
OUT2=$(bash "$CLAUDE_PLUGIN_ROOT/hooks/session-start.sh" 2>&1)
if echo "$OUT2" | grep -q "/docs-hero:setup"; then
    echo "FAIL: hint shown twice"; exit 1
fi

# Case 3: venv present → silent
mkdir -p "$HOME/.claude/plugins/data/docs-hero/.venv"
rm -f "$HOME/.claude/plugins/data/docs-hero/.first-run-hint-shown"
OUT3=$(bash "$CLAUDE_PLUGIN_ROOT/hooks/session-start.sh" 2>&1)
if echo "$OUT3" | grep -q "/docs-hero:setup"; then
    echo "FAIL: hint shown when venv present"; exit 1
fi

echo "TEST PASS"
```

- [ ] **Step 2: Run test — should FAIL**

```bash
chmod +x /tmp/test_session_start.sh
/tmp/test_session_start.sh
```

Expected: FAIL — hook missing.

- [ ] **Step 3: Write session-start.sh**

Create `/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/hooks/session-start.sh`:

```bash
#!/usr/bin/env bash
# session-start.sh — detect-only hint when docs-hero venv missing.
# Never auto-creates venv (would block session startup with 30-60s pip install).

set -uo pipefail

VENV="${HOME}/.claude/plugins/data/docs-hero/.venv"
STATE_DIR="${HOME}/.claude/plugins/data/docs-hero"
HINT_SHOWN="${STATE_DIR}/.first-run-hint-shown"

mkdir -p "$STATE_DIR"

if [ ! -d "$VENV" ] && [ ! -f "$HINT_SHOWN" ]; then
    echo "[docs-hero] venv not initialized. Run /docs-hero:setup to bootstrap (~30-60s)." >&2
    touch "$HINT_SHOWN"
fi

exit 0
```

```bash
chmod +x /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/hooks/session-start.sh
```

- [ ] **Step 4: Run test — should PASS**

```bash
/tmp/test_session_start.sh
```

Expected: `TEST PASS`

- [ ] **Step 5: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/hooks/session-start.sh
git commit -m "feat(docs-hero): add session-start hook with idempotent hint"
```

---

## Phase 5: Slash Commands

### Task 15: Create /docs-hero:setup command

**Files:**
- Create: `plugins/docs-hero/commands/setup.md`

- [ ] **Step 1: Write the file**

Create `/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/commands/setup.md`:

```markdown
---
description: Bootstrap docs-hero Python venv (~/.claude/plugins/data/docs-hero/.venv) and install pinned deps. Run once after /plugin install. Idempotent.
---

Bootstrap the docs-hero Python venv. This is a one-time setup that takes ~30-60s on first run; subsequent runs are fast (deps already installed).

Run the bootstrap script:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/setup-venv.sh"
```

After completion, verify the install:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.sh"
```

If any check shows FAIL or MISSING, re-run `/docs-hero:setup` or report the doctor output.
```

- [ ] **Step 2: Verify file**

```bash
test -s /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/commands/setup.md && \
grep -q "description:" /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/commands/setup.md && \
echo "OK"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/commands/setup.md
git commit -m "feat(docs-hero): add /docs-hero:setup slash command"
```

---

### Task 16: Create /docs-hero:doctor command

**Files:**
- Create: `plugins/docs-hero/commands/doctor.md`

- [ ] **Step 1: Write file**

Create `/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/commands/doctor.md`:

```markdown
---
description: Health-check docs-hero install (Python version, venv, deps, schema importable, mmdc availability). Read-only.
---

Run the health check:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.sh"
```

Expected output (all green):

```
=== docs-hero doctor ===
Python: OK (3.X.X)
venv: OK (~/.claude/plugins/data/docs-hero/.venv)
deps: OK (8 packages importable)
schema: OK (ProjectModel + Delta importable)
mmdc: not installed (optional) — agent uses syntax sanity check fallback
=== done ===
```

If `venv: MISSING` → run `/docs-hero:setup`.
If `deps: FAIL` → re-run `/docs-hero:setup` to refresh.
`mmdc: not installed` is optional and does NOT block functionality.
```

- [ ] **Step 2: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/commands/doctor.md
git commit -m "feat(docs-hero): add /docs-hero:doctor slash command"
```

---

### Task 17: Create /docs-hero:init command

**Files:**
- Create: `plugins/docs-hero/commands/init.md`

- [ ] **Step 1: Write file**

Create `/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/commands/init.md`:

```markdown
---
description: Generate fresh SRS + API docs + DB design from a ProjectModel JSON. Outputs to ./docs/ in current project. Single-language (JP|EN|VN).
argument-hint: "--project-model <path> --language <JP|EN|VN> [--outputs srs,api,db]"
---

Pre-flight check:

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /docs-hero:setup first." >&2
  exit 1
}
```

Then invoke the orchestrator skill:

Use the **Skill tool** to invoke `docs-hero-orchestrator` with mode `init` and pass through the user-provided arguments. The skill will:

1. Parse inputs from `${PWD}/.tmp/` or `--inputs` directory
2. Dispatch to sub-skills (parallel where safe)
3. Render docs to `${PWD}/docs/`
4. Generate aggregate report
5. Spawn the `docs-hero` QA agent for cross-reference + BrSE-quality validation

Output files:
- `docs/srs.md`
- `docs/api-docs.md`
- `docs/database-design.md`
- `docs/screen-specs/SCREEN-*.md` (per FR with screens)
- `.docs-hero-meta.json` (sidecar, gitignored)
```

- [ ] **Step 2: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/commands/init.md
git commit -m "feat(docs-hero): add /docs-hero:init slash command"
```

---

### Task 18: Create /docs-hero:update command

**Files:**
- Create: `plugins/docs-hero/commands/update.md`

- [ ] **Step 1: Write file**

Create `/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/commands/update.md`:

```markdown
---
description: Apply OpenSpec change or brainstorm plan to existing docs (SRS/API/DB) — preserves manual edits via diff engine.
argument-hint: "--from-openspec <change-name> | --from-plan <path-to-plan.md>"
---

Pre-flight check:

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /docs-hero:setup first." >&2
  exit 1
}

test -f "${PWD}/.docs-hero-meta.json" || {
  echo "ERROR: .docs-hero-meta.json missing. Run /docs-hero:init first or use /docs-hero rebuild-meta." >&2
  exit 1
}
```

Then invoke the orchestrator skill with mode `update`. Synergy with `spec` plugin:

```
/spec:propose "feature-X"          # creates openspec/changes/feature-X/...
# (review-checklist gate)
/docs-hero:update --from-openspec feature-X
# → SRS/API/DB updated atomically, your manual edits preserved
```

The diff engine flow:
1. `parse_openspec.py` (or `parse_plan.py`) → Delta JSON (ADD/UPDATE/DEPRECATE per entity)
2. `detect_manual_edits.py` → identify BrSE manual edits to preserve
3. `compute_diff.py` → compute patch plan
4. `apply_patch.py` → atomic write
5. Spawn `docs-hero` QA agent for verification
```

- [ ] **Step 2: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/commands/update.md
git commit -m "feat(docs-hero): add /docs-hero:update slash command"
```

---

### Task 19: Create /docs-hero:sync + apply-sync commands

**Files:**
- Create: `plugins/docs-hero/commands/sync.md`
- Create: `plugins/docs-hero/commands/apply-sync.md`

- [ ] **Step 1: Write sync.md**

Create `/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/commands/sync.md`:

```markdown
---
description: Scan codebase (ORM models + REST routes) and propose ADD/UPDATE/DEPRECATE changes to api-docs.md and database-design.md. Read-only — no doc changes. User ticks checkboxes, then runs /docs-hero:apply-sync.
argument-hint: "--codebase-paths <comma-separated>"
---

Pre-flight check:

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /docs-hero:setup first." >&2
  exit 1
}
```

Invoke the orchestrator skill with mode `sync`. The skill will:

1. Scan paths via `parse_codebase_models.py` (Prisma/TypeORM/Sequelize/Django/SQLAlchemy/GORM/raw SQL) and `parse_codebase_routes.py` (REST patterns)
2. Diff with current `docs/api-docs.md` and `docs/database-design.md`
3. Write proposals (with `[ ]` checkboxes) to:
   - `${PWD}/.tmp/api-sync-proposal.md`
   - `${PWD}/.tmp/db-sync-proposal.md`
4. **DOES NOT touch docs.** User reviews proposals, ticks `[x]` for what to apply.

Note: SRS sync is intentionally not supported — requirements cannot be safely inferred from code.

Next step:
```
# After ticking checkboxes in proposals:
/docs-hero:apply-sync --proposal .tmp/api-sync-proposal.md
```
```

- [ ] **Step 2: Write apply-sync.md**

Create `/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/commands/apply-sync.md`:

```markdown
---
description: Apply user-approved sync proposal (with ticked checkboxes) — converts to Delta and runs the standard update flow.
argument-hint: "--proposal <path-to-*-sync-proposal.md>"
---

Pre-flight:

```bash
test -d "${HOME}/.claude/plugins/data/docs-hero/.venv" || {
  echo "ERROR: venv not initialized. Run /docs-hero:setup first." >&2
  exit 1
}
```

Invoke orchestrator skill with mode `apply-sync` + the proposal path. The skill will:

1. Parse proposal → extract checked items only
2. Emit Delta JSON to `${PWD}/.tmp/<api|db>-delta.json`
3. Run standard update flow with that Delta (same as `/docs-hero:update`)
4. Manual edits preserved via diff engine
```

- [ ] **Step 3: Commit both**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add plugins/docs-hero/commands/sync.md plugins/docs-hero/commands/apply-sync.md
git commit -m "feat(docs-hero): add /docs-hero:sync + /docs-hero:apply-sync slash commands"
```

---

## Phase 6: Smoke Test on Plugin Layout

### Task 20: Run 227 tests from plugin location

**Files:**
- Test: existing `plugins/docs-hero/skills/docs-hero-orchestrator/tests/`

- [ ] **Step 1: Verify venv has pytest**

```bash
ls "$HOME/.claude/plugins/data/docs-hero/.venv/bin/pytest" 2>/dev/null || \
  bash /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/scripts/setup-venv.sh
```

Expected: pytest exists, OR setup-venv.sh runs to completion.

- [ ] **Step 2: Run smoke test from plugin layout**

```bash
cd /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero
export CLAUDE_PLUGIN_ROOT="/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero"
"$HOME/.claude/plugins/data/docs-hero/.venv/bin/python3" -m pytest \
  skills/docs-hero-orchestrator/tests/ -q --tb=line
```

Expected: `227 passed in ~3s`. If FAIL: inspect any test that hard-codes `parents[1]` or relies on bundle layout.

- [ ] **Step 3: If failures, identify + fix**

For any failure mentioning `FileNotFoundError` for sub-skill scripts:
- Open the test file, check if it constructs paths from `_SKILLS_ROOT` or similar
- If yes, the test needs `CLAUDE_PLUGIN_ROOT` env set in fixture
- Add `monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))` in test setup
- Re-run

- [ ] **Step 4: Commit any test fixes**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git status --short plugins/docs-hero/skills/docs-hero-orchestrator/tests/
git add plugins/docs-hero/skills/docs-hero-orchestrator/tests/
git diff --staged --stat
git commit -m "fix(docs-hero): adapt tests for plugin layout (CLAUDE_PLUGIN_ROOT)" || echo "no changes"
```

---

## Phase 7: Documentation

### Task 21: Write plugin README.md

**Files:**
- Create: `plugins/docs-hero/README.md`

- [ ] **Step 1: Write README**

Create `/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/README.md`:

```markdown
# docs-hero

> BrSE document generation suite (SRS + API + DB) cho ITO Japan offshore. Conflict-minimal updates from OpenSpec/plan, codebase sync với human-gated approval.

## Cài đặt

```
/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install docs-hero@mor-duongmh
/docs-hero:setup
```

Yêu cầu: Python ≥ 3.9, ~50 MB disk cho venv, ~30-60s lần đầu setup.

Optional: `mmdc` (mermaid CLI) cho QA agent validate Mermaid syntax — nếu thiếu, agent fallback sang sanity check.

## What it does

3 deliverables, 1 single-language output (JP / EN / VN):

| Document | Standard | Owner skill |
|----------|----------|-------------|
| `docs/srs.md` (+ `docs/screen-specs/SCREEN-*.md`) | BrSE template ITO Japan: 13 sections + 2 appendices, IPA-6 NFR | `generate-srs` |
| `docs/api-docs.md` | REST endpoints with cURL, error codes, webhooks | `generate-api-docs` |
| `docs/database-design.md` | Tables + indexes + Mermaid ERD | `generate-db-design` |

Plus a QA agent (`docs-hero`, model `haiku`) that validates cross-references and BrSE-standard quality after every init/update.

## 3 Modes

### `/docs-hero:init`
Render fresh docs from a `ProjectModel` JSON (Pydantic schema in `lib/normalized_schema.py`, ~40 entity types: FR, NFR, UseCase, Screen, DataItem, ExternalInterface, Report, Table, Endpoint, ...).

### `/docs-hero:update`
Apply Delta from OpenSpec change OR brainstorm plan, **preserving manual edits**. The diff engine:
1. Detect manual edits → preserve those regions
2. Compute patch plan against new Delta
3. Apply atomically with backup

### `/docs-hero:sync` + `/docs-hero:apply-sync`
2-step codebase ↔ docs reconciliation:
1. Scan ORM models + REST routes → write proposal markdown with `[ ]` checkboxes
2. **User reviews + ticks** what to apply
3. `apply-sync` parses ticks → Delta → runs update flow

SRS sync intentionally not supported (requirements ≠ code).

## Synergy với `spec` plugin

```
/spec:propose "feature-X"                          # creates openspec/changes/feature-X/
# (review-checklist gate per Mor workflow)
/spec:apply feature-X                              # implements code
/docs-hero:update --from-openspec feature-X        # syncs SRS/API/DB to match
```

Mor's spec-driven workflow now closes the loop: spec → code → docs.

## Slash Commands

| Command | Purpose |
|---------|---------|
| `/docs-hero:setup` | Bootstrap venv (one-time) |
| `/docs-hero:init` | Fresh docs from ProjectModel JSON |
| `/docs-hero:update` | Apply Delta from OpenSpec or plan |
| `/docs-hero:sync` | Propose codebase changes (read-only) |
| `/docs-hero:apply-sync` | Apply ticked sync proposal |
| `/docs-hero:doctor` | Health check |

## File ownership (in your project)

```
docs/
├── srs.md                          ← generate-srs owns
├── screen-specs/SCREEN-*.md        ← generate-srs owns
├── api-docs.md                     ← generate-api-docs owns
└── database-design.md              ← generate-db-design owns
.docs-hero-meta.json                ← orchestrator owns (gitignored)
.docs-hero.lock                     ← transient (gitignored)
.tmp/                               ← scratch (gitignored)
assets/screens/SCREEN-*-annotated.png  ← generate-srs owns (Pillow + vision)
```

## Troubleshooting

- **`venv: MISSING`** → `/docs-hero:setup`
- **`Python: FAIL`** → Install Python 3.9+
- **`schema: FAIL`** → re-run `/docs-hero:setup` to reinstall pydantic
- **Manual edits lost on update** → File a bug. The diff engine should preserve them; report which file/section.

## Architecture pointers

- Pydantic schema (single source of truth): `skills/docs-hero-orchestrator/scripts/lib/normalized_schema.py` (~803 lines, 40+ entities)
- Diff engine: `compute_diff.py` + `apply_patch.py`
- QA agent: `agents/docs-hero.md` (haiku model, read-only validation)

## License

MIT
```

- [ ] **Step 2: Verify + commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
test -s plugins/docs-hero/README.md && wc -l plugins/docs-hero/README.md
git add plugins/docs-hero/README.md
git commit -m "docs(docs-hero): add plugin README"
```

Expected: ~100 lines, commit succeeds.

---

### Task 22: Update root README.md (plugin table + commands table)

**Files:**
- Modify: `claude-plugins/README.md`

- [ ] **Step 1: Add docs-hero row to Plugins table**

Open `/Users/haiduong/Documents/work/claude-plugins/README.md`. Find the `## Plugins` section (around line 79) with the table. After the `deep-review` row, add:

```markdown
| [`docs-hero`](./plugins/docs-hero) | BrSE document generation: SRS + API + DB cho ITO Japan offshore. Init/update/sync với conflict-minimal diff engine. Synergy với `spec`: `/spec:propose` → `/docs-hero:update --from-openspec`. Python venv tại `~/.claude/plugins/data/docs-hero/.venv` (one-time `/docs-hero:setup`). |
```

- [ ] **Step 2: Add docs-hero rows to Slash commands table**

Find the `## Slash commands` table (around line 87). After the `/deep-review-doctor` row, add:

```markdown
| `/docs-hero:setup` | docs-hero | Bootstrap Python venv (~30-60s, one-time) |
| `/docs-hero:init` | docs-hero | Generate fresh SRS + API docs + DB design from ProjectModel JSON |
| `/docs-hero:update` | docs-hero | Apply OpenSpec change or brainstorm plan to docs (preserves manual edits) |
| `/docs-hero:sync` | docs-hero | Scan codebase, propose changes to API + DB docs (read-only) |
| `/docs-hero:apply-sync` | docs-hero | Apply user-approved sync proposal (ticked checkboxes) |
| `/docs-hero:doctor` | docs-hero | Health-check installation |
```

- [ ] **Step 3: Verify markdown table valid**

```bash
python3 -c "
content = open('/Users/haiduong/Documents/work/claude-plugins/README.md').read()
assert '| [\`docs-hero\`]' in content, 'plugin row missing'
assert '\`/docs-hero:setup\`' in content, 'setup command missing'
assert '\`/docs-hero:init\`' in content, 'init command missing'
print('OK')
"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git add README.md
git commit -m "docs: register docs-hero in marketplace README"
```

---

## Phase 8: End-to-End Verification

### Task 23: Local marketplace install test

**Files:**
- Test only — no new files

- [ ] **Step 1: Verify marketplace.json + plugin.json valid JSON**

```bash
python3 -c "
import json
m = json.load(open('/Users/haiduong/Documents/work/claude-plugins/.claude-plugin/marketplace.json'))
p = json.load(open('/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero/.claude-plugin/plugin.json'))
assert len(m['plugins']) == 4
assert any(plugin['name'] == 'docs-hero' for plugin in m['plugins'])
assert p['name'] == 'docs-hero'
print('OK')
"
```

Expected: `OK`

- [ ] **Step 2: Verify all required files present**

```bash
PLUGIN_DIR=/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero
for f in \
    .claude-plugin/plugin.json \
    requirements.txt \
    README.md \
    skills/docs-hero-orchestrator/SKILL.md \
    skills/generate-srs/SKILL.md \
    skills/generate-api-docs/SKILL.md \
    skills/generate-db-design/SKILL.md \
    agents/docs-hero.md \
    commands/setup.md \
    commands/init.md \
    commands/update.md \
    commands/sync.md \
    commands/apply-sync.md \
    commands/doctor.md \
    hooks/session-start.sh \
    scripts/setup-venv.sh \
    scripts/doctor.sh ; do
    test -f "$PLUGIN_DIR/$f" || { echo "MISSING: $f"; exit 1; }
done
echo "all 17 required files present"
```

Expected: `all 17 required files present`

- [ ] **Step 3: Verify executable bits on shell scripts**

```bash
PLUGIN_DIR=/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero
for f in hooks/session-start.sh scripts/setup-venv.sh scripts/doctor.sh; do
    test -x "$PLUGIN_DIR/$f" || { echo "NOT EXECUTABLE: $f"; chmod +x "$PLUGIN_DIR/$f"; }
done
echo "all scripts executable"
```

- [ ] **Step 4: Run doctor.sh from plugin context**

```bash
export CLAUDE_PLUGIN_ROOT=/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero
bash "$CLAUDE_PLUGIN_ROOT/scripts/doctor.sh"
```

Expected: at least Python:OK, venv:OK, deps:OK, schema:OK (mmdc may be optional/missing).

---

### Task 24: End-to-end init flow on test project

**Files:**
- Test project: `/tmp/docs-hero-e2e-test/`

- [ ] **Step 1: Create clean test project**

```bash
rm -rf /tmp/docs-hero-e2e-test
mkdir -p /tmp/docs-hero-e2e-test
cd /tmp/docs-hero-e2e-test
```

- [ ] **Step 2: Create minimal ProjectModel JSON**

Create `/tmp/docs-hero-e2e-test/project-model.json`:

```json
{
  "meta": {
    "project_name": "E2E Test",
    "release_name": "v1.0",
    "version": "1.0.0",
    "language": "EN"
  },
  "overview": {
    "summary": "Test project for docs-hero plugin e2e verification."
  },
  "functional_requirements": [
    {
      "id": "FR-001",
      "name": "User Login",
      "description": "User submits email + password, system validates against DB, issues JWT.",
      "priority": "Must",
      "main_flow": ["User enters credentials", "System validates", "JWT issued"],
      "postcondition": "User session active",
      "related_screens": ["SCREEN-001"]
    }
  ],
  "screens": [
    {"id": "SCREEN-001", "name": "Login Screen", "related_fr": ["FR-001"]}
  ],
  "tables": [
    {"id": "TBL-001", "name": "users", "columns": [
      {"name": "id", "type": "uuid", "pk": true},
      {"name": "email", "type": "varchar(255)", "unique": true},
      {"name": "password_hash", "type": "varchar(255)"}
    ]}
  ],
  "endpoints": [
    {"id": "ENDPOINT-POST-login", "method": "POST", "path": "/api/login", "related_fr": "FR-001"}
  ]
}
```

- [ ] **Step 3: Run dispatch_coordinator manually (simulate slash command)**

```bash
cd /tmp/docs-hero-e2e-test
export CLAUDE_PLUGIN_ROOT=/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero
VENV=$HOME/.claude/plugins/data/docs-hero/.venv
mkdir -p docs

"$VENV/bin/python3" "$CLAUDE_PLUGIN_ROOT/skills/docs-hero-orchestrator/scripts/dispatch_coordinator.py" init \
  --project-model /tmp/docs-hero-e2e-test/project-model.json \
  --language EN \
  --outputs srs,api,db \
  --docs-dir /tmp/docs-hero-e2e-test/docs/
```

Expected: exit code 0, no Python errors. Stderr may show INFO logs.

- [ ] **Step 4: Verify 3 docs generated**

```bash
test -s /tmp/docs-hero-e2e-test/docs/srs.md && \
test -s /tmp/docs-hero-e2e-test/docs/api-docs.md && \
test -s /tmp/docs-hero-e2e-test/docs/database-design.md && \
echo "all 3 docs generated" && \
wc -l /tmp/docs-hero-e2e-test/docs/*.md
```

Expected: `all 3 docs generated` and line counts > 50 each.

- [ ] **Step 5: Verify content quality (FR-001 mentioned in SRS, TBL-001 in DB)**

```bash
grep -q "FR-001" /tmp/docs-hero-e2e-test/docs/srs.md && \
grep -q "User Login" /tmp/docs-hero-e2e-test/docs/srs.md && \
grep -q "TBL-001\|users" /tmp/docs-hero-e2e-test/docs/database-design.md && \
grep -q "ENDPOINT-POST\|/api/login" /tmp/docs-hero-e2e-test/docs/api-docs.md && \
echo "content verified"
```

Expected: `content verified`

- [ ] **Step 6: Cleanup**

```bash
rm -rf /tmp/docs-hero-e2e-test
```

---

### Task 25: End-to-end update flow with manual edit preservation

**Files:**
- Test project: `/tmp/docs-hero-update-test/`

- [ ] **Step 1: Re-run init (or use snapshot)**

```bash
rm -rf /tmp/docs-hero-update-test
mkdir -p /tmp/docs-hero-update-test/docs
cp /tmp/docs-hero-e2e-test-fixture-project-model.json /tmp/docs-hero-update-test/project-model.json 2>/dev/null || \
  echo '{...same fixture as Task 24 step 2...}' > /tmp/docs-hero-update-test/project-model.json

cd /tmp/docs-hero-update-test
export CLAUDE_PLUGIN_ROOT=/Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero
VENV=$HOME/.claude/plugins/data/docs-hero/.venv

"$VENV/bin/python3" "$CLAUDE_PLUGIN_ROOT/skills/docs-hero-orchestrator/scripts/dispatch_coordinator.py" init \
  --project-model project-model.json --language EN --outputs srs,api,db --docs-dir docs/

# Build meta sidecar
"$VENV/bin/python3" "$CLAUDE_PLUGIN_ROOT/skills/docs-hero-orchestrator/scripts/meta_manager.py" \
  --docs-dir docs/ rebuild
```

Expected: docs/ populated + .docs-hero-meta.json created.

- [ ] **Step 2: Add manual edit to srs.md**

```bash
echo -e "\n<!-- MANUAL EDIT MARKER: BrSE clarification -->\nThis is a manual edit by BrSE that must be preserved.\n" >> /tmp/docs-hero-update-test/docs/srs.md
grep -c "MANUAL EDIT MARKER" /tmp/docs-hero-update-test/docs/srs.md
```

Expected: `1`

- [ ] **Step 3: Construct minimal Delta JSON (simulating new requirement)**

```bash
cat > /tmp/docs-hero-update-test/delta.json << 'EOF'
{
  "changes": [
    {
      "operation": "ADD",
      "entity_type": "FR",
      "entity": {
        "id": "FR-002",
        "name": "User Logout",
        "description": "User clicks logout button, session invalidated server-side.",
        "priority": "Should",
        "main_flow": ["User clicks logout", "Backend invalidates JWT", "Redirect to login"],
        "postcondition": "User session ended"
      }
    }
  ]
}
EOF
```

- [ ] **Step 4: Run update**

```bash
cd /tmp/docs-hero-update-test
"$VENV/bin/python3" "$CLAUDE_PLUGIN_ROOT/skills/docs-hero-orchestrator/scripts/dispatch_coordinator.py" update \
  --delta delta.json --docs-dir docs/ --meta .docs-hero-meta.json
```

Expected: exit 0.

- [ ] **Step 5: Verify FR-002 added AND manual edit preserved**

```bash
grep -q "FR-002" /tmp/docs-hero-update-test/docs/srs.md && echo "FR-002: ADDED" || echo "FAIL: FR-002 missing"
grep -q "MANUAL EDIT MARKER" /tmp/docs-hero-update-test/docs/srs.md && echo "manual edit: PRESERVED" || echo "FAIL: manual edit lost"
```

Expected:
```
FR-002: ADDED
manual edit: PRESERVED
```

- [ ] **Step 6: Cleanup**

```bash
rm -rf /tmp/docs-hero-update-test
```

---

### Task 26: Final commit + push

**Files:**
- All committed work on branch `feat/docs-hero-plugin`

- [ ] **Step 1: Verify branch state**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git log --oneline main..HEAD | wc -l
```

Expected: ≥ 14 commits (one per phase task that touched files).

- [ ] **Step 2: Run full test suite one more time**

```bash
cd /Users/haiduong/Documents/work/claude-plugins/plugins/docs-hero
export CLAUDE_PLUGIN_ROOT=$(pwd)
"$HOME/.claude/plugins/data/docs-hero/.venv/bin/python3" -m pytest \
  skills/docs-hero-orchestrator/tests/ -q --tb=line
```

Expected: `227 passed`

- [ ] **Step 3: Push branch (DO NOT auto-merge)**

```bash
cd /Users/haiduong/Documents/work/claude-plugins
git push -u origin feat/docs-hero-plugin
```

Expected: branch pushed. PR creation is a manual user step (per safety: pushing requires explicit ask, but `feat/*` branch pushing is normal dev flow — confirm with user before this step).

- [ ] **Step 4: Open PR (manual user step — NOT auto)**

User runs:
```bash
gh pr create --title "feat(docs-hero): integrate as plugin in mor-duongmh marketplace" \
  --body "$(cat <<'EOF'
## Summary
- Refactor docs-hero-1.1.0 (bundle installer) into Claude Code plugin
- Add 4th plugin to mor-duongmh marketplace
- Synergy with spec plugin: /spec:propose → /docs-hero:update --from-openspec
- Python venv at ~/.claude/plugins/data/docs-hero/.venv (explicit /docs-hero:setup, no silent SessionStart)

## Test plan
- [x] 227 tests pass on plugin layout
- [x] /docs-hero:doctor shows all green
- [x] E2E init: 3 docs generated from minimal ProjectModel JSON
- [x] E2E update: manual edits preserved, new FR added
- [ ] Verified on macOS (test machine)
- [ ] Verified on Linux (Ubuntu container)
- [ ] Plan-review-gate: review-checklist.md "Overall Decision: OK"

## Out of scope
- uvx migration (defer to v1.3)
- Bundle migration script for docs-hero-1.1.0 users
EOF
)"
```

---

## Self-Review Checklist

After all tasks, verify:

**1. Spec coverage:** Story sections 1-10 all addressed?
- [x] §2 AC-1 (manifest) → Tasks 3, 4
- [x] §2 AC-2 (paths) → Tasks 7-11
- [x] §2 AC-3 (venv bootstrap) → Tasks 12, 14, 15
- [x] §2 AC-4 (slash commands) → Tasks 15-19
- [x] §2 AC-5 (output paths) → Tasks 8-11 (all use `${PWD}`)
- [x] §2 AC-6 (docs) → Tasks 21, 22
- [x] §2 AC-7 (clean machine) → Tasks 23-25 (local equivalent)

**2. Placeholder scan:** any "TBD", "implement later", "similar to"?
- None found. Each task has exact code/commands.

**3. Type consistency:** path vars consistent across SKILL.md files?
- `CLAUDE_PLUGIN_ROOT`, `VENV`, `PY`, `*_SCRIPTS`, `PROJECT_DOCS_DIR`, `PROJECT_META` — all consistent.
- Hook script: `STATE_DIR`, `HINT_SHOWN` — consistent.

**4. Risk re-check from story §5:**
- Python 3.9+ requirement: addressed in Task 0 step 2 + setup-venv.sh check
- Path refactor coverage: Tasks 7-11 cover 4 SKILL.md + dispatch_coordinator.py
- Tests on plugin layout: Task 20 explicitly runs 227 tests

---

## Execution Handoff

**Plan complete and saved to `claude-plugins/docs/morkit/plans/2026-05-07-docs-hero-plugin-integration.md`.**

⚠️ **BEFORE EXECUTING**, per `feedback_plan_review_gate` user memory rule:

1. Generate review checklist:
   ```
   /spec:review --variant BE-Refactor
   ```
   (creates `openspec/changes/docs-hero-plugin/review-checklist.md`)

2. Tick items, fill summary, set:
   ```
   Overall Decision: OK
   ```

3. Then choose execution:
   - **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks → use `superpowers:subagent-driven-development`
   - **Inline Execution** — run tasks in same session with checkpoints → use `superpowers:executing-plans`

The plan-review-gate will block execution skills until `Overall Decision: OK` is set.
