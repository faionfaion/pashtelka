# TASK-06 — Wire `preflight_check()` into `pipeline/cli.py`

**Subject:** Call `pipeline.llm.preflight_check()` once at startup, after logging is configured and before mode dispatch. On `RuntimeError`, log the message and exit 2 (config error).

**Files touched:**
- `pipeline/cli.py` (edit)

**Patch shape:**

After the file-logging setup (around line 44, before `try:`), add:

```python
    # Pre-flight: when LLM_STACK=new, verify codex CLI + GEMINI_API_KEY.
    try:
        from pipeline.llm import preflight_check
        preflight_check()
    except RuntimeError as e:
        logger.error("Pre-flight check failed:\n%s", e)
        sys.exit(2)
```

**Success criterion:**

```bash
# Old default — preflight is no-op, plan runs normally
python3 -m pipeline plan -v 2>&1 | head -3
# Expected: pipeline starts; no preflight error

# New + missing key — exit 2 with clear message
LLM_STACK=new python3 -m pipeline plan 2>&1 | tail -5; echo "rc=$?"
# Expected: "Pre-flight check failed:" + listing missing items + rc=2
```

**Rollback:** Remove the inserted block. The pipeline reverts to the previous behavior (no startup check).
