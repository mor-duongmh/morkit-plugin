"""Put the skill's flat `scripts/` dir and the shared docs-hero lib on sys.path.

Mirrors how the CLIs resolve their imports at runtime (see task_mapper.py), so a
test never passes on a path layout the real entry points do not have.
"""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
ORCH_SCRIPTS = SKILL_DIR.parent / "docs-hero-orchestrator" / "scripts"

for path in (SKILL_DIR / "scripts", ORCH_SCRIPTS):
    sys.path.insert(0, str(path))
