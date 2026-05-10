# Vendored Superpowers Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a sibling plugin `superpowers@mor-duongmh` to the `mor-duongmh/claude-plugins` marketplace that mirrors upstream `obra/superpowers` content, refreshable via a manual sync script, with overlay-ready customization infrastructure.

**Architecture:** New folder `plugins/superpowers/` lives alongside existing `plugins/spec/`. A bash script (`scripts/sync-superpowers.sh`) downloads upstream tarball at a pinned version, verifies SHA256, wipes and replaces the vendored layer (`skills/`, `commands/`, `agents/`, `LICENSE`), then applies any `overlay/` customizations. Plugin name `superpowers` (matching upstream) keeps upstream's 34 internal `superpowers:*` cross-references intact.

**Tech Stack:** Bash 4+ (scripts and tests), `jq` (JSON), `curl` (download), `shasum`/`sha256sum` (verify), `tar` (extract), `git` (cleanliness check).

**Spec reference:** [`docs/superpowers/specs/2026-05-03-vendor-superpowers-plugin-design.md`](../specs/2026-05-03-vendor-superpowers-plugin-design.md)

---

## File Structure

### New files
- `plugins/superpowers/.claude-plugin/plugin.json` — plugin metadata
- `plugins/superpowers/README.md` — plugin-level README
- `plugins/superpowers/ATTRIBUTION.md` — credit upstream + MIT notice
- `plugins/superpowers/LICENSE` — copy of upstream MIT (placeholder at Task 1, real content via Task 8 sync)
- `plugins/superpowers/.vendor-manifest.json` — version, sha256, fetched_at, paths
- `plugins/superpowers/scripts/sync-superpowers.sh` — main sync orchestrator
- `plugins/superpowers/scripts/verify-vendor.sh` — post-sync sanity check
- `plugins/superpowers/scripts/start-overlay.sh` — helper to bootstrap an overlay
- `plugins/superpowers/scripts/lib/common.sh` — shared bash helpers
- `plugins/superpowers/scripts/tests/test-helper.sh` — assertion helpers for tests
- `plugins/superpowers/scripts/tests/test-sync-args.sh`
- `plugins/superpowers/scripts/tests/test-sync-dry-run.sh`
- `plugins/superpowers/scripts/tests/test-sync-full.sh`
- `plugins/superpowers/scripts/tests/test-sync-idempotent.sh`
- `plugins/superpowers/scripts/tests/test-sync-dirty-git.sh`
- `plugins/superpowers/scripts/tests/test-sync-overlay-apply.sh`
- `plugins/superpowers/scripts/tests/test-verify-vendor.sh`
- `plugins/superpowers/scripts/tests/test-start-overlay.sh`
- `plugins/superpowers/scripts/tests/run-all.sh` — runs every test-*.sh
- `plugins/superpowers/overlay/README.md` — overlay docs
- `plugins/superpowers/overlay/.gitkeep`
- `plugins/superpowers/skills/`, `plugins/superpowers/commands/`, `plugins/superpowers/agents/` — populated by Task 8 sync run

### Modified files
- `claude-plugins/.claude-plugin/marketplace.json` — append `superpowers` plugin entry (currently 1 entry)
- `claude-plugins/README.md` — update install flow (3 commands), mention 2 plugins
- `claude-plugins/.gitignore` — append `.preview/` if not already present

