# TASK-02 — Create `pipeline/llm.py` skeleton + preflight

**Subject:** Establish the new module with imports, retry helpers, stack accessor, pricing dict, and `preflight_check()`. Functions that do real LLM work are stubs in this task; they get filled in TASK-03/04/05.

**Files touched:**
- `pipeline/llm.py` (NEW)

**Module skeleton:**

```python
"""Pipeline LLM dispatcher: Gemini (search), Codex (generate), Claude (review).

Single integration point for the multi-vendor stack introduced by feature
pipeline-gemini-codex. All migrated stages call this module instead of
pipeline.sdk directly. The LLM_STACK env var (old|new) chooses the backend
per stage; old delegates back to pipeline.sdk.
"""

from __future__ import annotations

import logging
import os
import random
import shutil
import time

from pipeline.config import (
    CLAUDE_MODEL, CODEX_BIN, CODEX_MODEL, CODEX_TIMEOUT,
    GEMINI_MODEL, GEMINI_TIMEOUT, LLM_STACK,
    RETRY_BASE_DELAY, RETRY_MAX_ATTEMPTS, RETRY_MAX_DELAY,
)

logger = logging.getLogger(__name__)

# --- Pricing for AC5 bench (USD per 1M tokens) ---
PRICING = {
    "claude-opus-4-7":  {"in": 15.00, "out": 75.00},
    "gemini-2.5-flash": {"in":  0.30, "out":  2.50},
    "gpt-5.5":          {"in":  1.25, "out": 10.00},
}


def _stack() -> str:
    """Read at call time so tests/bench can override env mid-process."""
    return os.environ.get("LLM_STACK", LLM_STACK).lower().strip() or "old"


def _backoff_delay(attempt: int) -> float:
    delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
    return delay + random.uniform(0, delay * 0.5)


def _is_retryable(error: Exception) -> bool:
    text = str(error).lower()
    if any(p in text for p in ("invalid_api_key", "authentication", "401", "403")):
        return False
    return any(p in text for p in (
        "timeout", "overloaded", "rate limit", "429",
        "500", "502", "503", "504", "resource_exhausted",
    ))


def preflight_check() -> None:
    """Fail fast when LLM_STACK=new and prerequisites are missing.

    No-op when LLM_STACK=old.
    """
    if _stack() != "new":
        return

    missing: list[str] = []

    codex_path = shutil.which(CODEX_BIN)
    if not codex_path:
        missing.append(f"codex CLI on PATH (looked for: {CODEX_BIN!r})")

    if not os.environ.get("GEMINI_API_KEY", "").strip():
        missing.append("GEMINI_API_KEY env var")

    if missing:
        msg = (
            "LLM_STACK=new requires:\n  - "
            + "\n  - ".join(missing)
            + "\nAdd to ~/workspace/.env or unset LLM_STACK to fall back."
        )
        raise RuntimeError(msg)

    logger.info(
        "preflight ok (codex=%s, gemini_key=set, codex_model=%s, gemini_model=%s, claude_model=%s)",
        codex_path, CODEX_MODEL, GEMINI_MODEL, CLAUDE_MODEL,
    )


# Public API stubs filled in TASK-03/04/05.
def gemini_search(prompt: str, *, system: str = "", model: str | None = None,
                  timeout: int = GEMINI_TIMEOUT) -> str:
    raise NotImplementedError("gemini_search lands in TASK-04")


def codex_generate(prompt: str, *, system: str = "", schema: dict,
                   model: str | None = None, timeout: int = CODEX_TIMEOUT) -> dict:
    raise NotImplementedError("codex_generate lands in TASK-03")


def claude_review(prompt: str, *, system: str, schema: dict,
                  model: str = "opus", timeout: int = 900) -> dict:
    raise NotImplementedError("claude_review lands in TASK-05")


def dispatch_research(prompt: str, *, system: str = "",
                      timeout: int = GEMINI_TIMEOUT) -> str:
    raise NotImplementedError("dispatch_research lands in TASK-05")


def dispatch_structured(prompt: str, *, system: str, schema: dict, stage: str,
                        timeout: int = CODEX_TIMEOUT) -> dict:
    raise NotImplementedError("dispatch_structured lands in TASK-05")
```

**Success criterion:**

```bash
# Stack=old: preflight is a no-op
python3 -c "from pipeline.llm import preflight_check; preflight_check(); print('ok')"
# Expected: ok

# Stack=new with no key: preflight raises with clear message
LLM_STACK=new python3 -c "from pipeline.llm import preflight_check; preflight_check()" 2>&1 | head -5
# Expected: RuntimeError: LLM_STACK=new requires: ...
```

```bash
python3 -m py_compile pipeline/llm.py
# Expected: no output, exit 0
```

**Rollback:** `rm pipeline/llm.py`. No callers yet.

## Execution Report

### Status: COMPLETED

### What Was Done
- Created `pipeline/llm.py` with full skeleton: imports, `PRICING` dict, `_stack()`, `_backoff_delay()`, `_is_retryable()`, `_sleep_backoff()`, `preflight_check()`.
- Public-API symbols `gemini_search`, `codex_generate`, `claude_review`, `dispatch_research`, `dispatch_structured` declared as `NotImplementedError` stubs (real bodies in TASK-03..05).

### Files Changed
| File | Change |
|------|--------|
| `pipeline/llm.py` | NEW (~120 lines) |

### Tests
- `python3 -m py_compile pipeline/llm.py` → OK
- `python3 -c "from pipeline.llm import preflight_check; preflight_check()"` → no output, returns None (no-op on `old`).
- `LLM_STACK=new python3 -c "preflight_check()"` → `RuntimeError: LLM_STACK=new requires: ...` (lists missing codex bin path AND `GEMINI_API_KEY`).

### Issues
- None.
