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

import json
import logging
import os
import random
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import jsonschema
import requests

from pipeline.config import (
    CLAUDE_MODEL, CODEX_BIN, CODEX_MODEL, CODEX_TIMEOUT,
    GEMINI_MODEL, GEMINI_TIMEOUT, LLM_STACK,
    RETRY_BASE_DELAY, RETRY_MAX_ATTEMPTS, RETRY_MAX_DELAY,
)
from pipeline.json_repair import safe_parse_json

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

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


def gemini_search(
    prompt: str,
    *,
    system: str = "",
    model: str | None = None,
    timeout: int = GEMINI_TIMEOUT,
) -> str:
    """Run Gemini with google_search grounding. Return concatenated text.

    Raises RuntimeError on missing key, safety-block, or retry exhaustion.
    """
    chosen_model = model or GEMINI_MODEL

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is empty. Set it in ~/workspace/.env"
        )

    body: dict = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 4096,
        },
    }
    if system:
        body["system_instruction"] = {"parts": [{"text": system}]}

    url = GEMINI_ENDPOINT.format(model=chosen_model)

    last_error: Exception | None = None

    for attempt in range(RETRY_MAX_ATTEMPTS):
        try:
            resp = requests.post(
                url,
                params={"key": api_key},
                json=body,
                timeout=timeout,
                headers={"Content-Type": "application/json"},
            )
        except requests.Timeout:
            exc = TimeoutError(f"gemini_search timed out after {timeout}s")
            if attempt < RETRY_MAX_ATTEMPTS - 1:
                last_error = exc
                _sleep_backoff(attempt, "gemini_search", exc)
                continue
            raise exc
        except requests.RequestException as e:
            if _is_retryable(e) and attempt < RETRY_MAX_ATTEMPTS - 1:
                last_error = e
                _sleep_backoff(attempt, "gemini_search", e)
                continue
            raise

        if resp.status_code >= 500 or resp.status_code == 429:
            exc = RuntimeError(
                f"gemini_search HTTP {resp.status_code}: {resp.text[:200]}"
            )
            if attempt < RETRY_MAX_ATTEMPTS - 1:
                last_error = exc
                _sleep_backoff(attempt, "gemini_search", exc)
                continue
            raise exc

        if resp.status_code >= 400:
            raise RuntimeError(
                f"gemini_search HTTP {resp.status_code}: {resp.text[:500]}"
            )

        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            block = data.get("promptFeedback", {}).get("blockReason")
            raise RuntimeError(
                f"gemini_search empty candidates (blockReason={block}): "
                f"{json.dumps(data)[:300]}"
            )

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "\n".join(p.get("text", "") for p in parts if "text" in p).strip()

        if not text:
            exc = RuntimeError("gemini_search returned empty text")
            if attempt < RETRY_MAX_ATTEMPTS - 1:
                last_error = exc
                _sleep_backoff(attempt, "gemini_search", exc)
                continue
            raise exc

        logger.info(
            "gemini_search: model=%s, %d chars, finish=%s",
            chosen_model, len(text),
            candidates[0].get("finishReason", "?"),
        )
        return text

    raise last_error or RuntimeError("gemini_search: retry exhausted")


def codex_generate(
    prompt: str,
    *,
    system: str = "",
    schema: dict,
    model: str | None = None,
    timeout: int = CODEX_TIMEOUT,
) -> dict:
    """Run Codex CLI in non-interactive JSON mode. Validate + return dict.

    Concatenates (system, prompt) into a single instruction blob, writes
    the schema to a temp file, runs `codex exec` with `--output-schema` and
    `--output-last-message`, parses the captured JSON via safe_parse_json,
    validates against the schema. Retries on transient failures.
    """
    chosen_model = model or CODEX_MODEL

    full_prompt = (
        (f"<system>\n{system}\n</system>\n\n" if system else "")
        + f"<task>\n{prompt}\n</task>\n\n"
        + "Output ONLY valid JSON matching the supplied output schema. "
        + "No markdown fences. No explanation. Do not call any tools."
    )

    last_error: Exception | None = None

    for attempt in range(RETRY_MAX_ATTEMPTS):
        with tempfile.TemporaryDirectory(prefix="codex_") as tmpdir:
            schema_path = Path(tmpdir) / "schema.json"
            out_path = Path(tmpdir) / "last.txt"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")

            cmd = [
                CODEX_BIN, "exec",
                "-m", chosen_model,
                "--output-schema", str(schema_path),
                "--output-last-message", str(out_path),
                "--skip-git-repo-check",
                "--sandbox", "read-only",
                "--ephemeral",
                "--color", "never",
                "-",
            ]

            try:
                proc = subprocess.run(
                    cmd,
                    input=full_prompt,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd="/tmp",
                    check=False,
                )
            except subprocess.TimeoutExpired:
                exc = TimeoutError(f"codex exec timed out after {timeout}s")
                if attempt < RETRY_MAX_ATTEMPTS - 1:
                    last_error = exc
                    _sleep_backoff(attempt, "codex_generate", exc)
                    continue
                raise exc
            except FileNotFoundError as e:
                raise RuntimeError(
                    f"codex CLI not found at {CODEX_BIN!r}. "
                    "Install via `npm i -g @openai/codex` or set CODEX_BIN."
                ) from e

            if proc.returncode != 0:
                err_text = (proc.stderr or proc.stdout or "").strip()[:500]
                exc = RuntimeError(f"codex exec rc={proc.returncode}: {err_text}")
                if _is_retryable(exc) and attempt < RETRY_MAX_ATTEMPTS - 1:
                    last_error = exc
                    _sleep_backoff(attempt, "codex_generate", exc)
                    continue
                raise exc

            raw = ""
            if out_path.exists():
                raw = out_path.read_text(encoding="utf-8")
            if not raw.strip():
                raw = (proc.stdout or "").strip()

            if not raw.strip():
                exc = RuntimeError("codex exec returned empty last-message")
                if attempt < RETRY_MAX_ATTEMPTS - 1:
                    last_error = exc
                    _sleep_backoff(attempt, "codex_generate", exc)
                    continue
                raise exc

            try:
                data = safe_parse_json(raw, context="codex_generate")
                jsonschema.validate(instance=data, schema=schema)
                logger.info(
                    "codex_generate: model=%s, %d chars in, %d chars out",
                    chosen_model, len(full_prompt), len(raw),
                )
                return data
            except jsonschema.ValidationError as e:
                logger.error(
                    "codex_generate schema validation failed: path=%s msg=%s raw_head=%s",
                    list(e.absolute_path), e.message, raw[:300],
                )
                raise
            except ValueError as e:
                exc = RuntimeError(f"codex_generate JSON parse failed: {e}")
                if attempt < RETRY_MAX_ATTEMPTS - 1:
                    last_error = exc
                    _sleep_backoff(attempt, "codex_generate", exc)
                    continue
                raise exc

    raise last_error or RuntimeError("codex_generate: retry exhausted")


def claude_review(prompt: str, *, system: str, schema: dict,
                  model: str = "opus", timeout: int = 900) -> dict:
    raise NotImplementedError("claude_review lands in TASK-05")


def dispatch_research(prompt: str, *, system: str = "",
                      timeout: int = GEMINI_TIMEOUT) -> str:
    raise NotImplementedError("dispatch_research lands in TASK-05")


def dispatch_structured(prompt: str, *, system: str, schema: dict, stage: str,
                        timeout: int = CODEX_TIMEOUT) -> dict:
    raise NotImplementedError("dispatch_structured lands in TASK-05")
