# TASK-12 — Unit tests for `pipeline/llm.py`

**Subject:** Add a self-contained pytest module covering preflight, routing, codex command construction (mocked subprocess), gemini body construction (mocked requests), and schema-validation rejection.

**Files touched:**
- `tests/test_llm.py` (NEW)

**Test cases:**

1. `test_preflight_old_noop` — `LLM_STACK` unset → `preflight_check()` returns None.
2. `test_preflight_new_missing_codex` — `LLM_STACK=new`, `CODEX_BIN=/nonexistent/codex` → `RuntimeError` mentions codex.
3. `test_preflight_new_missing_gemini` — codex resolves, no `GEMINI_API_KEY` → `RuntimeError` mentions GEMINI_API_KEY.
4. `test_dispatch_research_old_calls_claude` — monkeypatch `pipeline.llm._claude_research` to a sentinel; assert called when `LLM_STACK=old`.
5. `test_dispatch_research_new_calls_gemini` — set `LLM_STACK=new`, monkeypatch `gemini_search`; assert called.
6. `test_dispatch_structured_review_always_claude` — even with `LLM_STACK=new`, `stage="review"` calls `_claude_structured`.
7. `test_dispatch_structured_generate_new_calls_codex` — `LLM_STACK=new`, monkeypatch `codex_generate`; assert called.
8. `test_dispatch_structured_unknown_stage_raises` — `stage="bogus"` raises `ValueError`.
9. `test_codex_generate_command_shape` — monkeypatch `subprocess.run` with a fake that writes valid JSON to the `--output-last-message` path; assert returned dict matches and command list contains required flags.
10. `test_codex_generate_schema_validation_failure` — fake subprocess writes JSON missing required field; assert raises `jsonschema.ValidationError`.
11. `test_gemini_search_request_shape` — monkeypatch `requests.post` to capture body; assert `tools` contains `google_search`, `system_instruction` present when `system` arg given.
12. `test_gemini_search_429_retries` — fake returns 429 then 200; assert two POST calls made.

**Skeleton:**

```python
"""Unit tests for pipeline.llm dispatcher."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pipeline import llm


# -- preflight --

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
    fake_codex = tmp_path / "codex"; fake_codex.write_text("#!/bin/sh\n"); fake_codex.chmod(0o755)
    monkeypatch.setattr(llm, "CODEX_BIN", str(fake_codex))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        llm.preflight_check()


# -- routing --

def test_dispatch_research_old_calls_claude(monkeypatch):
    monkeypatch.setenv("LLM_STACK", "old")
    called = {}
    monkeypatch.setattr(llm, "_claude_research",
                        lambda prompt, system, timeout: called.setdefault("claude", True) or "x")
    assert llm.dispatch_research("p", system="s") == "x"
    assert called == {"claude": True}


def test_dispatch_research_new_calls_gemini(monkeypatch):
    monkeypatch.setenv("LLM_STACK", "new")
    monkeypatch.setattr(llm, "gemini_search", lambda *a, **kw: "g")
    assert llm.dispatch_research("p", system="s") == "g"


def test_dispatch_structured_review_always_claude(monkeypatch):
    monkeypatch.setenv("LLM_STACK", "new")
    monkeypatch.setattr(llm, "_claude_structured",
                        lambda p, s, sch, timeout: {"approved": True})
    out = llm.dispatch_structured("p", system="s", schema={}, stage="review")
    assert out == {"approved": True}


def test_dispatch_structured_generate_new_calls_codex(monkeypatch):
    monkeypatch.setenv("LLM_STACK", "new")
    monkeypatch.setattr(llm, "codex_generate",
                        lambda p, *, system, schema, timeout: {"k": 1})
    out = llm.dispatch_structured("p", system="s", schema={}, stage="generate")
    assert out == {"k": 1}


def test_dispatch_structured_unknown_stage_raises():
    with pytest.raises(ValueError):
        llm.dispatch_structured("p", system="s", schema={}, stage="bogus")


# -- codex_generate --

def _fake_codex_run(out_path_finder, payload):
    """Return a callable for monkeypatching subprocess.run."""
    def _run(cmd, **kwargs):
        # Find --output-last-message in cmd
        idx = cmd.index("--output-last-message")
        out = Path(cmd[idx + 1])
        out.write_text(json.dumps(payload), encoding="utf-8")
        m = MagicMock(); m.returncode = 0; m.stdout = ""; m.stderr = ""
        return m
    return _run


def test_codex_generate_command_shape(monkeypatch, tmp_path):
    schema = {"type": "object", "properties": {"x": {"type": "integer"}},
              "required": ["x"]}
    monkeypatch.setattr(llm.subprocess, "run", _fake_codex_run(None, {"x": 7}))
    out = llm.codex_generate("hi", system="sys", schema=schema, timeout=10)
    assert out == {"x": 7}


def test_codex_generate_schema_validation_failure(monkeypatch):
    schema = {"type": "object", "required": ["x"]}
    monkeypatch.setattr(llm.subprocess, "run",
                        _fake_codex_run(None, {"y": 1}))  # missing "x"
    import jsonschema
    with pytest.raises(jsonschema.ValidationError):
        llm.codex_generate("hi", schema=schema, timeout=10)


# -- gemini_search --

def test_gemini_search_request_shape(monkeypatch):
    captured: dict = {}

    def fake_post(url, params=None, json=None, timeout=None, headers=None):
        captured["url"] = url
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
    assert "google_search" in {list(t.keys())[0] for t in captured["body"]["tools"]}
    assert captured["body"]["system_instruction"]["parts"][0]["text"] == "sys"


def test_gemini_search_429_retries(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, params=None, json=None, timeout=None, headers=None):
        calls["n"] += 1
        m = MagicMock()
        if calls["n"] == 1:
            m.status_code = 429; m.text = "rate limit"
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
```

**Success criterion:**

```bash
python3 -m pytest tests/test_llm.py -v
# Expected: all tests pass
```

**Rollback:** `rm tests/test_llm.py`. No production code dependency.
