# TASK-10 — Migrate `s6_generate_tg.py` to `dispatch_structured`

**Subject:** Swap to dispatcher, `stage="tg"`.

**Files touched:**
- `pipeline/stages/s6_generate_tg.py`

**Patch shape:**

```python
# replace:
from pipeline.sdk import structured_query
# with:
from pipeline.llm import dispatch_structured
```

```python
# replace:
result = structured_query(
    prompt=prompt,
    system_prompt=system,
    schema=load_schema("tg_post"),
    model=MODEL_TG,
)
# with:
result = dispatch_structured(
    prompt=prompt,
    system=system,
    schema=load_schema("tg_post"),
    stage="tg",
)
```

**Success criterion:**

```bash
python3 -m py_compile pipeline/stages/s6_generate_tg.py
python3 -c "from pipeline.stages import s6_generate_tg; print('ok')"
```

**Rollback:** Revert single-file change.

## Execution Report

### Status: COMPLETED

### What Was Done
- Replaced `structured_query(model=MODEL_TG, ...)` with `dispatch_structured(stage="tg", ...)`. Dropped `MODEL_TG` import (was only used here for this stage).
- `MAX_TG_CAPTION` was already imported-but-unused in the original file; left as-is (out of scope for this task).

### Files Changed
| File | Change |
|------|--------|
| `pipeline/stages/s6_generate_tg.py` | -3 / +3 lines (net 0) |

### Tests
- `python3 -m py_compile pipeline/stages/s6_generate_tg.py` → OK
- Module imports cleanly.

### Issues
- None.
