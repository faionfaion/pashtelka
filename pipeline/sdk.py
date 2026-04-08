"""Claude Code SDK wrapper: structured_query() + agent_query().

Synchronous. Calls `claude` CLI directly via subprocess to avoid
nested event loop issues when running inside Claude Code session.
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import subprocess
import time
from pathlib import Path

from pipeline.config import RETRY_BASE_DELAY, RETRY_MAX_ATTEMPTS, RETRY_MAX_DELAY
from pipeline.json_repair import safe_parse_json

logger = logging.getLogger(__name__)

_RETRYABLE_CODES = (429, 500, 502, 503)
_NON_RETRYABLE_CODES = (400, 401, 403)
_RETRYABLE_TEXT = ("timeout", "overloaded", "rate limit", "etimedout", "econnreset")
_NON_RETRYABLE_TEXT = ("invalid_api_key", "authentication")


def _has_code(text: str, code: int) -> bool:
    return bool(re.search(rf'\b{code}\b', text))


def _is_retryable(error_text: str) -> bool:
    lower = error_text.lower()
    if any(_has_code(lower, c) for c in _NON_RETRYABLE_CODES):
        return False
    if any(p in lower for p in _NON_RETRYABLE_TEXT):
        return False
    if any(_has_code(lower, c) for c in _RETRYABLE_CODES):
        return True
    return any(p in lower for p in _RETRYABLE_TEXT)


def _backoff_delay(attempt: int) -> float:
    delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
    jitter = random.uniform(0, delay * 0.5)
    return delay + jitter


def _call_claude(
    prompt: str,
    system_prompt: str | None = None,
    model: str = "opus",
    allowed_tools: list[str] | None = None,
    cwd: str | None = None,
    timeout: int = 900,
) -> str:
    cmd = ["claude", "--print", "--model", model]

    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    if allowed_tools:
        for tool in allowed_tools:
            cmd.extend(["--allowedTools", tool])
    else:
        cmd.extend(["--allowedTools", ""])

    cmd.extend(["--permission-mode", "bypassPermissions"])
    cmd.extend(["-p", prompt])

    env = {k: v for k, v in os.environ.items()
           if not k.startswith("CLAUDE") and k != "CLAUDECODE"}
    env["PATH"] = os.environ.get("PATH", "/usr/bin:/usr/local/bin")
    env["HOME"] = os.environ.get("HOME", str(Path.home()))

    work_dir = cwd or str(Path(__file__).resolve().parent.parent)
    last_error: Exception | None = None

    for attempt in range(RETRY_MAX_ATTEMPTS):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                cwd=work_dir,
                env=env,
                timeout=timeout,
            )

            if result.returncode == 0:
                return result.stdout.strip()

            stderr = result.stderr[:500]
            if not _is_retryable(stderr):
                logger.error("claude CLI failed (non-retryable): %s", stderr[:300])
                raise RuntimeError(
                    f"claude CLI non-retryable error (exit {result.returncode}): {stderr[:300]}"
                )

            last_error = RuntimeError(
                f"claude CLI exit {result.returncode}: {stderr[:200]}"
            )

        except subprocess.TimeoutExpired as e:
            last_error = e

        if attempt < RETRY_MAX_ATTEMPTS - 1:
            delay = _backoff_delay(attempt)
            logger.warning(
                "SDK retry %d/%d after %s — backoff %.1fs",
                attempt + 1, RETRY_MAX_ATTEMPTS - 1,
                type(last_error).__name__, delay,
            )
            time.sleep(delay)
        else:
            logger.error("SDK call failed after %d attempts: %s",
                         RETRY_MAX_ATTEMPTS, last_error)
            raise last_error  # type: ignore[misc]

    raise RuntimeError("SDK retry exhausted")


def structured_query(
    prompt: str,
    system_prompt: str,
    schema: dict,
    model: str = "opus",
    timeout: int = 900,
) -> dict:
    """LLM call expecting structured JSON output."""
    schema_json = json.dumps(schema, indent=2)
    full_prompt = (
        f"{prompt}\n\n"
        f"Output ONLY valid JSON matching this schema. No markdown fences. No explanation.\n"
        f"Schema:\n{schema_json}"
    )
    full_system = f"{system_prompt}\n\nYou MUST output ONLY valid JSON. No markdown fences."

    text = _call_claude(
        prompt=full_prompt,
        system_prompt=full_system,
        model=model,
        allowed_tools=[],
        timeout=timeout,
    )

    return safe_parse_json(text, context="structured_query")


def agent_query(
    prompt: str,
    system_prompt: str,
    model: str = "opus",
    cwd: str | None = None,
    allowed_tools: list[str] | None = None,
    timeout: int = 900,
) -> str:
    """LLM call with tool access, returns text."""
    return _call_claude(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        allowed_tools=allowed_tools,
        cwd=cwd,
        timeout=timeout,
    )
