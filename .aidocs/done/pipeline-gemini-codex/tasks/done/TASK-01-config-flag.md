# TASK-01 — Config: LLM_STACK flag and per-vendor constants

**Subject:** Extend `pipeline/config.py` with the `LLM_STACK` feature flag, per-vendor model overrides, timeouts, and the `CODEX_BIN` path. Read all from env vars with documented defaults.

**Files touched:**
- `pipeline/config.py` (edit, append-only)

**What to add (append at end of file):**

```python
import os

# ---- LLM stack switch (feature pipeline-gemini-codex) ----
LLM_STACK = os.environ.get("LLM_STACK", "old").lower().strip()

# Per-vendor model overrides
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
CODEX_MODEL = os.environ.get("CODEX_MODEL", "gpt-5.5")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-7")

# Codex CLI binary (allow override; PATH lookup by default)
CODEX_BIN = os.environ.get("CODEX_BIN", "codex")

# Per-vendor timeouts (seconds)
GEMINI_TIMEOUT = int(os.environ.get("GEMINI_TIMEOUT", "300"))
CODEX_TIMEOUT = int(os.environ.get("CODEX_TIMEOUT", "600"))
```

`os` is not yet imported by `config.py`; add the import at the top alongside `from pathlib import Path` (or place a second `import os` at the boundary — Python is fine with a second import, but cleaner to consolidate at top).

**Existing constants are NOT touched.** `MODEL_*` legacy constants stay; they only matter on the `old` stack.

**Success criterion:**

```bash
python3 -c "from pipeline.config import LLM_STACK, GEMINI_MODEL, CODEX_MODEL, CLAUDE_MODEL, CODEX_BIN, GEMINI_TIMEOUT, CODEX_TIMEOUT; print(LLM_STACK, GEMINI_MODEL, CODEX_MODEL)"
# Expected: old gemini-2.5-flash gpt-5.5
```

```bash
LLM_STACK=new GEMINI_MODEL=gemini-2.5-pro python3 -c "from pipeline.config import LLM_STACK, GEMINI_MODEL; print(LLM_STACK, GEMINI_MODEL)"
# Expected: new gemini-2.5-pro
```

**Rollback:** `git revert <commit>` — config-only change, no runtime impact when `LLM_STACK` is unset.

## Execution Report

### Status: COMPLETED

### What Was Done
- Added `import os` at top of `pipeline/config.py`.
- Appended `LLM_STACK`, `GEMINI_MODEL`, `CODEX_MODEL`, `CLAUDE_MODEL`, `CODEX_BIN`, `GEMINI_TIMEOUT`, `CODEX_TIMEOUT` constants — all read from env with documented defaults.
- Did NOT touch existing `MODEL_*` constants (kept for backward compat on `LLM_STACK=old`).

### Files Changed
| File | Change |
|------|--------|
| `pipeline/config.py` | +18 lines (imports + LLM_STACK block) |

### Tests
- `python3 -m py_compile pipeline/config.py` → OK
- Default import: `old gemini-2.5-flash gpt-5.5 codex`
- Override: `LLM_STACK=new GEMINI_MODEL=gemini-2.5-pro` → `new gemini-2.5-pro`

### Issues
- None.
