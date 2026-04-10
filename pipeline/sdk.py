"""Claude Code Agent SDK wrapper: structured_query() + agent_query().

Uses claude_code_sdk (Python Agent SDK) instead of CLI subprocess.
Synchronous interface — wraps async SDK with asyncio.run().
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from pathlib import Path

from claude_code_sdk import ClaudeCodeOptions, TextBlock, query

from pipeline.config import RETRY_BASE_DELAY, RETRY_MAX_ATTEMPTS, RETRY_MAX_DELAY
from pipeline.json_repair import safe_parse_json

logger = logging.getLogger(__name__)

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)


def _backoff_delay(attempt: int) -> float:
    delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
    jitter = random.uniform(0, delay * 0.5)
    return delay + jitter


async def _async_query(
    prompt: str,
    system_prompt: str | None = None,
    model: str = "opus",
    allowed_tools: list[str] | None = None,
    cwd: str | None = None,
) -> str:
    """Single async SDK call. Returns concatenated text output."""
    options = ClaudeCodeOptions(
        model=model,
        system_prompt=system_prompt or "",
        permission_mode="bypassPermissions",
        allowed_tools=allowed_tools or [],
        cwd=cwd or _PROJECT_ROOT,
    )

    text_parts: list[str] = []
    async for msg in query(prompt=prompt, options=options):
        if hasattr(msg, "content"):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    text_parts.append(block.text)

    return "\n".join(text_parts).strip()


def _call_sdk(
    prompt: str,
    system_prompt: str | None = None,
    model: str = "opus",
    allowed_tools: list[str] | None = None,
    cwd: str | None = None,
    timeout: int = 900,
) -> str:
    """Synchronous wrapper with retry logic."""
    last_error: Exception | None = None

    for attempt in range(RETRY_MAX_ATTEMPTS):
        try:
            result = asyncio.run(
                asyncio.wait_for(
                    _async_query(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        model=model,
                        allowed_tools=allowed_tools,
                        cwd=cwd,
                    ),
                    timeout=timeout,
                )
            )
            if result:
                return result
            last_error = RuntimeError("Empty response from SDK")

        except asyncio.TimeoutError:
            last_error = TimeoutError(f"SDK call timed out after {timeout}s")
        except Exception as e:
            error_text = str(e).lower()
            # Non-retryable errors
            if any(p in error_text for p in ("invalid_api_key", "authentication", "401", "403")):
                logger.error("SDK non-retryable error: %s", str(e)[:300])
                raise
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
            logger.error("SDK call failed after %d attempts: %s", RETRY_MAX_ATTEMPTS, last_error)
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

    text = _call_sdk(
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
    return _call_sdk(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        allowed_tools=allowed_tools,
        cwd=cwd,
        timeout=timeout,
    )
