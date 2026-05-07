"""Pipeline LLM dispatcher: Gemini (search), Codex (generate), Claude (review).

Single integration point for the multi-vendor stack introduced by feature
pipeline-gemini-codex. All migrated stages call this module instead of
pipeline.sdk directly. The LLM_STACK env var (old|new) chooses the backend
per stage; old delegates back to pipeline.sdk.

Public API:
    gemini_search(prompt, *, system, model, timeout) -> str
    codex_generate(prompt, *, system, schema, model, timeout) -> dict
    claude_review(prompt, *, system, schema, model, timeout) -> dict
    preflight_check() -> None
    dispatch_research(prompt, *, system, timeout) -> str
    dispatch_structured(prompt, *, system, schema, stage, timeout) -> dict
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

# --- Pricing for AC5 bench (USD per 1M tokens; rough Q2 2026 reference) ---
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


def _sleep_backoff(attempt: int, label: str, err: Exception) -> None:
    delay = _backoff_delay(attempt)
    logger.warning(
        "%s retry %d/%d: %s — sleeping %.1fs",
        label, attempt + 1, RETRY_MAX_ATTEMPTS - 1, str(err)[:120], delay,
    )
    time.sleep(delay)


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
        "preflight ok (codex=%s, codex_model=%s, gemini_model=%s, claude_model=%s)",
        codex_path, CODEX_MODEL, GEMINI_MODEL, CLAUDE_MODEL,
    )


# Public API stubs — real implementations land in TASK-03/04/05.

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
