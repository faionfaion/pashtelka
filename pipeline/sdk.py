"""Claude Agent SDK wrapper: structured_query() + agent_query().

Uses claude_agent_sdk with native structured output (output_format + ToolUseBlock).
Synchronous interface — wraps async SDK with asyncio.run().
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, query as sdk_query
from claude_agent_sdk.types import AssistantMessage, ToolUseBlock, TextBlock

from pipeline.config import RETRY_BASE_DELAY, RETRY_MAX_ATTEMPTS, RETRY_MAX_DELAY

logger = logging.getLogger(__name__)

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)


def _backoff_delay(attempt: int) -> float:
    delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
    jitter = random.uniform(0, delay * 0.5)
    return delay + jitter


def _is_retryable(error: Exception) -> bool:
    text = str(error).lower()
    if any(p in text for p in ("invalid_api_key", "authentication", "401", "403")):
        return False
    return any(p in text for p in ("timeout", "overloaded", "rate limit", "429", "500", "502", "503"))


# ---- Structured output (JSON schema) ----

async def _async_structured(
    prompt: str,
    system_prompt: str,
    schema: dict,
    model: str = "opus",
) -> dict:
    """SDK call with native structured output. Returns parsed dict."""
    options = ClaudeAgentOptions(
        model=model,
        system_prompt=system_prompt,
        permission_mode="bypassPermissions",
        allowed_tools=[],
        max_turns=1,
        output_format={"type": "json_schema", "schema": schema},
        cwd=_PROJECT_ROOT,
    )

    result = None
    async for msg in sdk_query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, ToolUseBlock) and block.name == "StructuredOutput":
                    result = block.input

    if result is None:
        raise RuntimeError("No StructuredOutput block in response")
    return result


def structured_query(
    prompt: str,
    system_prompt: str,
    schema: dict,
    model: str = "opus",
    timeout: int = 900,
) -> dict:
    """LLM call with native structured output. Returns validated dict."""
    last_error: Exception | None = None

    for attempt in range(RETRY_MAX_ATTEMPTS):
        try:
            return asyncio.run(
                asyncio.wait_for(
                    _async_structured(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        schema=schema,
                        model=model,
                    ),
                    timeout=timeout,
                )
            )
        except asyncio.TimeoutError:
            last_error = TimeoutError(f"structured_query timed out after {timeout}s")
        except Exception as e:
            if not _is_retryable(e):
                raise
            last_error = e

        if attempt < RETRY_MAX_ATTEMPTS - 1:
            delay = _backoff_delay(attempt)
            logger.warning("structured_query retry %d/%d: %s — %.1fs",
                           attempt + 1, RETRY_MAX_ATTEMPTS - 1, last_error, delay)
            time.sleep(delay)
        else:
            logger.error("structured_query failed after %d attempts: %s", RETRY_MAX_ATTEMPTS, last_error)
            raise last_error  # type: ignore[misc]

    raise RuntimeError("retry exhausted")


# ---- Agent query (free text with tools) ----

async def _async_agent(
    prompt: str,
    system_prompt: str,
    model: str = "opus",
    allowed_tools: list[str] | None = None,
    cwd: str | None = None,
) -> str:
    """SDK call with tool access. Returns concatenated text."""
    options = ClaudeAgentOptions(
        model=model,
        system_prompt=system_prompt,
        permission_mode="bypassPermissions",
        allowed_tools=allowed_tools or [],
        cwd=cwd or _PROJECT_ROOT,
    )

    parts: list[str] = []
    async for msg in sdk_query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    parts.append(block.text)

    return "\n".join(parts).strip()


def agent_query(
    prompt: str,
    system_prompt: str,
    model: str = "opus",
    cwd: str | None = None,
    allowed_tools: list[str] | None = None,
    timeout: int = 900,
) -> str:
    """LLM call with tool access, returns text."""
    last_error: Exception | None = None

    for attempt in range(RETRY_MAX_ATTEMPTS):
        try:
            result = asyncio.run(
                asyncio.wait_for(
                    _async_agent(
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
            last_error = RuntimeError("Empty response")

        except asyncio.TimeoutError:
            last_error = TimeoutError(f"agent_query timed out after {timeout}s")
        except Exception as e:
            if not _is_retryable(e):
                raise
            last_error = e

        if attempt < RETRY_MAX_ATTEMPTS - 1:
            delay = _backoff_delay(attempt)
            logger.warning("agent_query retry %d/%d: %s — %.1fs",
                           attempt + 1, RETRY_MAX_ATTEMPTS - 1, last_error, delay)
            time.sleep(delay)
        else:
            logger.error("agent_query failed after %d attempts: %s", RETRY_MAX_ATTEMPTS, last_error)
            raise last_error  # type: ignore[misc]

    raise RuntimeError("retry exhausted")
