# TASK-07 — Migrate `s2_research.py` to `dispatch_research`

**Subject:** Swap `from pipeline.sdk import agent_query` for `from pipeline.llm import dispatch_research`. Keep prompt-building unchanged. The dispatcher routes per `LLM_STACK` so the old behavior is preserved exactly.

**Files touched:**
- `pipeline/stages/s2_research.py`

**Patch shape:**

```python
# replace:
from pipeline.sdk import agent_query
# with:
from pipeline.llm import dispatch_research
```

```python
# replace:
ctx.research_text = agent_query(
    prompt=prompt,
    system_prompt=system,
    model=MODEL_RESEARCH,
    allowed_tools=["WebSearch", "WebFetch", "Read", "Glob"],
    timeout=300,
)
# with:
ctx.research_text = dispatch_research(
    prompt=prompt,
    system=system,
    timeout=300,
)
```

`MODEL_RESEARCH` import becomes unused — drop it. Logging line stays unchanged.

**Success criterion:**

```bash
python3 -m py_compile pipeline/stages/s2_research.py

# Old path still works
LLM_STACK=old python3 -c "
from pipeline.stages import s2_research
print('s2 imports ok')
"

# New path: routing through gemini_search; without GEMINI_API_KEY it should
# raise RuntimeError on the call (NOT at import time).
LLM_STACK=new python3 -c "
from pipeline.stages import s2_research
print('s2 imports ok on new stack')
"
```

`pytest tests/test_stages.py -v` (if it touches s2) must still pass. If it does NOT mock `agent_query`/`dispatch_research`, the migration is import-only and tests should be unaffected.

**Rollback:** Revert this single file. The dispatcher is still present but unused.
