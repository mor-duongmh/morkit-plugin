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

If any check shows FAIL or MISSING, re-run `/morkit:setup` or report the doctor output.

## Next step

Once doctor passes, offer to start docs generation — call **AskUserQuestion**:
"Setup xong ✅ Chạy `/morkit:init` để tạo bộ docs ngay không?"
- `Có, chạy /morkit:init` → follow the `/morkit:init` flow (it asks greenfield/brownfield + doc types).
- `Để sau` → stop, and remind the user they can run `/morkit:init` anytime.
