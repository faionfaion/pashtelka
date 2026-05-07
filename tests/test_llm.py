"""Unit tests for pipeline.llm dispatcher.

Covers:
- preflight_check no-op vs failure paths
- dispatch_research / dispatch_structured routing per LLM_STACK + stage
- codex_generate command shape and schema validation
- gemini_search request shape and 429-retry path
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import jsonschema
import pytest

from pipeline import llm


# ---- preflight ----

def test_preflight_old_noop(monkeypatch):
    monkeypatch.delenv("LLM_STACK", raising=False)
    assert llm.preflight_check() is None


def test_preflight_new_missing_codex(monkeypatch):
    monkeypatch.setenv("LLM_STACK", "new")
    monkeypatch.setattr(llm, "CODEX_BIN", "/no/such/codex")
    monkeypatch.setenv("GEMINI_API_KEY", "anything")
    with pytest.raises(RuntimeError, match="codex"):
        llm.preflight_check()


def test_preflight_new_missing_gemini(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_STACK", "new")
    fake_codex = tmp_path / "codex"
    fake_codex.write_text("#!/bin/sh\n")
    fake_codex.chmod(0o755)
    monkeypatch.setattr(llm, "CODEX_BIN", str(fake_codex))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        llm.preflight_check()


# ---- routing: research ----

def test_dispatch_research_old_calls_claude(monkeypatch):
    monkeypatch.setenv("LLM_STACK", "old")
    called = {}

    def fake_claude(prompt, system, timeout):
        called["claude"] = True
        return "x"

    monkeypatch.setattr(llm, "_claude_research", fake_claude)
    assert llm.dispatch_research("p", system="s") == "x"
    assert called == {"claude": True}


def test_dispatch_research_new_calls_gemini(monkeypatch):
    monkeypatch.setenv("LLM_STACK", "new")
    monkeypatch.setattr(llm, "gemini_search", lambda *a, **kw: "g")
    assert llm.dispatch_research("p", system="s") == "g"


# ---- routing: structured ----

def test_dispatch_structured_review_always_claude(monkeypatch):
    monkeypatch.setenv("LLM_STACK", "new")
    monkeypatch.setattr(
        llm, "_claude_structured",
        lambda p, s, sch, timeout: {"approved": True},
    )
    out = llm.dispatch_structured("p", system="s", schema={}, stage="review")
    assert out == {"approved": True}


def test_dispatch_structured_plan_always_claude(monkeypatch):
    monkeypatch.setenv("LLM_STACK", "new")
    monkeypatch.setattr(
        llm, "_claude_structured",
        lambda p, s, sch, timeout: {"articles": []},
    )
    out = llm.dispatch_structured("p", system="s", schema={}, stage="plan")
    assert out == {"articles": []}


def test_dispatch_structured_generate_new_calls_codex(monkeypatch):
    monkeypatch.setenv("LLM_STACK", "new")
    monkeypatch.setattr(
        llm, "codex_generate",
        lambda p, *, system, schema, timeout: {"k": 1},
    )
    out = llm.dispatch_structured("p", system="s", schema={}, stage="generate")
    assert out == {"k": 1}


def test_dispatch_structured_generate_old_calls_claude(monkeypatch):
    monkeypatch.setenv("LLM_STACK", "old")
    monkeypatch.setattr(
        llm, "_claude_structured",
        lambda p, s, sch, timeout: {"old": True},
    )
    out = llm.dispatch_structured("p", system="s", schema={}, stage="generate")
    assert out == {"old": True}


def test_dispatch_structured_unknown_stage_raises():
    with pytest.raises(ValueError):
        llm.dispatch_structured("p", system="s", schema={}, stage="bogus")


# ---- codex_generate ----

def _fake_codex_run(payload):
    """Return a callable for monkeypatching subprocess.run.

    Writes `payload` (already JSON-serializable) to the path passed via
    --output-last-message and returns a MagicMock with rc=0.
    """
    def _run(cmd, **kwargs):
        idx = cmd.index("--output-last-message")
        out = Path(cmd[idx + 1])
        out.write_text(json.dumps(payload), encoding="utf-8")
        m = MagicMock()
        m.returncode = 0
        m.stdout = ""
        m.stderr = ""
        return m
    return _run


def test_codex_generate_command_shape(monkeypatch):
    schema = {
        "type": "object",
        "properties": {"x": {"type": "integer"}},
        "required": ["x"],
    }
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["input"] = kwargs.get("input")
        idx = cmd.index("--output-last-message")
        Path(cmd[idx + 1]).write_text('{"x": 7}', encoding="utf-8")
        m = MagicMock(); m.returncode = 0; m.stdout = ""; m.stderr = ""
        return m

    monkeypatch.setattr(llm.subprocess, "run", fake_run)
    out = llm.codex_generate("hi", system="sys", schema=schema, timeout=10)
    assert out == {"x": 7}

    cmd = captured["cmd"]
    assert cmd[0] == llm.CODEX_BIN
    assert cmd[1] == "exec"
    assert "-m" in cmd
    assert "--output-schema" in cmd
    assert "--output-last-message" in cmd
    assert "--skip-git-repo-check" in cmd
    assert "--sandbox" in cmd
    assert "--ephemeral" in cmd
    assert cmd[-1] == "-"
    # Stdin contains both the system block and the JSON-only directive.
    assert "<system>" in captured["input"]
    assert "Output ONLY valid JSON" in captured["input"]


def test_codex_generate_schema_validation_failure(monkeypatch):
    schema = {
        "type": "object",
        "properties": {"x": {"type": "integer"}},
        "required": ["x"],
    }
    monkeypatch.setattr(llm.subprocess, "run", _fake_codex_run({"y": 1}))
    with pytest.raises(jsonschema.ValidationError):
        llm.codex_generate("hi", schema=schema, timeout=10)


def test_codex_generate_retries_on_transient(monkeypatch):
    schema = {
        "type": "object",
        "properties": {"x": {"type": "integer"}},
        "required": ["x"],
    }
    calls = {"n": 0}

    def fake_run(cmd, **kwargs):
        calls["n"] += 1
        idx = cmd.index("--output-last-message")
        out = Path(cmd[idx + 1])
        m = MagicMock()
        if calls["n"] == 1:
            m.returncode = 1
            m.stdout = ""
            m.stderr = "rate limit (429)"
            return m
        out.write_text('{"x": 9}', encoding="utf-8")
        m.returncode = 0
        m.stdout = ""
        m.stderr = ""
        return m

    monkeypatch.setattr(llm.subprocess, "run", fake_run)
    monkeypatch.setattr(llm, "_sleep_backoff", lambda *a, **kw: None)
    out = llm.codex_generate("hi", schema=schema, timeout=10)
    assert out == {"x": 9}
    assert calls["n"] == 2


# ---- gemini_search ----

def test_gemini_search_request_shape(monkeypatch):
    captured: dict = {}

    def fake_post(url, params=None, json=None, timeout=None, headers=None):
        captured["url"] = url
        captured["params"] = params
        captured["body"] = json
        m = MagicMock()
        m.status_code = 200
        m.json.return_value = {
            "candidates": [{
                "content": {"parts": [{"text": "answer"}]},
                "finishReason": "STOP",
            }]
        }
        return m

    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setattr(llm.requests, "post", fake_post)
    text = llm.gemini_search("p", system="sys")
    assert text == "answer"
    assert captured["params"] == {"key": "fake"}
    assert "google_search" in captured["body"]["tools"][0]
    assert captured["body"]["system_instruction"]["parts"][0]["text"] == "sys"


def test_gemini_search_429_retries(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, params=None, json=None, timeout=None, headers=None):
        calls["n"] += 1
        m = MagicMock()
        if calls["n"] == 1:
            m.status_code = 429
            m.text = "rate limit"
            return m
        m.status_code = 200
        m.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "ok"}]}}]
        }
        return m

    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setattr(llm.requests, "post", fake_post)
    monkeypatch.setattr(llm, "_sleep_backoff", lambda *a, **kw: None)
    out = llm.gemini_search("p")
    assert out == "ok"
    assert calls["n"] == 2


def test_gemini_search_missing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        llm.gemini_search("p")
