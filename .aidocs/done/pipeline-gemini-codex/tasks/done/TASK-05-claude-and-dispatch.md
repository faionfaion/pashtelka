# TASK-05 — `claude_review` wrapper + dispatch shims

**Subject:** Implement the thin Claude wrapper (delegates to existing `pipeline.sdk.structured_query`) and the two routing shims (`dispatch_research`, `dispatch_structured`). The shims read `_stack()` at call time so bench mode can flip mid-process.

**Files touched:**
- `pipeline/llm.py` (edit)

**Implementation:**

```python
def claude_review(
    prompt: str,
    *,
    system: str,
    schema: dict,
    model: str = "opus",
    timeout: int = 900,
) -> dict:
    """Thin wrapper over pipeline.sdk.structured_query. Used by s4_review."""
    # Local import to avoid pipeline.sdk's import-time SDK patch when LLM_STACK=new
    # paths only need codex/gemini.
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
    """Stack-aware research call. old → Claude+WebSearch. new → Gemini."""
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
```

**Success criterion:**

```bash
python3 -m py_compile pipeline/llm.py
python3 -c "
from pipeline.llm import (
    gemini_search, codex_generate, claude_review,
    preflight_check, dispatch_research, dispatch_structured,
    _stack, _CLAUDE_ONLY_STAGES, _CODEX_STAGES,
)
assert _stack() == 'old'
assert 'review' in _CLAUDE_ONLY_STAGES
assert 'generate' in _CODEX_STAGES
print('ok')
"
# Expected: ok
```

Routing unit tests come in TASK-12.

**Rollback:** Restore stubs from TASK-02. No stage callers wired yet (TASK-07..11 wire them).

## Execution Report

### Status: COMPLETED

### What Was Done
- Implemented `claude_review`, `_claude_structured`, `_claude_research` (all delegate to `pipeline.sdk` via local imports — keeps the SDK import-time patch off the hot path when only the new stack is exercised).
- Implemented `dispatch_research` (`old → _claude_research`, `new → gemini_search`).
- Implemented `dispatch_structured` with stage-aware routing: `{review, plan}` → always Claude; `{generate, revise, tg, digest}` → flips with stack; unknown stage → `ValueError`.
- Exposed `_CLAUDE_ONLY_STAGES` and `_CODEX_STAGES` as module attrs for the unit tests in TASK-12.

### Files Changed
| File | Change |
|------|--------|
| `pipeline/llm.py` | +90 lines for wrappers + dispatch shims |

### Tests
- `python3 -m py_compile pipeline/llm.py` → OK
- All public symbols importable in one statement → ok
- `_stack() == 'old'`, both stage sets correctly populated.

### Issues
- None.
