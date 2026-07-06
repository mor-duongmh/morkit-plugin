#!/usr/bin/env bash
# release.sh — cắt một release morkit: bump version → tag → pin marketplace.json → push.
#
# Chạy SAU KHI feature PR đã merge vào main (marketplace sha phải trỏ code đã có feature).
# Cơ chế sha-freeze: user /plugin update chỉ nhận bản mới khi marketplace.json ref+sha đổi.
#
#   Usage:  bash plugins/morkit/scripts/release.sh <X.Y.Z>      # vd 1.4.0
#           DRY_RUN=1 bash plugins/morkit/scripts/release.sh 1.4.0   # xem, không push
set -euo pipefail

VERSION="${1:?usage: release.sh <X.Y.Z> (vd 1.4.0)}"
TAG="morkit--v${VERSION}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

# 0. An toàn: phải ở main sạch, đồng bộ remote, tag chưa tồn tại
[ "$(git branch --show-current)" = "main" ] || { echo "✗ phải đứng ở nhánh main"; exit 1; }
git fetch origin --quiet
git pull --ff-only origin main
[ -z "$(git status --porcelain)" ] || { echo "✗ working tree không sạch"; exit 1; }
git rev-parse "$TAG" >/dev/null 2>&1 && { echo "✗ tag $TAG đã tồn tại"; exit 1; }

# 1. Bump plugin.json version → commit (đây là commit được tag & pin)
python3 - "$VERSION" <<'PY'
import re, sys, pathlib
v = sys.argv[1]
p = pathlib.Path("plugins/morkit/.claude-plugin/plugin.json")
p.write_text(re.sub(r'("version":\s*")[0-9.]+(")', rf'\g<1>{v}\g<2>', p.read_text(), count=1))
PY
git add plugins/morkit/.claude-plugin/plugin.json
git commit -q -m "chore(release): morkit v${VERSION}"
RELEASE_SHA="$(git rev-parse HEAD)"

# 2. Tag tại commit release
git tag "$TAG" "$RELEASE_SHA"

# 3. Pin marketplace.json ref+sha = release này (chỉ đổi 2 dòng → diff tối thiểu)
python3 - "$TAG" "$RELEASE_SHA" <<'PY'
import re, sys, pathlib
tag, sha = sys.argv[1], sys.argv[2]
p = pathlib.Path(".claude-plugin/marketplace.json")
t = p.read_text()
t = re.sub(r'("ref":\s*")morkit--v[0-9.]+(")', rf'\g<1>{tag}\g<2>', t)
t = re.sub(r'("sha":\s*")[0-9a-f]{7,40}(")', rf'\g<1>{sha}\g<2>', t)
p.write_text(t)
PY
git add .claude-plugin/marketplace.json
git commit -q -m "chore(release): pin marketplace → morkit v${VERSION} @ ${RELEASE_SHA:0:12}"

# 4. Push main + tag (trừ khi DRY_RUN)
if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "DRY_RUN: KHÔNG push. Local đã có commit bump + tag $TAG. Hoàn tác:"
  echo "  git tag -d $TAG && git reset --hard origin/main"
else
  git push origin main
  git push origin "$TAG"
  echo "✓ Released morkit v${VERSION} @ ${RELEASE_SHA:0:12}. User /plugin update sẽ nhận skill mới."
fi
