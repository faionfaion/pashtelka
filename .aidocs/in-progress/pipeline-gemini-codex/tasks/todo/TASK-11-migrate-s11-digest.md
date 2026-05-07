# TASK-11 — Migrate `s11_digest.py` to `dispatch_structured`

**Subject:** Swap to dispatcher, `stage="digest"`. Note: spec Open Question reserves the right to revisit (Codex vs Opus for digest creativity); default is Codex per spec.

**Files touched:**
- `pipeline/stages/s11_digest.py`

**Patch shape:**

```python
# replace:
from pipeline.sdk import structured_query
# with:
from pipeline.llm import dispatch_structured
```

```python
# replace:
return structured_query(
    prompt=prompt,
    system_prompt=system,
    schema=load_schema("digest"),
    model=MODEL_TG,
)
# with:
return dispatch_structured(
    prompt=prompt,
    system=system,
    schema=load_schema("digest"),
    stage="digest",
)
```

**Success criterion:**

```bash
python3 -m py_compile pipeline/stages/s11_digest.py
python3 -c "from pipeline.stages import s11_digest; print('ok')"
```

**Rollback:** Revert single-file change.
