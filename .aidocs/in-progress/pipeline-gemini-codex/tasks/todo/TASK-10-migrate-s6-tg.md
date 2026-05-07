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
