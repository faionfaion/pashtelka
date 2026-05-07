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

from pipeline.config import (
    CLAUDE_MODEL, CODEX_BIN, CODEX_MODEL, CODEX_TIMEOUT,
    GEMINI_BIN, GEMINI_MODEL, GEMINI_TIMEOUT, LLM_STACK,
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


def estimate_tokens(text: str) -> int:
    """Rough char-to-token approximation (~4 chars per token).

    Used by the AC5 bench when the upstream API does not surface a
    structured usage field. Direction-of-delta is what matters; absolute
    numbers are advisory.
    """
    return max(1, len(text) // 4)


def estimate_usd(model: str, in_tokens: int, out_tokens: int) -> float:
    """Convert (in_tokens, out_tokens) to USD using PRICING.

    Returns 0.0 for an unknown model so the bench never crashes on a
    typo; the operator should sanity-check PRICING annually.
    """
    p = PRICING.get(model)
    if not p:
        logger.warning("estimate_usd: no PRICING entry for %r — returning 0.0", model)
        return 0.0
    return (in_tokens / 1e6) * p["in"] + (out_tokens / 1e6) * p["out"]


def stack_models(stack: str) -> dict:
    """Map stack value -> {stage: model_name} for AC5 cost calc."""
    if stack == "new":
        return {
            "research": GEMINI_MODEL,
            "generate": CODEX_MODEL,
            "revise":   CODEX_MODEL,
            "tg":       CODEX_MODEL,
            "review":   CLAUDE_MODEL,
        }
    return {
        "research": CLAUDE_MODEL,
        "generate": CLAUDE_MODEL,
        "revise":   CLAUDE_MODEL,
        "tg":       CLAUDE_MODEL,
        "review":   CLAUDE_MODEL,
    }


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

    gemini_path = shutil.which(GEMINI_BIN)
    if not gemini_path:
        missing.append(f"gemini CLI on PATH (looked for: {GEMINI_BIN!r})")

    if missing:
        msg = (
            "LLM_STACK=new requires:\n  - "
            + "\n  - ".join(missing)
            + "\nInstall the missing CLI(s) or unset LLM_STACK to fall back."
        )
        raise RuntimeError(msg)

    logger.info(
        "preflight ok (codex=%s, gemini=%s, codex_model=%s, gemini_model=%s, claude_model=%s)",
        codex_path, gemini_path, CODEX_MODEL, GEMINI_MODEL, CLAUDE_MODEL,
    )


def gemini_search(
    prompt: str,
    *,
    system: str = "",
    model: str | None = None,
    timeout: int = GEMINI_TIMEOUT,
) -> str:
    """Run the `gemini` CLI in non-interactive headless mode. Return text.

    Shells out to `gemini -p <prompt> -m <model> -o json --approval-mode plan
    --skip-trust`. The CLI manages its own auth chain (cached Google login
    or its own env-var pickup); we do NOT pass any API key from Python.
    `--approval-mode plan` keeps the run read-only (no edits, no file writes
    — we only need the search-grounded response). `--skip-trust` bypasses
    the trusted-folder prompt that otherwise downgrades the approval mode
    in headless contexts.

    `--approval-mode` and `-y/--yolo` are mutually exclusive in CLI
    v0.41.1, so we use `plan` alone.

    The CLI's `-o json` output on stdout is a single object of the shape
    `{"session_id": "...", "response": "<text>", "stats": {...}}`. We
    extract the `response` field. Warnings (terminal capability hints,
    ripgrep fallback notice) go to stderr and are ignored.

    If `system` is provided we prepend it to the prompt — the CLI has no
    separate system field in headless mode.

    Raises RuntimeError on retry exhaustion or empty/garbled output.
    """
    chosen_model = model or GEMINI_MODEL

    full_prompt = (
        f"<system>\n{system}\n</system>\n\n<task>\n{prompt}\n</task>"
        if system
        else prompt
    )

    cmd = [
        GEMINI_BIN,
        "-p", full_prompt,
        "-m", chosen_model,
        "-o", "json",
        "--approval-mode", "plan",
        "--skip-trust",
    ]

    last_error: Exception | None = None

    for attempt in range(RETRY_MAX_ATTEMPTS):
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd="/tmp",
                check=False,
            )
        except subprocess.TimeoutExpired:
            exc = TimeoutError(f"gemini_search timed out after {timeout}s")
            if attempt < RETRY_MAX_ATTEMPTS - 1:
                last_error = exc
                _sleep_backoff(attempt, "gemini_search", exc)
                continue
            raise exc
        except FileNotFoundError as e:
            raise RuntimeError(
                f"gemini CLI not found at {GEMINI_BIN!r}. "
                "Install via `npm i -g @google/gemini-cli` or set GEMINI_BIN."
            ) from e

        if proc.returncode != 0:
            err_text = (proc.stderr or proc.stdout or "").strip()[:500]
            exc = RuntimeError(
                f"gemini exec rc={proc.returncode}: {err_text}"
            )
            if _is_retryable(exc) and attempt < RETRY_MAX_ATTEMPTS - 1:
                last_error = exc
                _sleep_backoff(attempt, "gemini_search", exc)
                continue
            raise exc

        raw = (proc.stdout or "").strip()
        if not raw:
            exc = RuntimeError("gemini_search: empty stdout")
            if attempt < RETRY_MAX_ATTEMPTS - 1:
                last_error = exc
                _sleep_backoff(attempt, "gemini_search", exc)
                continue
            raise exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            exc = RuntimeError(
                f"gemini_search: stdout is not valid JSON: {e}; "
                f"head={raw[:200]!r}"
            )
            if attempt < RETRY_MAX_ATTEMPTS - 1:
                last_error = exc
                _sleep_backoff(attempt, "gemini_search", exc)
                continue
            raise exc

        text = (data.get("response") or "").strip()
        if not text:
            exc = RuntimeError(
                f"gemini_search: empty 'response' field (keys={list(data)})"
            )
            if attempt < RETRY_MAX_ATTEMPTS - 1:
                last_error = exc
                _sleep_backoff(attempt, "gemini_search", exc)
                continue
            raise exc

        # Stats block is best-effort: surface model + latency for ops.
        try:
            mstats = data.get("stats", {}).get("models", {}).get(chosen_model, {})
            api = mstats.get("api", {}) or {}
            tokens = mstats.get("tokens", {}) or {}
            logger.info(
                "gemini_search: model=%s, %d chars, latency_ms=%s, tokens_in=%s, tokens_out=%s",
                chosen_model, len(text),
                api.get("totalLatencyMs", "?"),
                tokens.get("input", "?"), tokens.get("candidates", "?"),
            )
        except Exception:
            logger.info("gemini_search: model=%s, %d chars", chosen_model, len(text))

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


def claude_review(
    prompt: str,
    *,
    system: str,
    schema: dict,
    model: str = "opus",
    timeout: int = 900,
) -> dict:
    """Thin wrapper over pipeline.sdk.structured_query. Used by s4_review."""
    # Local import keeps pipeline.sdk's import-time SDK patch out of the way
    # for code paths that only need codex/gemini.
    from pipeline.sdk import structured_query
    return structured_query(
        prompt=prompt,
        system_prompt=system,
        schema=schema,
        model=model,
        timeout=timeout,
    )


def _claude_structured(prompt: str, system: str, schema: dict, timeout: int) -> dict:
    """Old-stack call for stages that originally used structured_query."""
    from pipeline.sdk import structured_query
    return structured_query(
        prompt=prompt,
        system_prompt=system,
        schema=schema,
        model="opus",
        timeout=timeout,
    )


def _claude_research(prompt: str, system: str, timeout: int) -> str:
    """Old-stack call for s2_research using agent_query + WebSearch tools."""
    from pipeline.sdk import agent_query
    return agent_query(
        prompt=prompt,
        system_prompt=system,
        model="opus",
        allowed_tools=["WebSearch", "WebFetch", "Read", "Glob"],
        timeout=timeout,
    )


def dispatch_research(
    prompt: str,
    *,
    system: str = "",
    timeout: int = GEMINI_TIMEOUT,
) -> str:
    """Stack-aware research call.

    old → Claude agent_query with WebSearch / WebFetch / Read / Glob.
    new → Gemini 2.5 Flash with google_search grounding.
    """
    if _stack() == "new":
        return gemini_search(prompt, system=system, timeout=timeout)
    return _claude_research(prompt, system, timeout)


# Stages that always stay on Claude regardless of LLM_STACK.
_CLAUDE_ONLY_STAGES = {"review", "plan"}

# Stages that flip to Codex on the new stack.
_CODEX_STAGES = {"generate", "revise", "tg", "digest"}


def dispatch_structured(
    prompt: str,
    *,
    system: str,
    schema: dict,
    stage: str,
    timeout: int = CODEX_TIMEOUT,
) -> dict:
    """Stack + stage aware structured-output call.

    Routing:
      - stage in {review, plan}: always Claude (AC3 + s0 not in AC2 list)
      - stage in {generate, revise, tg, digest}:
          new → codex_generate, old → Claude structured_query
    """
    if stage in _CLAUDE_ONLY_STAGES:
        return _claude_structured(prompt, system, schema, timeout=timeout)

    if stage not in _CODEX_STAGES:
        raise ValueError(f"dispatch_structured: unknown stage {stage!r}")

    if _stack() == "new":
        return codex_generate(prompt, system=system, schema=schema, timeout=timeout)

    return _claude_structured(prompt, system, schema, timeout=timeout)


# ---- pt-translation-b1: PT translation routing ----

# Translation slots into the existing dispatch as stage="revise":
# - Same vendor preference (Codex on `new`, Claude on `old`).
# - Same timeout class (long output expected).
# - Reuses the structured-output path with our translation schema.
# A dedicated wrapper keeps the call site readable and gives us a single
# place to tune translation routing later (e.g. cheaper model per locale)
# without touching every call site.

def dispatch_translate(
    prompt: str,
    *,
    system: str,
    schema: dict,
    lang: str,
    timeout: int = CODEX_TIMEOUT,
) -> dict:
    """Stack-aware PT translation call.

    For now, only `lang="pt"` is supported. Routes through
    `dispatch_structured(stage="revise")` to inherit the existing
    LLM_STACK behaviour. A future locale (es/fr/en) can pick a different
    routing path here without changing call sites.
    """
    if lang != "pt":
        raise ValueError(
            f"dispatch_translate: only lang='pt' is supported in v1, got {lang!r}"
        )
    result = dispatch_structured(
        prompt, system=system, schema=schema, stage="revise", timeout=timeout,
    )

    # Soft cost-warn (AC9): no hard ceiling, log only.
    try:
        _maybe_warn_translation_cost(
            in_chars=len(prompt) + len(system),
            out_chars=sum(len(v) for v in result.values() if isinstance(v, str)),
        )
    except Exception:
        # Cost-warn is best-effort and must never fail the call.
        logger.exception("translation cost-warn raised; ignoring")

    return result


def _maybe_warn_translation_cost(*, in_chars: int, out_chars: int) -> None:
    """Log a WARNING when a translation call's estimated USD cost exceeds the
    `TRANSLATION_COST_WARN_USD` threshold from config. Soft guardrail only.
    """
    from pipeline.config import TRANSLATION_COST_WARN_USD

    in_tokens = estimate_tokens("x" * in_chars)
    out_tokens = estimate_tokens("x" * out_chars)
    # Use the dispatcher's stack to pick the dominant model.
    model = stack_models(_stack())["revise"]
    usd = estimate_usd(model, in_tokens, out_tokens)

    if usd > TRANSLATION_COST_WARN_USD:
        logger.warning(
            "translation cost ${%.4f} exceeds threshold ${%.4f} "
            "(model=%s, in_tokens=%d, out_tokens=%d). "
            "Tune TRANSLATION_COST_WARN_USD if this is expected.",
            usd, TRANSLATION_COST_WARN_USD, model, in_tokens, out_tokens,
        )
    else:
        logger.debug(
            "translation cost ${%.4f} within threshold ${%.4f} (model=%s)",
            usd, TRANSLATION_COST_WARN_USD, model,
        )
