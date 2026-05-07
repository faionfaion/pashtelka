# TASK-04 — Implement `gemini_search`

**Subject:** REST POST to `generativelanguage.googleapis.com` with `google_search` grounding tool, retry on transient errors, return concatenated text.

**Files touched:**
- `pipeline/llm.py` (edit)

**Implementation:**

```python
import requests

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
    """Run Gemini with google_search grounding. Return concatenated text."""
    model = model or GEMINI_MODEL

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

    url = GEMINI_ENDPOINT.format(model=model)

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
        except requests.Timeout as e:
            last_error = TimeoutError(f"gemini_search timed out after {timeout}s")
            if attempt < RETRY_MAX_ATTEMPTS - 1:
                _sleep_backoff(attempt, "gemini_search", last_error)
                continue
            raise last_error
        except requests.RequestException as e:
            last_error = e
            if _is_retryable(e) and attempt < RETRY_MAX_ATTEMPTS - 1:
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
            # 400/401/403 — non-retryable
            raise RuntimeError(
                f"gemini_search HTTP {resp.status_code}: {resp.text[:500]}"
            )

        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            # Safety block or empty response
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
            model, len(text),
            candidates[0].get("finishReason", "?"),
        )
        return text

    raise last_error or RuntimeError("gemini_search: retry exhausted")
```

**Success criterion:**

```bash
python3 -m py_compile pipeline/llm.py
python3 -c "from pipeline.llm import gemini_search; print('ok')"
# Expected: ok

# Failure-fast on missing key
python3 -c "
import os; os.environ.pop('GEMINI_API_KEY', None)
from pipeline.llm import gemini_search
try: gemini_search('test')
except RuntimeError as e: print('OK raised:', str(e)[:60])
"
```

Real-API smoke test deferred (requires key + costs $).

**Rollback:** Re-stub `gemini_search` to `NotImplementedError`. No callers wired yet (TASK-07 wires it).

## Execution Report

### Status: COMPLETED

### What Was Done
- Added `import requests`, `GEMINI_ENDPOINT` constant.
- Filled `gemini_search()` with REST POST to `v1beta/models/{model}:generateContent`, `tools=[{"google_search":{}}]`, optional `system_instruction`, `temperature=0.4`, `maxOutputTokens=4096`.
- Retries on `requests.Timeout`, 429, and 5xx. Raises immediately on 4xx (non-retryable auth/quota).
- Raises explicit error on empty `candidates[]` and exposes `blockReason` from `promptFeedback`.

### Files Changed
| File | Change |
|------|--------|
| `pipeline/llm.py` | +90 lines for `gemini_search` + endpoint constant |

### Tests
- `python3 -m py_compile pipeline/llm.py` → OK
- Symbol import: ok
- Missing-key path: `RuntimeError: GEMINI_API_KEY is empty. Set it in ~/workspace/.env`
- Real API smoke test deferred until `GEMINI_API_KEY` is added by operator.

### Issues
- None.
