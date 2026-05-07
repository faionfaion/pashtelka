# TASK-03 — Implement `codex_generate`

**Subject:** Replace the stub with a real `codex exec` shell-out. Concatenates `(system, prompt)`, writes schema to a temp file, runs Codex non-interactively, captures the last message, parses JSON via `safe_parse_json`, validates against the schema, retries on transient errors.

**Files touched:**
- `pipeline/llm.py` (edit)

**Implementation:**

```python
import json
import subprocess
import tempfile
from pathlib import Path

import jsonschema  # already installed via transitive deps; declare in requirements

from pipeline.json_repair import safe_parse_json


def codex_generate(
    prompt: str,
    *,
    system: str = "",
    schema: dict,
    model: str | None = None,
    timeout: int = CODEX_TIMEOUT,
) -> dict:
    """Run Codex CLI in non-interactive JSON mode. Validate + return dict."""
    model = model or CODEX_MODEL

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
                "-m", model,
                "--output-schema", str(schema_path),
                "--output-last-message", str(out_path),
                "--skip-git-repo-check",
                "--sandbox", "read-only",
                "--ephemeral",
                "--color", "never",
                "-",  # prompt on stdin
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
            except subprocess.TimeoutExpired as e:
                last_error = TimeoutError(f"codex exec timed out after {timeout}s")
                if not _retry_or_raise(attempt, last_error):
                    continue
                raise last_error
            except FileNotFoundError as e:
                # Hard error: codex not installed
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

            try:
                raw = out_path.read_text(encoding="utf-8")
            except FileNotFoundError:
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
                return data
            except jsonschema.ValidationError as e:
                # Schema failure is non-retryable — prompt or schema is wrong.
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


def _sleep_backoff(attempt: int, label: str, err: Exception) -> None:
    delay = _backoff_delay(attempt)
    logger.warning(
        "%s retry %d/%d: %s — sleeping %.1fs",
        label, attempt + 1, RETRY_MAX_ATTEMPTS - 1, str(err)[:120], delay,
    )
    time.sleep(delay)


def _retry_or_raise(attempt: int, err: Exception) -> bool:
    """Return True if caller should `continue` to retry."""
    if attempt < RETRY_MAX_ATTEMPTS - 1 and _is_retryable(err):
        _sleep_backoff(attempt, "codex_generate", err)
        return True
    return False
```

Also add `jsonschema>=4.0` to `requirements.txt`.

**Success criterion:**

```bash
python3 -m py_compile pipeline/llm.py
python3 -c "from pipeline.llm import codex_generate; print('ok')"
# Expected: ok
```

The unit test in TASK-12 will cover the subprocess-mocked path. Manual e2e test deferred to bench mode.

**Rollback:** Revert `pipeline/llm.py` to the TASK-02 skeleton. No external callers wired yet.
