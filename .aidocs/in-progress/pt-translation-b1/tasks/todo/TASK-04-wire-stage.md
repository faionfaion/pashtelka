# TASK-04 — Wire s_translate_pt into generate mode

**Subject:** Insert `s_translate_pt.run(ctx)` into the per-article
pipeline in `pipeline/modes/generate.py`, between the review loop and
`s6_generate_tg.run(ctx)`.

## Files touched

- `pipeline/modes/generate.py`
- `pipeline/stages/__init__.py` (export new stage if needed)
- `pipeline/run_report.py` (optional — record b1_metrics summary)

## Approach

Single insertion in `_generate_one_article`:

```python
with time_stage(report, f"review:{topic_label[:30]}"):
    _review_loop(ctx)

with time_stage(report, f"translate_pt:{topic_label[:30]}"):
    s_translate_pt.run(ctx)

with time_stage(report, f"tg_caption:{topic_label[:30]}"):
    s6_generate_tg.run(ctx)
```

Add `from pipeline.stages import s_translate_pt` to the imports block.

If `s_translate_pt.run` raises, the per-article try/except already
catches it and skips the article — same as any other stage failure. Log
clearly that PT translation failed but UA can still ship; for now,
failure is hard (we abort the article).

## Success criterion

- `python3 -m pipeline plan -v` exits 0 (no LLM call).
- `python3 -c "from pipeline.modes.generate import run; print('ok')"`.
- `python3 -m py_compile pipeline/modes/generate.py`.
- Existing tests still pass.

## Rollback

`git revert <commit>` — single import + 3 lines.