### Conventions
- All scripts are executable (`chmod +x`).
- All scripts begin with `#!/usr/bin/env bash` and `set -euo pipefail`.
- `lib/common.sh` is sourced by scripts AND tests for shared functions; it never auto-runs anything.
- Test files use the pattern: `tests/test-helper.sh` provides `assert_equal`, `assert_contains`, `assert_file_exists`. Each `test-*.sh` is a self-contained executable that exits non-zero on failure.
- Pinned upstream version for v1: **`5.0.7`** (matches what's currently cached on this machine and what the spec was designed against).

---

## Task 1: Scaffolding (no logic, no tests)

**Files:**
- Create: `plugins/superpowers/.claude-plugin/plugin.json`
- Create: `plugins/superpowers/README.md`
- Create: `plugins/superpowers/ATTRIBUTION.md`
- Create: `plugins/superpowers/LICENSE`
- Create: `plugins/superpowers/.vendor-manifest.json`
- Create: `plugins/superpowers/overlay/README.md`
- Create: `plugins/superpowers/overlay/.gitkeep`
- Create: `plugins/superpowers/.gitignore`

- [ ] **Step 1.1: Create `plugins/superpowers/.claude-plugin/plugin.json`**

```json
{
  "name": "superpowers",
  "version": "5.0.7-mor.1",
  "description": "Vendored fork of obra/superpowers. Skills, commands, and agents are mirrored as-is from upstream; sync via scripts/sync-superpowers.sh. Mor customizations live in overlay/.",
  "author": {
    "name": "Mor (Hai Duong)",
    "email": "duongmh@mor.com.vn"
  },
  "homepage": "https://github.com/mor-duongmh/claude-plugins/tree/main/plugins/superpowers",
  "repository": "https://github.com/mor-duongmh/claude-plugins",
  "license": "MIT",
  "keywords": ["superpowers", "tdd", "skills", "vendored-fork"]
}
```

- [ ] **Step 1.2: Create `plugins/superpowers/README.md`**

```markdown
# superpowers (vendored)

Mor's vendored fork of [obra/superpowers](https://github.com/obra/superpowers). Skills, commands, and agents under this plugin are mirrored verbatim from upstream — see [ATTRIBUTION.md](./ATTRIBUTION.md) for credit and licensing.

## Install

```
/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install superpowers@mor-duongmh
```

This plugin replaces upstream `superpowers@obra` (same plugin name → cannot coexist). If you have upstream installed, `/plugin uninstall superpowers@obra` first.

## Sync upstream

The vendored layer is refreshed by:

```bash
./scripts/sync-superpowers.sh           # use version pinned in .vendor-manifest.json
./scripts/sync-superpowers.sh 5.1.0     # bump to a specific upstream tag
./scripts/sync-superpowers.sh --dry-run 5.1.0
```

The script downloads the upstream tarball, verifies SHA256, wipes and re-copies vendored content, then applies any `overlay/` customizations.

## Customize

Place a file at `overlay/<same-relative-path>/...` to replace the vendored version after sync. See [overlay/README.md](./overlay/README.md).
```

- [ ] **Step 1.3: Create `plugins/superpowers/ATTRIBUTION.md`**

```markdown
# Attribution

This plugin is a **vendored fork** of [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent (jesse@fsck.com), licensed under the MIT License.

## Original work

- **Project:** Superpowers
- **Author:** Jesse Vincent
- **License:** MIT (see [LICENSE](./LICENSE))
- **Upstream:** https://github.com/obra/superpowers
- **Sponsor upstream:** https://github.com/sponsors/obra

## What this fork contains

The contents of `skills/`, `commands/`, and `agents/` are mirrored verbatim from a pinned upstream release (see `.vendor-manifest.json` for the exact version and SHA256). They are NOT modified by Mor.

Mor's customizations, when they exist, live separately in `overlay/` and are layered on top of the vendored content at sync time.

## Why we vendor under the name `superpowers`

Upstream skills contain 34 internal cross-references like `superpowers:executing-plans`. Plugin name must match for these to resolve. Renaming the plugin would require rewriting these references, breaking "vendor as-is" and increasing sync maintenance.

The cost: users cannot install both `superpowers@obra` and `superpowers@mor-duongmh` simultaneously. Mor's vendored fork is a drop-in replacement, not a coexisting alternative.

## Sync policy

`scripts/sync-superpowers.sh` downloads a specific upstream tarball release, verifies its SHA256, and replaces the vendored folders. The script never silently overwrites — it requires user confirmation.
```

- [ ] **Step 1.4: Create `plugins/superpowers/LICENSE`** (placeholder — Task 8 sync replaces with real upstream MIT)

```
MIT License

Copyright (c) 2025 Jesse Vincent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 1.5: Create `plugins/superpowers/.vendor-manifest.json` (initial stub)**

```json
{
  "name": "obra/superpowers",
  "source": "https://github.com/obra/superpowers",
  "version": null,
  "tarball_url": null,
  "tarball_sha256": null,
  "fetched_at": null,
  "fetched_by": "scripts/sync-superpowers.sh",
  "vendored_paths": ["skills/", "commands/", "agents/", "LICENSE"]
}
```

`version: null` means "never synced". Task 8 will populate.

- [ ] **Step 1.6: Create `plugins/superpowers/overlay/README.md`**

```markdown
# Overlay — Mor customizations on top of vendored Superpowers

This folder contains Mor-specific customizations layered on top of the vendored Superpowers content. The sync script applies overlay AFTER copying the vendored layer.

## How overlay works

For each path under `overlay/`, the sync script does:

1. Compute target = `<plugin-root>/<same-relative-path>` (i.e., remove the leading `overlay/`).
2. If target exists → REPLACE it with the overlay file (full replacement).
3. If target does not exist → ADD the overlay file as a new entry.

## Three use cases

| Use case | Overlay path | Effect |
|----------|-------------|--------|
| Override a skill from upstream | `overlay/skills/test-driven-development/SKILL.md` | Replaces vendored after sync |
| Add a Mor-only skill | `overlay/skills/mor-code-style/SKILL.md` | New skill, no upstream collision |
| Override an agent | `overlay/agents/code-reviewer.md` | Replaces vendored agent |

## Start a new overlay

Use the helper:

```bash
./scripts/start-overlay.sh skills/test-driven-development
```

It copies the live vendored skill into `overlay/...` and creates a `.overlay-meta.json` with the base version, so future drift detection (planned for v2) can warn when upstream changes the same file.

## Limitations (v1)

- **Replace mode only.** No append/patch mode — overlay file always replaces the entire target.
- **No automatic drift detection.** When you sync upstream to a newer version that touches an overlaid file, you must manually diff and reconcile.
```

- [ ] **Step 1.7: Create `plugins/superpowers/overlay/.gitkeep`** (empty file, ensures git tracks the directory)

```bash
touch plugins/superpowers/overlay/.gitkeep
```

- [ ] **Step 1.8: Create `plugins/superpowers/.gitignore`**

```
# Temporary sync artifacts
/tmp-sync/
*.tar.gz.tmp
```

- [ ] **Step 1.9: Verify scaffolding tree**

Run:
```bash
find plugins/superpowers -type f | sort
```

Expected output (8 files):
```
plugins/superpowers/.claude-plugin/plugin.json
plugins/superpowers/.gitignore
plugins/superpowers/.vendor-manifest.json
plugins/superpowers/ATTRIBUTION.md
plugins/superpowers/LICENSE
plugins/superpowers/README.md
plugins/superpowers/overlay/.gitkeep
plugins/superpowers/overlay/README.md
```

- [ ] **Step 1.10: Commit**

```bash
git add plugins/superpowers/
git commit -m "scaffold(superpowers): add plugin metadata, attribution, manifest stub"
```

---

## Task 2: Common helpers + test framework

**Files:**
- Create: `plugins/superpowers/scripts/lib/common.sh`
- Create: `plugins/superpowers/scripts/tests/test-helper.sh`
- Create: `plugins/superpowers/scripts/tests/run-all.sh`
- Create: `plugins/superpowers/scripts/tests/test-helper-sanity.sh`

- [ ] **Step 2.1: Write the failing test for `assert_equal`** (sanity check that the test framework works)

Create `plugins/superpowers/scripts/tests/test-helper-sanity.sh`:

```bash
#!/usr/bin/env bash
# Sanity check that test-helper.sh assertions behave correctly.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helper.sh"

assert_equal "5.0.7" "5.0.7" "version equality"
assert_contains "hello world" "world" "substring"
echo "PASS: test-helper-sanity"
```

Make executable:
```bash
chmod +x plugins/superpowers/scripts/tests/test-helper-sanity.sh
```

- [ ] **Step 2.2: Run test, verify it fails**

Run:
```bash
plugins/superpowers/scripts/tests/test-helper-sanity.sh
```
Expected: FAIL with "test-helper.sh: No such file or directory"

- [ ] **Step 2.3: Implement `plugins/superpowers/scripts/tests/test-helper.sh`**

```bash
#!/usr/bin/env bash
# Minimal assertion helpers for bash tests in this plugin.
# Source this file from any test-*.sh script.
set -euo pipefail

assert_equal() {
    local actual="$1" expected="$2" label="${3:-equality}"
    if [[ "$actual" != "$expected" ]]; then
        echo "FAIL ($label): expected '$expected' got '$actual'" >&2
        exit 1
    fi
}

assert_contains() {
    local haystack="$1" needle="$2" label="${3:-substring}"
    if [[ "$haystack" != *"$needle"* ]]; then
        echo "FAIL ($label): '$haystack' does not contain '$needle'" >&2
        exit 1
    fi
}

assert_file_exists() {
    local path="$1" label="${2:-file exists}"
    if [[ ! -f "$path" ]]; then
        echo "FAIL ($label): file '$path' does not exist" >&2
        exit 1
    fi
}

assert_dir_exists() {
    local path="$1" label="${2:-dir exists}"
    if [[ ! -d "$path" ]]; then
        echo "FAIL ($label): directory '$path' does not exist" >&2
        exit 1
    fi
}

assert_file_not_exists() {
    local path="$1" label="${2:-file absent}"
    if [[ -f "$path" ]]; then
        echo "FAIL ($label): file '$path' should not exist" >&2
        exit 1
    fi
}
```

Make sure it's NOT executable (it's only sourced, not run):
```bash
chmod 644 plugins/superpowers/scripts/tests/test-helper.sh
```

- [ ] **Step 2.4: Run test, verify it passes**

Run:
```bash
plugins/superpowers/scripts/tests/test-helper-sanity.sh
```
Expected: `PASS: test-helper-sanity`

- [ ] **Step 2.5: Implement `plugins/superpowers/scripts/lib/common.sh`**

```bash
#!/usr/bin/env bash
# Shared helpers for sync/verify/start-overlay scripts.
# This file is sourced — never run directly. No top-level side effects.
set -euo pipefail

# Resolve the plugin root from any script in scripts/ or scripts/lib/.
plugin_root() {
    local script_path="${BASH_SOURCE[1]:-$0}"
    local dir
    dir="$(cd "$(dirname "$script_path")" && pwd)"
    # Walk up until we find .claude-plugin/plugin.json
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/.claude-plugin/plugin.json" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "common.sh: cannot locate plugin root from $script_path" >&2
    return 1
}

# Cross-platform SHA256 (macOS shasum vs Linux sha256sum).
compute_sha256() {
    local file="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$file" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$file" | awk '{print $1}'
    else
        echo "common.sh: neither sha256sum nor shasum found" >&2
        return 1
    fi
}

require_command() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Required command '$cmd' not found in PATH" >&2
        exit 1
    fi
}

require_commands() {
    for cmd in "$@"; do
        require_command "$cmd"
    done
}

# Read a top-level field from .vendor-manifest.json. Returns "null" string for null/missing.
manifest_get() {
    local manifest="$1" field="$2"
    jq -r ".$field // \"null\"" "$manifest"
}

# Set a top-level field in .vendor-manifest.json (in place).
manifest_set() {
    local manifest="$1" field="$2" value="$3"
    local tmp
    tmp="$(mktemp)"
    jq --arg v "$value" ".$field = \$v" "$manifest" > "$tmp"
    mv "$tmp" "$manifest"
}

# Set a top-level field as null literal (jq distinguishes string "null" from JSON null).
manifest_set_null() {
    local manifest="$1" field="$2"
    local tmp
    tmp="$(mktemp)"
    jq ".$field = null" "$manifest" > "$tmp"
    mv "$tmp" "$manifest"
}
```

Note: `lib/common.sh` is sourced, never executed → keep mode 644:
```bash
chmod 644 plugins/superpowers/scripts/lib/common.sh
```

- [ ] **Step 2.6: Implement `plugins/superpowers/scripts/tests/run-all.sh`**

```bash
#!/usr/bin/env bash
# Run every test-*.sh in this directory.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

failed=0
total=0
for test in "$SCRIPT_DIR"/test-*.sh; do
    [[ -x "$test" ]] || continue
    total=$((total + 1))
    if ! "$test"; then
        failed=$((failed + 1))
    fi
done

echo
echo "Tests: $((total - failed))/$total passed"
[[ "$failed" -eq 0 ]]
```

```bash
chmod +x plugins/superpowers/scripts/tests/run-all.sh
```

- [ ] **Step 2.7: Verify run-all picks up the sanity test**

Run:
```bash
plugins/superpowers/scripts/tests/run-all.sh
```
Expected:
```
PASS: test-helper-sanity
Tests: 1/1 passed
```

- [ ] **Step 2.8: Commit**

```bash
git add plugins/superpowers/scripts/
git commit -m "test: add bash test framework and shared script helpers"
```

---

## Task 3: Sync script — argument parsing & usage

**Files:**
- Create: `plugins/superpowers/scripts/sync-superpowers.sh`
- Create: `plugins/superpowers/scripts/tests/test-sync-args.sh`

- [ ] **Step 3.1: Write failing test**

Create `plugins/superpowers/scripts/tests/test-sync-args.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helper.sh"

