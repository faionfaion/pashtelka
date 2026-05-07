# TASK-03 — s_translate_pt stage

**Subject:** Implement the translation stage that calls
`dispatch_translate`, runs the B1 validator, retries once on failure,
and stores PT fields on `PipelineContext`.

## Files touched

- `pipeline/stages/s_translate_pt.py` (new)
- `pipeline/context.py` (add PT fields + `b1_metrics` + `b1_warning`)
- `tests/test_stages.py` (add `TestSTranslatePt`)

## Approach

```python
def run(ctx: PipelineContext) -> None:
    if not ctx.article_text:
        raise RuntimeError("s_translate_pt: ctx.article_text is empty")

    system, prompt = build_translate_pt_prompt(ctx)
    schema = load_schema("translation_pt")

    result = dispatch_translate(prompt, system=system, schema=schema, lang="pt")
    metrics = b1_validate(result["article"])

    if not metrics["passed"]:
        prompt2 = prompt + "\n\n" + metrics["retry_addendum"]
        result = dispatch_translate(prompt2, system=system, schema=schema, lang="pt")
        metrics = b1_validate(result["article"])

    ctx.article_text_pt = result["article"]
    ctx.title_pt        = result["title"]
    ctx.description_pt  = result["description"]
    ctx.summary_pt      = result.get("summary", "")
    ctx.b1_metrics      = metrics
    ctx.b1_warning      = not metrics["passed"]
```

Helper `translate_one_file(path: Path) -> Path` reads a `uk.md` file,
parses frontmatter, runs the stage in standalone mode, writes
`pt.md` next to it. Used by tests + `backfill_pt.py`.

`PipelineContext` extension:
```python
article_text_pt: str = ""
title_pt: str = ""
description_pt: str = ""
summary_pt: str = ""
b1_metrics: dict = field(default_factory=dict)
b1_warning: bool = False
```

## Success criterion

- `python3 -c "from pipeline.stages.s_translate_pt import run; print('ok')"`.
- Unit tests:
  - `test_calls_dispatch_translate` — correct stage args
  - `test_writes_pt_fields` — ctx mutated
  - `test_retries_once_on_b1_failure` — addendum used, second call made
  - `test_b1_warning_on_double_failure` — `ctx.b1_warning=True`, article still set
- All four pass under `pytest tests/test_stages.py::TestSTranslatePt -v`.

## Rollback

`git revert <commit>`. Stage is unwired (TASK-04 wires it); reverting is
safe.
