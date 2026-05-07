# TASK-02 — Translation prompt template + schema + dispatcher wrapper

**Subject:** Add the B1 translation prompt template, JSON schema for the
output, and the `dispatch_translate` wrapper in `pipeline/llm.py`. The
wrapper routes through `dispatch_structured(stage="revise")` so the
existing LLM_STACK toggle drives translation too.

## Files touched

- `pipeline/prompts/templates/s_translate_pt.xml.j2` (new)
- `pipeline/prompts/builder.py` (add `build_translate_pt_prompt`)
- `pipeline/schemas/translation_pt.json` (new)
- `pipeline/llm.py` (add `dispatch_translate`)

## Approach

Template encodes the AC4 rules (tenses, sentence length, idioms, proper
nouns, tone, structure). System prompt: short paragraph identifying the
translator role. User prompt: the rules + 2-3 short UA→PT B1 few-shot
examples + the actual UA article body. Use the project's `===SPLIT===`
marker convention.

Schema requires `title`, `description`, `article`; `summary` optional.

`dispatch_translate(prompt, *, system, schema, lang)` is a thin shim:

```python
def dispatch_translate(prompt, *, system, schema, lang):
    if lang != "pt":
        raise ValueError(f"dispatch_translate: only lang='pt' supported, got {lang!r}")
    return dispatch_structured(prompt, system=system, schema=schema, stage="revise")
```

We hard-code `lang="pt"` for v1 — when ES/FR/EN come, a switch goes here.

## Success criterion

- Render: `from pipeline.prompts.builder import build_translate_pt_prompt;
  s, u = build_translate_pt_prompt(ctx_like)` returns non-empty strings,
  both contain "B1" or "simplified Portuguese", "20 words" / "20 palavras",
  "OTAN".
- Schema: `from pipeline.schemas import load_schema;
  load_schema('translation_pt')['required']` includes
  `["title", "description", "article"]`.
- `pipeline/llm.py` exposes `dispatch_translate`. Unit test in
  `tests/test_llm.py::test_dispatch_translate_routes_to_revise` confirms
  it calls `dispatch_structured` with `stage="revise"`.
- Few-shot examples present: `grep -c "Exemplo" pipeline/prompts/templates/
  s_translate_pt.xml.j2` ≥ 2.

## Rollback

`git revert <commit>` — additive only. No call sites yet.
