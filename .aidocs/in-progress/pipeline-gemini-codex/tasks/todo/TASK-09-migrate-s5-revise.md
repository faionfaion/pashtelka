# TASK-09 — Migrate `s5_revise.py` to `dispatch_structured`

**Subject:** Swap to dispatcher, `stage="revise"`.

**Files touched:**
- `pipeline/stages/s5_revise.py`

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
    schema=load_schema("revision"),
    model=MODEL_GENERATE,
)
# with:
result = dispatch_structured(
    prompt=prompt,
    system=system,
    schema=load_schema("revision"),
    stage="revise",
)
```

**Success criterion:**

```bash
python3 -m py_compile pipeline/stages/s5_revise.py
python3 -c "from pipeline.stages import s5_revise; print('ok')"
```

**Rollback:** Revert single-file change.
