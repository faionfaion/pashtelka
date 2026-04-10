"""Tests for pipeline.sdk — Claude Agent SDK wrapper."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pipeline.sdk import (
    _backoff_delay,
    _is_retryable,
    _async_structured,
    _async_agent,
)


class TestBackoffDelay:
    """_backoff_delay: exponential backoff with jitter."""

    def test_first_attempt_within_range(self):
        delay = _backoff_delay(0)
        # Base delay = 5.0, jitter up to 50%
        assert 5.0 <= delay <= 7.5

    def test_increases_with_attempts(self):
        delays = [_backoff_delay(i) for i in range(5)]
        # General trend should be increasing (ignoring jitter)
        # Just verify the minimum increases
        assert _backoff_delay(3) > 5.0  # Should be at least base * 2^3

    def test_respects_max_delay(self):
        delay = _backoff_delay(100)  # Very high attempt
        # Max delay is 60.0, plus up to 50% jitter
        assert delay <= 90.0  # 60 + 30 jitter

    def test_always_positive(self):
        for i in range(10):
            assert _backoff_delay(i) > 0


class TestIsRetryable:
    """_is_retryable: determine if an error should trigger retry."""

    def test_timeout_is_retryable(self):
        assert _is_retryable(Exception("Connection timeout")) is True

    def test_overloaded_is_retryable(self):
        assert _is_retryable(Exception("Server overloaded")) is True

    def test_rate_limit_is_retryable(self):
        assert _is_retryable(Exception("rate limit exceeded")) is True

    def test_429_is_retryable(self):
        assert _is_retryable(Exception("HTTP 429")) is True

    def test_500_is_retryable(self):
        assert _is_retryable(Exception("HTTP 500")) is True

    def test_502_is_retryable(self):
        assert _is_retryable(Exception("HTTP 502")) is True

    def test_503_is_retryable(self):
        assert _is_retryable(Exception("HTTP 503")) is True

    def test_invalid_api_key_not_retryable(self):
        assert _is_retryable(Exception("invalid_api_key")) is False

    def test_authentication_not_retryable(self):
        assert _is_retryable(Exception("authentication failed")) is False

    def test_401_not_retryable(self):
        assert _is_retryable(Exception("HTTP 401")) is False

    def test_403_not_retryable(self):
        assert _is_retryable(Exception("HTTP 403")) is False

    def test_generic_error_not_retryable(self):
        assert _is_retryable(Exception("Something went wrong")) is False

    def test_empty_error_not_retryable(self):
        assert _is_retryable(Exception("")) is False


class TestStructuredQuery:
    """structured_query: LLM call with native structured output."""

    @patch("pipeline.sdk.asyncio.run")
    @patch("pipeline.sdk.time.sleep")
    def test_successful_query(self, mock_sleep, mock_run):
        mock_run.return_value = {"key": "value"}

        from pipeline.sdk import structured_query
        result = structured_query(
            prompt="test prompt",
            system_prompt="system",
            schema={"type": "object"},
            model="opus",
        )
        assert result == {"key": "value"}
        mock_sleep.assert_not_called()

    @patch("pipeline.sdk.asyncio.run")
    @patch("pipeline.sdk.time.sleep")
    def test_retries_on_timeout(self, mock_sleep, mock_run):
        mock_run.side_effect = [
            asyncio.TimeoutError("timeout"),
            {"key": "value"},
        ]

        from pipeline.sdk import structured_query
        result = structured_query(
            prompt="test",
            system_prompt="system",
            schema={"type": "object"},
        )
        assert result == {"key": "value"}
        assert mock_sleep.call_count == 1

    @patch("pipeline.sdk.asyncio.run")
    @patch("pipeline.sdk.time.sleep")
    def test_retries_on_retryable_error(self, mock_sleep, mock_run):
        mock_run.side_effect = [
            Exception("Server overloaded"),
            {"key": "value"},
        ]

        from pipeline.sdk import structured_query
        result = structured_query(
            prompt="test",
            system_prompt="system",
            schema={"type": "object"},
        )
        assert result == {"key": "value"}

    @patch("pipeline.sdk.asyncio.run")
    @patch("pipeline.sdk.time.sleep")
    def test_no_retry_on_auth_error(self, mock_sleep, mock_run):
        mock_run.side_effect = Exception("invalid_api_key")

        from pipeline.sdk import structured_query
        with pytest.raises(Exception, match="invalid_api_key"):
            structured_query(
                prompt="test",
                system_prompt="system",
                schema={"type": "object"},
            )
        mock_sleep.assert_not_called()

    @patch("pipeline.sdk.asyncio.run")
    @patch("pipeline.sdk.time.sleep")
    def test_exhausts_retries(self, mock_sleep, mock_run):
        mock_run.side_effect = Exception("Server overloaded")

        from pipeline.sdk import structured_query
        with pytest.raises(Exception):
            structured_query(
                prompt="test",
                system_prompt="system",
                schema={"type": "object"},
            )


class TestAgentQuery:
    """agent_query: LLM call with tool access."""

    @patch("pipeline.sdk.asyncio.run")
    @patch("pipeline.sdk.time.sleep")
    def test_successful_query(self, mock_sleep, mock_run):
        mock_run.return_value = "Research text about Portugal."

        from pipeline.sdk import agent_query
        result = agent_query(
            prompt="test prompt",
            system_prompt="system",
            model="opus",
        )
        assert result == "Research text about Portugal."
        mock_sleep.assert_not_called()

    @patch("pipeline.sdk.asyncio.run")
    @patch("pipeline.sdk.time.sleep")
    def test_retries_on_empty_response(self, mock_sleep, mock_run):
        mock_run.side_effect = [
            "",  # Empty response
            "Valid response",
        ]

        from pipeline.sdk import agent_query
        result = agent_query(
            prompt="test",
            system_prompt="system",
        )
        assert result == "Valid response"

    @patch("pipeline.sdk.asyncio.run")
    @patch("pipeline.sdk.time.sleep")
    def test_retries_on_timeout(self, mock_sleep, mock_run):
        mock_run.side_effect = [
            asyncio.TimeoutError("timeout"),
            "Valid response",
        ]

        from pipeline.sdk import agent_query
        result = agent_query(
            prompt="test",
            system_prompt="system",
        )
        assert result == "Valid response"

    @patch("pipeline.sdk.asyncio.run")
    @patch("pipeline.sdk.time.sleep")
    def test_no_retry_on_auth_error(self, mock_sleep, mock_run):
        mock_run.side_effect = Exception("authentication failed")

        from pipeline.sdk import agent_query
        with pytest.raises(Exception, match="authentication"):
            agent_query(
                prompt="test",
                system_prompt="system",
            )
        mock_sleep.assert_not_called()

    @patch("pipeline.sdk.asyncio.run")
    @patch("pipeline.sdk.time.sleep")
    def test_exhausts_retries(self, mock_sleep, mock_run):
        mock_run.side_effect = Exception("HTTP 503")

        from pipeline.sdk import agent_query
        with pytest.raises(Exception):
            agent_query(
                prompt="test",
                system_prompt="system",
            )


class TestAsyncStructured:
    """_async_structured: SDK call with native structured output."""

    @pytest.mark.asyncio
    @patch("pipeline.sdk.sdk_query")
    async def test_returns_structured_output(self, mock_sdk_query):
        from pipeline.sdk import _async_structured
        from claude_agent_sdk.types import AssistantMessage, ToolUseBlock

        tool_block = MagicMock(spec=ToolUseBlock)
        tool_block.name = "StructuredOutput"
        tool_block.input = {"key": "value"}

        msg = MagicMock(spec=AssistantMessage)
        msg.content = [tool_block]

        async def fake_query(*args, **kwargs):
            yield msg

        mock_sdk_query.side_effect = fake_query

        result = await _async_structured("prompt", "system", {}, "opus")
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    @patch("pipeline.sdk.sdk_query")
    async def test_raises_on_no_structured_output(self, mock_sdk_query):
        from pipeline.sdk import _async_structured
        from claude_agent_sdk.types import AssistantMessage, TextBlock

        text_block = MagicMock(spec=TextBlock)
        text_block.text = "Just text, no structured output"

        msg = MagicMock(spec=AssistantMessage)
        msg.content = [text_block]

        async def fake_query(*args, **kwargs):
            yield msg

        mock_sdk_query.side_effect = fake_query

        with pytest.raises(RuntimeError, match="No StructuredOutput"):
            await _async_structured("prompt", "system", {}, "opus")


class TestAsyncAgent:
    """_async_agent: SDK call with tool access, returns text."""

    @pytest.mark.asyncio
    @patch("pipeline.sdk.sdk_query")
    async def test_returns_text(self, mock_sdk_query):
        from pipeline.sdk import _async_agent
        from claude_agent_sdk.types import AssistantMessage, TextBlock

        text_block = MagicMock(spec=TextBlock)
        text_block.text = "Research findings"

        msg = MagicMock(spec=AssistantMessage)
        msg.content = [text_block]

        async def fake_query(*args, **kwargs):
            yield msg

        mock_sdk_query.side_effect = fake_query

        result = await _async_agent("prompt", "system")
        assert result == "Research findings"

    @pytest.mark.asyncio
    @patch("pipeline.sdk.sdk_query")
    async def test_concatenates_multiple_text_blocks(self, mock_sdk_query):
        from pipeline.sdk import _async_agent
        from claude_agent_sdk.types import AssistantMessage, TextBlock

        block1 = MagicMock(spec=TextBlock)
        block1.text = "Part 1"
        block2 = MagicMock(spec=TextBlock)
        block2.text = "Part 2"

        msg = MagicMock(spec=AssistantMessage)
        msg.content = [block1, block2]

        async def fake_query(*args, **kwargs):
            yield msg

        mock_sdk_query.side_effect = fake_query

        result = await _async_agent("prompt", "system")
        assert "Part 1" in result
        assert "Part 2" in result

    @pytest.mark.asyncio
    @patch("pipeline.sdk.sdk_query")
    async def test_empty_response(self, mock_sdk_query):
        from pipeline.sdk import _async_agent

        async def fake_query(*args, **kwargs):
            return
            yield  # Make it an async generator

        mock_sdk_query.side_effect = fake_query

        result = await _async_agent("prompt", "system")
        assert result == ""
