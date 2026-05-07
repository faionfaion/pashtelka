# TASK-08 — Migrate `s3_generate.py` to `dispatch_structured`

**Subject:** Replace `pipeline.sdk.structured_query` with `pipeline.llm.dispatch_structured(stage="generate")`. Keep prompt-building, schema loading, and ctx mutation unchanged.

**Files touched:**
- `pipeline/stages/s3_generate.py`

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
    schema=load_schema("generation"),
    model=MODEL_GENERATE,
)
# with:
result = dispatch_structured(
    prompt=prompt,
    system=system,
    schema=load_schema("generation"),
    stage="generate",
)
```

`MODEL_GENERATE` import becomes unused for this stage — keep removing only what's truly unused so other call sites are not affected.

**Success criterion:**

```bash
python3 -m py_compile pipeline/stages/s3_generate.py
python3 -c "from pipeline.stages import s3_generate; print('ok')"

# Existing test suite must remain green for this module
python3 -m pytest tests/test_stages.py -v -k "generate" 2>&1 | tail -10
```

**Rollback:** Revert single-file change.