SYNC="$SCRIPT_DIR/../sync-superpowers.sh"

# Test 1: --help prints usage and exits 0
output="$("$SYNC" --help 2>&1)"
assert_contains "$output" "Usage:" "help shows Usage"
assert_contains "$output" "sync-superpowers.sh" "help shows script name"

# Test 2: invalid flag fails with helpful message
if "$SYNC" --bogus 2>/dev/null; then
    echo "FAIL: --bogus should have errored" >&2
    exit 1
fi

# Test 3: valid version arg is accepted (will fail later for other reasons; we only check parsing here)
output="$("$SYNC" --help 5.1.0 2>&1 || true)"
assert_contains "$output" "Usage:" "version arg with --help still shows usage"

echo "PASS: test-sync-args"
```

```bash
chmod +x plugins/superpowers/scripts/tests/test-sync-args.sh
```

- [ ] **Step 3.2: Run test, verify it fails**

Run:
```bash
plugins/superpowers/scripts/tests/test-sync-args.sh
```
Expected: FAIL with "No such file or directory" or similar (sync-superpowers.sh doesn't exist yet).

- [ ] **Step 3.3: Implement minimal `plugins/superpowers/scripts/sync-superpowers.sh`** (just enough for arg test to pass)

```bash
#!/usr/bin/env bash
# sync-superpowers.sh — refresh the vendored Superpowers layer from upstream.
# Usage:
#   ./sync-superpowers.sh                    Use version pinned in .vendor-manifest.json
#   ./sync-superpowers.sh <version>          Bump to specific upstream tag (e.g. 5.1.0)
#   ./sync-superpowers.sh --dry-run [<ver>]  Show what would change without writing
#   ./sync-superpowers.sh --help             Show this help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

DRY_RUN=0
TARGET_VERSION=""

print_usage() {
    cat <<'EOF'
Usage: sync-superpowers.sh [--dry-run] [--help] [<version>]

Refresh the vendored Superpowers layer from obra/superpowers.

Options:
  --dry-run    Print actions without writing files
  --help       Show this help

Arguments:
  <version>    Upstream tag to sync (e.g. 5.1.0). If omitted, the version
               pinned in .vendor-manifest.json is used.

Examples:
  sync-superpowers.sh                  # use pinned version
  sync-superpowers.sh 5.1.0            # bump to 5.1.0
  sync-superpowers.sh --dry-run 5.1.0  # preview only
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                print_usage
                exit 0
                ;;
            --dry-run)
                DRY_RUN=1
                shift
                ;;
            -*)
                echo "Unknown option: $1" >&2
                print_usage >&2
                exit 2
                ;;
            *)
                if [[ -z "$TARGET_VERSION" ]]; then
                    TARGET_VERSION="$1"
                    shift
                else
                    echo "Unexpected extra argument: $1" >&2
                    exit 2
                fi
                ;;
        esac
    done
}

main() {
    parse_args "$@"
    # Subsequent tasks fill in the rest.
    echo "(stub) DRY_RUN=$DRY_RUN TARGET_VERSION=${TARGET_VERSION:-<from manifest>}"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

```bash
chmod +x plugins/superpowers/scripts/sync-superpowers.sh
```

- [ ] **Step 3.4: Run test, verify it passes**

```bash
plugins/superpowers/scripts/tests/test-sync-args.sh
```
Expected: `PASS: test-sync-args`

- [ ] **Step 3.5: Run all tests as regression check**

```bash
plugins/superpowers/scripts/tests/run-all.sh
```
Expected: `Tests: 2/2 passed`

- [ ] **Step 3.6: Commit**

```bash
git add plugins/superpowers/scripts/sync-superpowers.sh plugins/superpowers/scripts/tests/test-sync-args.sh
git commit -m "feat(sync): add argument parsing and --help"
```

---

## Task 4: Sync script — dry-run mode

**Files:**
- Modify: `plugins/superpowers/scripts/sync-superpowers.sh`
- Create: `plugins/superpowers/scripts/tests/test-sync-dry-run.sh`

- [ ] **Step 4.1: Write failing test**

Create `plugins/superpowers/scripts/tests/test-sync-dry-run.sh`:

```bash
#!/usr/bin/env bash
# Verify that --dry-run prints the planned actions without writing files.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helper.sh"

SYNC="$SCRIPT_DIR/../sync-superpowers.sh"
PLUGIN_ROOT="$SCRIPT_DIR/../.."

# Snapshot manifest contents before running
manifest_before="$(cat "$PLUGIN_ROOT/.vendor-manifest.json")"

# Run dry-run with explicit version
output="$("$SYNC" --dry-run 5.0.7 2>&1)"

assert_contains "$output" "DRY RUN" "dry-run banner"
assert_contains "$output" "5.0.7" "target version shown"
assert_contains "$output" "would download" "download action listed"
assert_contains "$output" "would extract" "extract action listed"

# Manifest must be unchanged
manifest_after="$(cat "$PLUGIN_ROOT/.vendor-manifest.json")"
assert_equal "$manifest_after" "$manifest_before" "manifest unchanged after dry-run"

echo "PASS: test-sync-dry-run"
```

```bash
chmod +x plugins/superpowers/scripts/tests/test-sync-dry-run.sh
```

- [ ] **Step 4.2: Run, verify it fails**

```bash
plugins/superpowers/scripts/tests/test-sync-dry-run.sh
```
Expected: FAIL on "DRY RUN" not found in output.

- [ ] **Step 4.3: Extend `sync-superpowers.sh` with dry-run output**

In `sync-superpowers.sh`, replace the `main()` function with:

```bash
resolve_version() {
    local manifest="$PLUGIN_ROOT/.vendor-manifest.json"
    if [[ -n "$TARGET_VERSION" ]]; then
        echo "$TARGET_VERSION"
        return
    fi
    local pinned
    pinned="$(manifest_get "$manifest" version)"
    if [[ "$pinned" == "null" ]]; then
        echo "No version pinned in manifest. Pass version explicitly: ./sync-superpowers.sh <version>" >&2
        exit 1
    fi
    echo "$pinned"
}

print_dry_run_plan() {
    local version="$1"
    cat <<EOF
=== DRY RUN ===
Target version: $version
Tarball URL:    https://github.com/obra/superpowers/archive/refs/tags/v$version.tar.gz

Plan:
  1. would download tarball to /tmp
  2. would compute SHA256 and verify against manifest (or store if first sync)
  3. would extract to a tempdir
  4. would wipe: $PLUGIN_ROOT/skills $PLUGIN_ROOT/commands $PLUGIN_ROOT/agents $PLUGIN_ROOT/LICENSE
  5. would copy from extracted tree
  6. would apply overlay/ on top
  7. would update .vendor-manifest.json

No files were written.
EOF
}

main() {
    parse_args "$@"
    PLUGIN_ROOT="$(plugin_root)"
    require_commands curl tar jq git

    local version
    version="$(resolve_version)"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        print_dry_run_plan "$version"
        exit 0
    fi

    echo "(real sync not yet implemented — see Task 5+)"
}
```

- [ ] **Step 4.4: Run, verify it passes**

```bash
plugins/superpowers/scripts/tests/test-sync-dry-run.sh
```
Expected: `PASS: test-sync-dry-run`

- [ ] **Step 4.5: Run all tests**

```bash
plugins/superpowers/scripts/tests/run-all.sh
```
Expected: 3/3 passed.

- [ ] **Step 4.6: Commit**

```bash
git add plugins/superpowers/scripts/sync-superpowers.sh plugins/superpowers/scripts/tests/test-sync-dry-run.sh
git commit -m "feat(sync): add --dry-run plan output"
```

---

## Task 5: Sync script — git cleanliness check

**Files:**
- Modify: `plugins/superpowers/scripts/sync-superpowers.sh`
- Create: `plugins/superpowers/scripts/tests/test-sync-dirty-git.sh`

- [ ] **Step 5.1: Write failing test**

Create `plugins/superpowers/scripts/tests/test-sync-dirty-git.sh`:

```bash
#!/usr/bin/env bash
# Verify sync aborts when vendored dirs have uncommitted changes.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helper.sh"

SYNC="$SCRIPT_DIR/../sync-superpowers.sh"
PLUGIN_ROOT="$SCRIPT_DIR/../.."

# Setup: create a dirty vendored file
mkdir -p "$PLUGIN_ROOT/skills/dummy"
echo "uncommitted" > "$PLUGIN_ROOT/skills/dummy/SKILL.md"

cleanup() {
    rm -rf "$PLUGIN_ROOT/skills/dummy"
}
trap cleanup EXIT

# Try real sync (not dry-run) — should abort due to dirty state
if output="$(echo n | "$SYNC" 5.0.7 2>&1)"; then
    echo "FAIL: sync should have aborted on dirty git state" >&2
    echo "Output was: $output" >&2
    exit 1
fi

assert_contains "$output" "uncommitted changes" "abort message mentions uncommitted"

echo "PASS: test-sync-dirty-git"
```

```bash
chmod +x plugins/superpowers/scripts/tests/test-sync-dirty-git.sh
```

- [ ] **Step 5.2: Run, verify it fails**

Expected: FAIL — sync stub doesn't yet check git state.

- [ ] **Step 5.3: Implement `check_git_clean` in `sync-superpowers.sh`**

Add inside `sync-superpowers.sh`, before `main()`:

```bash
check_git_clean() {
    local plugin_root="$1"
    # Check uncommitted changes inside the vendored layer paths
    local dirty
    dirty="$(cd "$plugin_root" && git status --porcelain skills/ commands/ agents/ LICENSE 2>/dev/null || true)"
    if [[ -n "$dirty" ]]; then
        echo "Refusing to sync: vendored layer has uncommitted changes." >&2
        echo "Commit, stash, or discard them before running sync." >&2
        echo "$dirty" >&2
        exit 1
    fi
}
```

In `main()`, after resolving version and BEFORE the dry-run branch, leave dry-run untouched. After the dry-run early-exit, add (this is the start of real-sync flow — subsequent tasks fill in more):

```bash
main() {
    parse_args "$@"
    PLUGIN_ROOT="$(plugin_root)"
    require_commands curl tar jq git

    local version
    version="$(resolve_version)"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        print_dry_run_plan "$version"
        exit 0
    fi

    check_git_clean "$PLUGIN_ROOT"
    echo "(real sync not yet implemented — see Task 6+)"
}
```

- [ ] **Step 5.4: Run, verify it passes**

```bash
plugins/superpowers/scripts/tests/test-sync-dirty-git.sh
```
Expected: `PASS: test-sync-dirty-git`

- [ ] **Step 5.5: Run all tests**

Expected: 4/4 passed.

- [ ] **Step 5.6: Commit**

```bash
git add plugins/superpowers/scripts/sync-superpowers.sh plugins/superpowers/scripts/tests/test-sync-dirty-git.sh
git commit -m "feat(sync): abort when vendored layer has uncommitted changes"
```

---

## Task 6: Sync script — full download → verify → extract → write

**Files:**
- Modify: `plugins/superpowers/scripts/sync-superpowers.sh`
- Create: `plugins/superpowers/scripts/tests/test-sync-full.sh`

This is the largest task. The test downloads a real upstream tarball (~1MB, cached after first run).

- [ ] **Step 6.1: Write failing test**

Create `plugins/superpowers/scripts/tests/test-sync-full.sh`:

```bash
#!/usr/bin/env bash
# End-to-end test: run sync against real upstream and verify file structure + manifest.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helper.sh"

SYNC="$SCRIPT_DIR/../sync-superpowers.sh"
PLUGIN_ROOT="$SCRIPT_DIR/../.."

TEST_VERSION="5.0.7"

# Ensure clean state — backup live folders if they happen to exist
backup="$(mktemp -d)"
for d in skills commands agents LICENSE; do
    [[ -e "$PLUGIN_ROOT/$d" ]] && mv "$PLUGIN_ROOT/$d" "$backup/$d"
done
manifest_backup="$(cat "$PLUGIN_ROOT/.vendor-manifest.json")"

cleanup() {
    rm -rf "$PLUGIN_ROOT/skills" "$PLUGIN_ROOT/commands" "$PLUGIN_ROOT/agents" "$PLUGIN_ROOT/LICENSE"
    for d in skills commands agents LICENSE; do
        [[ -e "$backup/$d" ]] && mv "$backup/$d" "$PLUGIN_ROOT/$d"
    done
    echo "$manifest_backup" > "$PLUGIN_ROOT/.vendor-manifest.json"
    rm -rf "$backup"
}
trap cleanup EXIT

# Run full sync (auto-confirm with 'y')
echo "y" | "$SYNC" "$TEST_VERSION"

# Verify file structure
assert_dir_exists "$PLUGIN_ROOT/skills/brainstorming" "brainstorming skill present"
assert_dir_exists "$PLUGIN_ROOT/skills/executing-plans" "executing-plans skill present"
assert_file_exists "$PLUGIN_ROOT/skills/brainstorming/SKILL.md" "SKILL.md present"
assert_file_exists "$PLUGIN_ROOT/commands/brainstorm.md" "brainstorm command present"
assert_file_exists "$PLUGIN_ROOT/LICENSE" "LICENSE present"

# Verify skill count
skill_count="$(find "$PLUGIN_ROOT/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
assert_equal "$skill_count" "14" "14 skill dirs"

# Verify manifest updated
manifest_version="$(jq -r .version "$PLUGIN_ROOT/.vendor-manifest.json")"
assert_equal "$manifest_version" "$TEST_VERSION" "manifest version updated"

manifest_sha="$(jq -r .tarball_sha256 "$PLUGIN_ROOT/.vendor-manifest.json")"
[[ ${#manifest_sha} -eq 64 ]] || { echo "FAIL: tarball_sha256 not 64 chars" >&2; exit 1; }

manifest_fetched_at="$(jq -r .fetched_at "$PLUGIN_ROOT/.vendor-manifest.json")"
assert_contains "$manifest_fetched_at" "T" "fetched_at is ISO8601-ish"

echo "PASS: test-sync-full"
```

```bash
chmod +x plugins/superpowers/scripts/tests/test-sync-full.sh
```

- [ ] **Step 6.2: Run, verify it fails**

Expected: FAIL — main sync logic isn't implemented yet.

- [ ] **Step 6.3: Implement download/extract/copy in `sync-superpowers.sh`**

Add these functions (above `main()`, after `check_git_clean`):

```bash
download_tarball() {
    local version="$1" dest="$2"
    local url="https://github.com/obra/superpowers/archive/refs/tags/v${version}.tar.gz"
    echo "Downloading $url"
    if ! curl -fsSL "$url" -o "$dest"; then
        echo "Download failed for $url" >&2
        exit 1
    fi
}

verify_or_record_sha256() {
    # Args: tarball_path manifest_path target_version
    # If manifest already has a SHA for this version → verify match.
    # Else → store the freshly-computed SHA into manifest.
    local tarball="$1" manifest="$2" version="$3"
    local actual
    actual="$(compute_sha256 "$tarball")"
    local recorded_version recorded_sha
    recorded_version="$(manifest_get "$manifest" version)"
    recorded_sha="$(manifest_get "$manifest" tarball_sha256)"
    if [[ "$recorded_version" == "$version" && "$recorded_sha" != "null" ]]; then
        if [[ "$actual" != "$recorded_sha" ]]; then
            echo "SHA256 mismatch for v$version!" >&2
            echo "  expected: $recorded_sha" >&2
            echo "  actual:   $actual" >&2
            exit 1
        fi
        echo "✓ SHA256 verified: $actual"
    else
        echo "✓ SHA256 computed (first sync of v$version): $actual"
    fi
    echo "$actual"  # last line is the sha for caller
}

extract_tarball() {
    local tarball="$1" dest="$2"
    mkdir -p "$dest"
    tar -xzf "$tarball" -C "$dest"
    # Upstream tarball extracts as superpowers-<version>/...
    local extracted_root
    extracted_root="$(find "$dest" -mindepth 1 -maxdepth 1 -type d | head -1)"
    echo "$extracted_root"
}

wipe_vendored_layer() {
    local plugin_root="$1"
    rm -rf "$plugin_root/skills" "$plugin_root/commands" "$plugin_root/agents" "$plugin_root/LICENSE"
}

copy_vendored_layer() {
    local src="$1" plugin_root="$2"
    for path in skills commands agents LICENSE; do
        if [[ -e "$src/$path" ]]; then
            cp -R "$src/$path" "$plugin_root/$path"
        fi
    done
}

apply_overlay() {
    local plugin_root="$1"
    local overlay="$plugin_root/overlay"
    [[ -d "$overlay" ]] || return 0
    local applied=0
    for sub in skills commands agents; do
        [[ -d "$overlay/$sub" ]] || continue
        # Copy overlay contents into plugin_root, replacing existing files.
        cp -R "$overlay/$sub/." "$plugin_root/$sub/"
        applied=$((applied + 1))
    done
    if [[ "$applied" -gt 0 ]]; then
        echo "✓ Applied overlay layer"
    fi
}

update_manifest() {
    local manifest="$1" version="$2" sha="$3"
    local url="https://github.com/obra/superpowers/archive/refs/tags/v${version}.tar.gz"
    local now
    now="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    manifest_set "$manifest" version "$version"
    manifest_set "$manifest" tarball_url "$url"
    manifest_set "$manifest" tarball_sha256 "$sha"
    manifest_set "$manifest" fetched_at "$now"
}

confirm_or_abort() {
    local current="$1" target="$2"
    echo
    echo "Sync vendored Superpowers layer"
    echo "  Current: ${current}"
    echo "  Target:  ${target}"
    read -r -p "Continue? [y/N]: " ans
    if [[ "$ans" != "y" && "$ans" != "Y" ]]; then
        echo "Aborted by user."
        exit 0
    fi
}
```

Replace `main()` with full orchestration:

```bash
main() {
    parse_args "$@"
    PLUGIN_ROOT="$(plugin_root)"
    require_commands curl tar jq git

    local manifest="$PLUGIN_ROOT/.vendor-manifest.json"
    local version
    version="$(resolve_version)"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        print_dry_run_plan "$version"
        exit 0
    fi

    check_git_clean "$PLUGIN_ROOT"

    local current
    current="$(manifest_get "$manifest" version)"
    confirm_or_abort "$current" "$version"

    local tmp
    tmp="$(mktemp -d)"
    trap 'rm -rf "$tmp"' EXIT

    local tarball="$tmp/superpowers-v${version}.tar.gz"
    download_tarball "$version" "$tarball"

    local sha
    sha="$(verify_or_record_sha256 "$tarball" "$manifest" "$version" | tail -1)"

    local extract_dir="$tmp/extract"
    local extracted
    extracted="$(extract_tarball "$tarball" "$extract_dir")"

    wipe_vendored_layer "$PLUGIN_ROOT"
    copy_vendored_layer "$extracted" "$PLUGIN_ROOT"
    apply_overlay "$PLUGIN_ROOT"
    update_manifest "$manifest" "$version" "$sha"

    echo
    echo "✓ Vendored layer synced to v$version"
    echo "  SHA256: $sha"
    echo
    echo "Suggested commit:"
    echo "  git add plugins/superpowers/{skills,commands,agents,LICENSE,.vendor-manifest.json}"
    echo "  git commit -m \"chore(superpowers): vendor upstream v$version\""
}
```

- [ ] **Step 6.4: Run, verify it passes**

```bash
plugins/superpowers/scripts/tests/test-sync-full.sh
```
Expected: `PASS: test-sync-full` (test takes ~5–15s due to network).

If the test fails because upstream tag `v5.0.7` no longer exists or the URL has changed, abort and investigate. Do NOT silently bypass.

- [ ] **Step 6.5: Run all tests as regression check**

```bash
plugins/superpowers/scripts/tests/run-all.sh
```
Expected: 5/5 passed.

- [ ] **Step 6.6: Commit (script + test only — vendored content goes in Task 8)**

The full sync test ran and populated `skills/`, `commands/`, `agents/`, `LICENSE` and updated the manifest. The test's `cleanup()` trap reverted those changes — verify the working tree is clean for the script files only:

```bash
git status
```

If the test's cleanup left vendored folders behind for any reason, run:

```bash
rm -rf plugins/superpowers/{skills,commands,agents,LICENSE}
git checkout -- plugins/superpowers/.vendor-manifest.json
```

Then commit:

```bash
git add plugins/superpowers/scripts/sync-superpowers.sh plugins/superpowers/scripts/tests/test-sync-full.sh
git commit -m "feat(sync): full download → verify → extract → write flow"
```

---

## Task 7: Sync script — idempotency

**Files:**
- Modify: `plugins/superpowers/scripts/sync-superpowers.sh`
- Create: `plugins/superpowers/scripts/tests/test-sync-idempotent.sh`

- [ ] **Step 7.1: Write failing test**

Create `plugins/superpowers/scripts/tests/test-sync-idempotent.sh`:

```bash
#!/usr/bin/env bash
# Running sync at the same version twice should be a no-op the second time.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helper.sh"

SYNC="$SCRIPT_DIR/../sync-superpowers.sh"
PLUGIN_ROOT="$SCRIPT_DIR/../.."
TEST_VERSION="5.0.7"

# Backup state
backup="$(mktemp -d)"
for d in skills commands agents LICENSE; do
    [[ -e "$PLUGIN_ROOT/$d" ]] && mv "$PLUGIN_ROOT/$d" "$backup/$d"
done
manifest_backup="$(cat "$PLUGIN_ROOT/.vendor-manifest.json")"

cleanup() {
    rm -rf "$PLUGIN_ROOT/skills" "$PLUGIN_ROOT/commands" "$PLUGIN_ROOT/agents" "$PLUGIN_ROOT/LICENSE"
    for d in skills commands agents LICENSE; do
        [[ -e "$backup/$d" ]] && mv "$backup/$d" "$PLUGIN_ROOT/$d"
    done
    echo "$manifest_backup" > "$PLUGIN_ROOT/.vendor-manifest.json"
    rm -rf "$backup"
}
trap cleanup EXIT

# First sync
echo "y" | "$SYNC" "$TEST_VERSION" >/dev/null

# Capture state after first sync
sha_first="$(jq -r .tarball_sha256 "$PLUGIN_ROOT/.vendor-manifest.json")"
mtime_first="$(stat -f %m "$PLUGIN_ROOT/skills/brainstorming/SKILL.md" 2>/dev/null || stat -c %Y "$PLUGIN_ROOT/skills/brainstorming/SKILL.md")"

# Second sync (same version) — should detect "already at target" and skip work
output="$(echo "y" | "$SYNC" "$TEST_VERSION" 2>&1)"
assert_contains "$output" "already at v$TEST_VERSION" "idempotent skip message"

# State must not change
sha_second="$(jq -r .tarball_sha256 "$PLUGIN_ROOT/.vendor-manifest.json")"
assert_equal "$sha_second" "$sha_first" "sha unchanged"

mtime_second="$(stat -f %m "$PLUGIN_ROOT/skills/brainstorming/SKILL.md" 2>/dev/null || stat -c %Y "$PLUGIN_ROOT/skills/brainstorming/SKILL.md")"
assert_equal "$mtime_second" "$mtime_first" "skill file mtime unchanged"

echo "PASS: test-sync-idempotent"
```

```bash
chmod +x plugins/superpowers/scripts/tests/test-sync-idempotent.sh
```

- [ ] **Step 7.2: Run, verify it fails**

Expected: FAIL on "already at v5.0.7" not in output (current main always re-downloads).

- [ ] **Step 7.3: Add idempotency check to `main()` in sync-superpowers.sh**

Add this block to `main()`, immediately AFTER the `check_git_clean` call and BEFORE `confirm_or_abort`:

```bash
    local current
    current="$(manifest_get "$manifest" version)"
    if [[ "$current" == "$version" ]]; then
        echo "✓ already at v$version (manifest matches target). Nothing to do."
        echo "  To force re-fetch, manually clear .vendor-manifest.json version field."
        exit 0
    fi
```

Note the `current` variable was already declared and assigned before `confirm_or_abort` in Task 6 — move the early-exit ABOVE that prior assignment, OR refactor to avoid the duplicate declaration (recommended: keep the single declaration and check before `confirm_or_abort`):

```bash
    local current
    current="$(manifest_get "$manifest" version)"
    if [[ "$current" == "$version" ]]; then
        echo "✓ already at v$version (manifest matches target). Nothing to do."
        echo "  To force re-fetch, manually clear .vendor-manifest.json version field."
        exit 0
    fi
    confirm_or_abort "$current" "$version"
```

- [ ] **Step 7.4: Run, verify it passes**

```bash
plugins/superpowers/scripts/tests/test-sync-idempotent.sh
```
Expected: `PASS: test-sync-idempotent`

- [ ] **Step 7.5: Run all tests**

Expected: 6/6 passed.

- [ ] **Step 7.6: Commit**

```bash
git add plugins/superpowers/scripts/sync-superpowers.sh plugins/superpowers/scripts/tests/test-sync-idempotent.sh
git commit -m "feat(sync): skip re-fetch when manifest already at target version"
```

---

## Task 8: First production sync — populate the vendored layer

This is a one-time real run that bakes the v5.0.7 vendored content into the repo.

**Files:**
- Modify (via script): `plugins/superpowers/.vendor-manifest.json`
- Create (via script): `plugins/superpowers/skills/`, `commands/`, `agents/`, `LICENSE`

- [ ] **Step 8.1: Verify pre-sync state is clean**

```bash
git status plugins/superpowers/
```
Expected: clean (no uncommitted changes in `plugins/superpowers/`).

- [ ] **Step 8.2: Run the sync**

```bash
cd plugins/superpowers
echo "y" | ./scripts/sync-superpowers.sh 5.0.7
cd -
```
Expected output ends with:
```
✓ Vendored layer synced to v5.0.7
  SHA256: <64-char hex>
```

- [ ] **Step 8.3: Verify file structure**

```bash
find plugins/superpowers/skills -mindepth 1 -maxdepth 1 -type d | wc -l
```
Expected: `14`

```bash
ls plugins/superpowers/commands/
```
Expected (3 files): `brainstorm.md  execute-plan.md  write-plan.md`

```bash
test -f plugins/superpowers/LICENSE && echo "LICENSE OK"
```
Expected: `LICENSE OK`

- [ ] **Step 8.4: Verify manifest**

```bash
jq . plugins/superpowers/.vendor-manifest.json
```
Expected fields: `version: "5.0.7"`, `tarball_sha256: <64 hex>`, `fetched_at: <ISO timestamp>`, `tarball_url: ...v5.0.7.tar.gz`.

- [ ] **Step 8.5: Run regression**

```bash
plugins/superpowers/scripts/tests/run-all.sh
```
Expected: 6/6 passed.

- [ ] **Step 8.6: Commit (large diff — the vendored content)**

```bash
git add plugins/superpowers/skills/ plugins/superpowers/commands/ plugins/superpowers/agents/ plugins/superpowers/LICENSE plugins/superpowers/.vendor-manifest.json
git commit -m "chore(superpowers): vendor upstream v5.0.7 (initial import)"
```

---

## Task 9: Sync script — overlay apply

**Files:**
- Create: `plugins/superpowers/scripts/tests/test-sync-overlay-apply.sh`

The `apply_overlay` function was already implemented in Task 6. This task verifies it works.

- [ ] **Step 9.1: Write failing test (no overlay yet → expect overlay to be applied)**

Create `plugins/superpowers/scripts/tests/test-sync-overlay-apply.sh`:

```bash
#!/usr/bin/env bash
# Test that overlay/<path>/<file> replaces vendored <path>/<file> after sync.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helper.sh"

SYNC="$SCRIPT_DIR/../sync-superpowers.sh"
PLUGIN_ROOT="$SCRIPT_DIR/../.."
TEST_VERSION="5.0.7"

# Backup state
backup="$(mktemp -d)"
for d in skills commands agents LICENSE overlay; do
    [[ -e "$PLUGIN_ROOT/$d" ]] && cp -R "$PLUGIN_ROOT/$d" "$backup/$d"
done
manifest_backup="$(cat "$PLUGIN_ROOT/.vendor-manifest.json")"
# Clear manifest version so sync runs (avoid idempotent skip)
jq '.version = null | .tarball_sha256 = null' "$PLUGIN_ROOT/.vendor-manifest.json" > "$PLUGIN_ROOT/.vendor-manifest.json.tmp"
mv "$PLUGIN_ROOT/.vendor-manifest.json.tmp" "$PLUGIN_ROOT/.vendor-manifest.json"

cleanup() {
    rm -rf "$PLUGIN_ROOT/skills" "$PLUGIN_ROOT/commands" "$PLUGIN_ROOT/agents" "$PLUGIN_ROOT/LICENSE" "$PLUGIN_ROOT/overlay"
    for d in skills commands agents LICENSE overlay; do
        [[ -e "$backup/$d" ]] && cp -R "$backup/$d" "$PLUGIN_ROOT/$d"
    done
    echo "$manifest_backup" > "$PLUGIN_ROOT/.vendor-manifest.json"
    rm -rf "$backup"
}
trap cleanup EXIT

# Setup overlay: create a file that will replace a known vendored skill
mkdir -p "$PLUGIN_ROOT/overlay/skills/brainstorming"
echo "MOR-OVERLAY-MARKER" > "$PLUGIN_ROOT/overlay/skills/brainstorming/SKILL.md"

# Run sync
echo "y" | "$SYNC" "$TEST_VERSION" >/dev/null

# After sync, the overlay file should have replaced the vendored one
content="$(cat "$PLUGIN_ROOT/skills/brainstorming/SKILL.md")"
assert_equal "$content" "MOR-OVERLAY-MARKER" "overlay replaced vendored SKILL.md"

echo "PASS: test-sync-overlay-apply"
```

```bash
chmod +x plugins/superpowers/scripts/tests/test-sync-overlay-apply.sh
```

- [ ] **Step 9.2: Run test, verify it passes**

(`apply_overlay` is already implemented in Task 6, so this test should pass on first run.)

```bash
plugins/superpowers/scripts/tests/test-sync-overlay-apply.sh
```
Expected: `PASS: test-sync-overlay-apply`

If it fails: review `apply_overlay` in `sync-superpowers.sh` and fix.

- [ ] **Step 9.3: Run all tests**

Expected: 7/7 passed.

- [ ] **Step 9.4: Commit**

```bash
git add plugins/superpowers/scripts/tests/test-sync-overlay-apply.sh
git commit -m "test(sync): cover overlay apply replacing vendored file"
```

---

## Task 10: verify-vendor.sh script

**Files:**
- Create: `plugins/superpowers/scripts/verify-vendor.sh`
- Create: `plugins/superpowers/scripts/tests/test-verify-vendor.sh`

`verify-vendor.sh` re-fetches the upstream tarball recorded in the manifest, recomputes SHA256, and compares against the recorded value. Catches tampering or accidental edits to vendored files.

- [ ] **Step 10.1: Write failing test**

Create `plugins/superpowers/scripts/tests/test-verify-vendor.sh`:

```bash
#!/usr/bin/env bash
# Verify-vendor must pass after a clean sync.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helper.sh"

VERIFY="$SCRIPT_DIR/../verify-vendor.sh"

# Assumes Task 8 already ran a real sync — manifest has version + sha
output="$("$VERIFY" 2>&1)"
assert_contains "$output" "OK" "verify reports OK"
assert_contains "$output" "$(jq -r .version "$SCRIPT_DIR/../../.vendor-manifest.json")" "verify shows version"

echo "PASS: test-verify-vendor"
```

```bash
chmod +x plugins/superpowers/scripts/tests/test-verify-vendor.sh
```

- [ ] **Step 10.2: Run, verify it fails**

Expected: FAIL — script doesn't exist.

- [ ] **Step 10.3: Implement `plugins/superpowers/scripts/verify-vendor.sh`**

```bash
#!/usr/bin/env bash
# verify-vendor.sh — verify the vendored layer matches the manifest's recorded SHA256.
# Re-downloads the upstream tarball and compares its hash to .vendor-manifest.json.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

main() {
    local plugin_root
    plugin_root="$(plugin_root)"
    require_commands curl jq
    local manifest="$plugin_root/.vendor-manifest.json"
    local version url expected_sha
    version="$(manifest_get "$manifest" version)"
    url="$(manifest_get "$manifest" tarball_url)"
    expected_sha="$(manifest_get "$manifest" tarball_sha256)"

    if [[ "$version" == "null" || "$url" == "null" || "$expected_sha" == "null" ]]; then
        echo "Manifest is incomplete — run sync-superpowers.sh first." >&2
        exit 1
    fi

    local tmp
    tmp="$(mktemp -d)"
    trap 'rm -rf "$tmp"' EXIT
    local tarball="$tmp/superpowers-v$version.tar.gz"

    echo "Verifying vendored Superpowers v$version"
    echo "  URL: $url"

    if ! curl -fsSL "$url" -o "$tarball"; then
        echo "Download failed for $url" >&2
        exit 2
    fi

    local actual_sha
    actual_sha="$(compute_sha256 "$tarball")"
    if [[ "$actual_sha" != "$expected_sha" ]]; then
        echo "MISMATCH" >&2
        echo "  expected: $expected_sha" >&2
        echo "  actual:   $actual_sha" >&2
        exit 3
    fi

    echo "OK — upstream tarball SHA256 matches manifest for v$version"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

```bash
chmod +x plugins/superpowers/scripts/verify-vendor.sh
```

- [ ] **Step 10.4: Run, verify it passes**

```bash
plugins/superpowers/scripts/tests/test-verify-vendor.sh
```
Expected: `PASS: test-verify-vendor` (network-dependent, ~5s).

- [ ] **Step 10.5: Run all tests**

Expected: 8/8 passed.

- [ ] **Step 10.6: Commit**

```bash
git add plugins/superpowers/scripts/verify-vendor.sh plugins/superpowers/scripts/tests/test-verify-vendor.sh
git commit -m "feat(verify): add verify-vendor.sh to check vendored SHA256 against upstream"
```

---

## Task 11: start-overlay.sh helper

**Files:**
- Create: `plugins/superpowers/scripts/start-overlay.sh`
- Create: `plugins/superpowers/scripts/tests/test-start-overlay.sh`

- [ ] **Step 11.1: Write failing test**

Create `plugins/superpowers/scripts/tests/test-start-overlay.sh`:

```bash
#!/usr/bin/env bash
# start-overlay.sh copies a live skill into overlay/ and creates .overlay-meta.json.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helper.sh"

START="$SCRIPT_DIR/../start-overlay.sh"
PLUGIN_ROOT="$SCRIPT_DIR/../.."
TARGET="skills/brainstorming"

# Backup overlay
backup="$(mktemp -d)"
[[ -e "$PLUGIN_ROOT/overlay/$TARGET" ]] && cp -R "$PLUGIN_ROOT/overlay/$TARGET" "$backup/"
cleanup() {
    rm -rf "$PLUGIN_ROOT/overlay/$TARGET"
    if [[ -e "$backup/$(basename "$TARGET")" ]]; then
        mkdir -p "$PLUGIN_ROOT/overlay/$(dirname "$TARGET")"
        cp -R "$backup/$(basename "$TARGET")" "$PLUGIN_ROOT/overlay/$(dirname "$TARGET")/"
    fi
    rm -rf "$backup"
}
trap cleanup EXIT

# Run helper
"$START" "$TARGET"

# Assertions
assert_dir_exists "$PLUGIN_ROOT/overlay/$TARGET" "overlay dir created"
assert_file_exists "$PLUGIN_ROOT/overlay/$TARGET/SKILL.md" "skill content copied"
assert_file_exists "$PLUGIN_ROOT/overlay/$TARGET/.overlay-meta.json" ".overlay-meta.json created"

base_version="$(jq -r .based_on_upstream_version "$PLUGIN_ROOT/overlay/$TARGET/.overlay-meta.json")"
manifest_version="$(jq -r .version "$PLUGIN_ROOT/.vendor-manifest.json")"
assert_equal "$base_version" "$manifest_version" "meta records current upstream version"

echo "PASS: test-start-overlay"
```

```bash
chmod +x plugins/superpowers/scripts/tests/test-start-overlay.sh
```

- [ ] **Step 11.2: Run, verify it fails**

Expected: FAIL — script doesn't exist.

- [ ] **Step 11.3: Implement `plugins/superpowers/scripts/start-overlay.sh`**

```bash
#!/usr/bin/env bash
# start-overlay.sh — bootstrap a Mor overlay for an existing vendored path.
# Usage: ./start-overlay.sh <relative-path>
# Example: ./start-overlay.sh skills/test-driven-development

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

main() {
    if [[ $# -ne 1 ]]; then
        echo "Usage: start-overlay.sh <relative-path>" >&2
        echo "  e.g. start-overlay.sh skills/test-driven-development" >&2
        exit 2
    fi
    local rel="$1"
    require_commands jq
    local plugin_root
    plugin_root="$(plugin_root)"
    local source="$plugin_root/$rel"
    local target="$plugin_root/overlay/$rel"

    if [[ ! -e "$source" ]]; then
        echo "Source path does not exist: $source" >&2
        exit 1
    fi
    if [[ -e "$target" ]]; then
        echo "Overlay already exists at $target — refusing to overwrite." >&2
        exit 1
    fi

    mkdir -p "$(dirname "$target")"
    cp -R "$source" "$target"

    local manifest="$plugin_root/.vendor-manifest.json"
    local version
    version="$(manifest_get "$manifest" version)"
    local now
    now="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

    cat > "$target/.overlay-meta.json" <<EOF
{
  "overlay_path": "$rel",
  "based_on_upstream_version": "$version",
  "created_at": "$now",
  "note": ""
}
EOF

    echo "✓ Overlay created at $target"
    echo "  Edit files in that directory, then run sync-superpowers.sh to apply."
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

```bash
chmod +x plugins/superpowers/scripts/start-overlay.sh
```

- [ ] **Step 11.4: Run, verify it passes**

```bash
plugins/superpowers/scripts/tests/test-start-overlay.sh
```
Expected: `PASS: test-start-overlay`

- [ ] **Step 11.5: Run all tests**

Expected: 9/9 passed.

- [ ] **Step 11.6: Commit**

```bash
git add plugins/superpowers/scripts/start-overlay.sh plugins/superpowers/scripts/tests/test-start-overlay.sh
git commit -m "feat(overlay): add start-overlay.sh helper to bootstrap a customization"
```

---

## Task 12: Update marketplace.json

**Files:**
- Modify: `claude-plugins/.claude-plugin/marketplace.json`

- [ ] **Step 12.1: Read current `marketplace.json`**

```bash
cat .claude-plugin/marketplace.json
```

It should currently have one plugin entry (`spec`).

- [ ] **Step 12.2: Update `marketplace.json`**

Replace the contents with:

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "mor-duongmh",
  "description": "Mor's Claude Code plugin marketplace — spec-driven workflows + vendored Superpowers.",
  "owner": {
    "name": "duongmh",
    "email": "duongmh@mor.com.vn"
  },
  "plugins": [
    {
      "name": "spec",
      "description": "Mor's spec-driven workflow with superpowers-driven schema. Artifacts are TDD-ready and consumable by Superpowers executing-plans and subagent-driven-development.",
      "source": "./plugins/spec",
      "category": "development",
      "author": { "name": "Mor" },
      "homepage": "https://github.com/mor-duongmh/claude-plugins/tree/main/plugins/spec"
    },
    {
      "name": "superpowers",
      "description": "Mor's vendored fork of obra/superpowers — same skills as upstream, pinned and synced via script. Replaces upstream superpowers@obra in this marketplace.",
      "source": "./plugins/superpowers",
      "category": "development",
      "author": {
        "name": "Jesse Vincent (upstream) / Mor (vendoring)",
        "email": "duongmh@mor.com.vn"
      },
      "homepage": "https://github.com/mor-duongmh/claude-plugins/tree/main/plugins/superpowers"
    }
  ]
}
```

- [ ] **Step 12.3: Validate JSON**

```bash
jq . .claude-plugin/marketplace.json > /dev/null && echo "JSON OK"
```
Expected: `JSON OK`

- [ ] **Step 12.4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat(marketplace): list superpowers as second plugin"
```

---

## Task 13: Update top-level README

**Files:**
- Modify: `README.md`

- [ ] **Step 13.1: Replace `README.md`**

Open `README.md` and replace its content with:

```markdown
# Mor Claude Plugins

> Marketplace plugin Claude Code của Mor — spec-driven, TDD-first, vendored Superpowers.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Cài đặt

Yêu cầu: [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) + Node.js ≥ 18.

```
/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install spec@mor-duongmh
/plugin install superpowers@mor-duongmh
```

> `superpowers@mor-duongmh` là bản vendored fork của [obra/superpowers](https://github.com/obra/superpowers). Cùng plugin name → không cài đồng thời với upstream.

## Plugins

| Plugin | Mục đích |
|--------|----------|
| [`spec`](./plugins/spec) | Spec-driven workflow trên OpenSpec với schema `superpowers-driven`. Artifacts plug thẳng vào Superpowers. |
| [`superpowers`](./plugins/superpowers) | Vendored fork của obra/superpowers, sync qua script. Mor customizations qua `overlay/`. |

## Slash commands

| Command | Plugin | Mục đích |
|---------|--------|----------|
| `/spec:setup [path]` | spec | Cài schema vào project |
| `/spec:explore` | spec | Suy nghĩ trước khi implement |
| `/spec:propose [desc]` | spec | Sinh proposal + design + tasks (TDD) |
| `/spec:apply [name]` | spec | Native runner thực thi tasks |
| `/spec:archive [name]` | spec | Đóng change sau merge |
| `/superpowers:brainstorm` | superpowers | Brainstorming skill |
| `/superpowers:write-plan` | superpowers | Writing-plans skill |
| `/superpowers:execute-plan` | superpowers | Executing-plans skill |

Workflow điển hình: `/spec:propose` → `tasks.md` ready-for-Superpowers → `/superpowers:execute-plan` (hoặc `subagent-driven-development`).

## Schema `superpowers-driven` khác default ở 3 chỗ

1. `design.md` bắt buộc section **`## Tech Stack`**.
2. `tasks.md` mở đầu bằng **Superpowers header** + chú thích `REQUIRED SUB-SKILL`.
3. Mỗi task group có **Files block** + **5 bước TDD bắt buộc**.

## Auto-suggestion

Project có `openspec/` nhưng chưa cài schema → plugin gợi ý `/spec:setup` ở đầu session. Tắt vĩnh viễn:

```bash
touch openspec/.spec-setup-skip
```

## Sync upstream Superpowers

```bash
cd plugins/superpowers
./scripts/sync-superpowers.sh                    # use pinned version
./scripts/sync-superpowers.sh 5.1.0              # bump
./scripts/sync-superpowers.sh --dry-run 5.1.0    # preview
./scripts/verify-vendor.sh                       # check sha256 still matches
```

Customization → đọc [plugins/superpowers/overlay/README.md](plugins/superpowers/overlay/README.md).

## Troubleshooting

- **Commands hiện `/mor-openspec:*` thay vì `/spec:*`** → `/plugin update spec@mor-duongmh`.
- **`schema validate` báo lỗi** → xóa `openspec/schemas/superpowers-driven/` và chạy lại `/spec:setup`.
- **Đã cài upstream `superpowers@obra` trước đó** → `/plugin uninstall superpowers@obra` rồi cài lại Mor's bản.

## License

[MIT](LICENSE) © Mor. See [plugins/superpowers/ATTRIBUTION.md](plugins/superpowers/ATTRIBUTION.md) for upstream attribution.
```

- [ ] **Step 13.2: Verify rendering (manual)**

Open the file in a markdown previewer or VS Code. Verify:
- 3-command install block appears.
- 2-plugin table is correct.
- All slash commands listed.
- Sync section + troubleshooting present.

- [ ] **Step 13.3: Commit**

```bash
git add README.md
git commit -m "docs(readme): announce 2-plugin marketplace and 3-command install"
```

---

## Task 14: Update root `.gitignore`

**Files:**
- Modify: `.gitignore` (or create at root if absent)

- [ ] **Step 14.1: Inspect existing `.gitignore`**

```bash
cat .gitignore 2>/dev/null || echo "(no root .gitignore)"
```

- [ ] **Step 14.2: Append `.preview/` if missing**

Either create or extend `.gitignore` so it includes:

```
.preview/
```

(`.preview/` was created earlier in this branch's predecessor work for README rendering; should not be tracked.)

- [ ] **Step 14.3: Commit**

```bash
git add .gitignore
git commit -m "chore(gitignore): exclude .preview/ render artifacts"
```

---

## Task 15: Manual smoke test checklist (no automation)

This is a final validation that the plan worked end-to-end. Each item below should be ticked manually before opening the PR.

- [ ] **Step 15.1: Tests all green locally**

```bash
plugins/superpowers/scripts/tests/run-all.sh
```
Expected: 9/9 passed.

- [ ] **Step 15.2: `marketplace.json` parses & lists 2 plugins**

```bash
jq '.plugins | length' .claude-plugin/marketplace.json
```
Expected: `2`

- [ ] **Step 15.3: Install both plugins on a Claude Code session**

In a fresh Claude Code session (or use `/plugin add marketplace` against a local path / branch):

```
/plugin add marketplace github:mor-duongmh/claude-plugins
/plugin install spec@mor-duongmh
/plugin install superpowers@mor-duongmh
```

Verify no errors during install.

- [ ] **Step 15.4: Skill resolution check**

In the same session, ask Claude:

> List all skills with namespace `superpowers:`.

Expect at least these 14: `brainstorming`, `executing-plans`, `writing-plans`, `subagent-driven-development`, `systematic-debugging`, `test-driven-development`, `verification-before-completion`, `using-superpowers`, `using-git-worktrees`, `requesting-code-review`, `receiving-code-review`, `writing-skills`, `dispatching-parallel-agents`, `finishing-a-development-branch`.

Also verify `/superpowers:brainstorm`, `/superpowers:write-plan`, `/superpowers:execute-plan` are available as slash commands.

- [ ] **Step 15.5: Cross-reference resolution check**

In the same session, invoke:

```
Skill superpowers:executing-plans
```

Read the loaded skill content. Verify references like `superpowers:finishing-a-development-branch` and `superpowers:subagent-driven-development` are present and resolve to skills in the same plugin (no broken references).

- [ ] **Step 15.6: End-to-end with `spec` plugin**

In a project that has `openspec/`:

```
/spec:propose "add a hello world endpoint"
```

Step through prompts. After artifacts are generated, the propose skill should ask via AskUserQuestion which implementation path. Pick `/superpowers:subagent-driven-development` and verify the command resolves.

- [ ] **Step 15.7: All commits push cleanly**

```bash
git log --oneline origin/main..HEAD
```
Expected: a series of commits from Tasks 1–14.

```bash
git push -u origin feat/add-superpowers-plugin
```
Expected: branch pushed.

- [ ] **Step 15.8: Open PR**

```bash
gh pr create --title "Add vendored superpowers plugin alongside spec" --body "$(cat <<'EOF'
## Summary

Adds a second plugin `superpowers@mor-duongmh` to the marketplace — a vendored fork of [obra/superpowers](https://github.com/obra/superpowers) at v5.0.7. Plugin name matches upstream so the 34 internal `superpowers:*` cross-references stay intact.

## What's included

- `plugins/superpowers/` with vendored skills/commands/agents from upstream v5.0.7
- `scripts/sync-superpowers.sh` — refresh from upstream tarball, SHA256-verified, idempotent, with `--dry-run`
- `scripts/verify-vendor.sh` — check vendored SHA256 still matches upstream
- `scripts/start-overlay.sh` — bootstrap a Mor customization
- `overlay/` infrastructure (empty today — replace-mode, drift detection deferred to v2)
- `marketplace.json` updated to list 2 plugins
- Top-level README updated with 3-command install flow

## Spec & plan

- [Spec](docs/superpowers/specs/2026-05-03-vendor-superpowers-plugin-design.md)
- [Plan](docs/morkit/plans/2026-05-03-vendor-superpowers-plugin.md)

## Test plan

- [x] All bash tests pass (`plugins/superpowers/scripts/tests/run-all.sh` → 9/9)
- [x] `marketplace.json` parses and lists 2 plugins
- [x] Install both plugins on a fresh Claude Code session
- [x] All 14 `superpowers:*` skills resolve
- [x] Skill cross-references intact (manually inspected `executing-plans`)
- [x] `/spec:propose` end-to-end → can hand off to `/superpowers:subagent-driven-development`

## Trade-offs

- Mor's `superpowers@mor-duongmh` cannot coexist with upstream `superpowers@obra` (same plugin name). Drop-in replacement only.
- Replace-mode overlay only at v1; append-mode and drift detection deferred.
- 3-command install (no auto-install policy).
EOF
)"
```

---

## Self-review checklist

After completing all tasks, run this self-review against the spec:

- [ ] **Spec coverage:** every spec section maps to a task. Section 4 "Sync script" → Tasks 3–7. Section 5 "Overlay" → Task 9 + Task 11. Section 6 "Attribution" → Task 1.3 + 1.4. Section 7 "Testing" tests 1–8 → Tasks 4–11. Section 8 "Migration" → all tasks in order. Section 9 "Rollout" → Tasks 12–15.
- [ ] **No placeholders:** no "TBD", "TODO", "implement later" in any task.
- [ ] **Type/path consistency:** function names (`parse_args`, `resolve_version`, `apply_overlay`, ...) and file paths (`plugins/superpowers/scripts/...`) consistent across tasks.
- [ ] **Each step is bite-sized:** no step combines write+test+commit; each is one action.
- [ ] **Test code complete:** every test step has the actual test code, not "write a test for X".

---

## Out of scope (explicitly deferred)

- CI workflow that runs `verify-vendor.sh` on every PR.
- Append-mode overlay (concatenate vs replace).
- Automatic drift detection when syncing upstream.
- Plugin signing.
- Auto-install policy in marketplace (`installation: "AUTO"`).

These are tracked in spec Section 10 and can be brainstormed as separate cycles when needed.
