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

## Execution Report

### Status: COMPLETED

### What Was Done
- Wrote `pipeline/prompts/templates/s_translate_pt.xml.j2` (~85 lines).
  System prompt names the translator role and three audiences
  (native PT, BR/AO immigrants, UA diaspora). User prompt encodes the
  AC4 rule blocks (TENSES, SENTENCE LENGTH, VOCABULARY, PROPER NOUNS,
  TONE, STRUCTURE) plus three UA→PT B1 few-shot examples (lede,
  3-item list, idiom flattened).
- `pipeline/schemas/translation_pt.json` — title, description, article
  required; summary optional.
- `pipeline/prompts/builder.py` — added `build_translate_pt_prompt(ctx)`
  and `build_translate_digest_pt_prompt(digest_ua)` (TASK-11 helper).
- `pipeline/prompts/templates/s11_digest_translate_pt.xml.j2` — added
  here so TASK-11 has the template ready.
- `pipeline/llm.py` — added `dispatch_translate(prompt, *, system,
  schema, lang)` that rejects non-PT langs and routes via
  `dispatch_structured(stage="revise")`. Calls
  `_maybe_warn_translation_cost` after each call (best-effort; never
  fails the call).
- `pipeline/config.py` — added `TRANSLATION_COST_WARN_USD` (default
  $0.10/call), `TG_CHANNEL_PT_USERNAME = "pastelka_pt"`,
  `TG_CHANNEL_PT_ID` from env.
- `tests/test_llm.py` — added 4 cases:
  - `test_dispatch_translate_routes_via_revise`
  - `test_dispatch_translate_rejects_non_pt`
  - `test_translation_cost_warn_fires_above_threshold`
  - `test_translation_cost_warn_silent_below_threshold`

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `pipeline/prompts/templates/s_translate_pt.xml.j2` | new (~85 lines) |
| pashtelka-faion-net | `pipeline/prompts/templates/s11_digest_translate_pt.xml.j2` | new (~35 lines) |
| pashtelka-faion-net | `pipeline/schemas/translation_pt.json` | new |
| pashtelka-faion-net | `pipeline/prompts/builder.py` | +18 lines |
| pashtelka-faion-net | `pipeline/llm.py` | +60 lines (`dispatch_translate`, `_maybe_warn_translation_cost`) |
| pashtelka-faion-net | `pipeline/config.py` | +12 lines |
| pashtelka-faion-net | `tests/test_llm.py` | +60 lines |

### Tests
- `pytest tests/test_llm.py -v` — **20 passed in 0.27s**.
- Render smoke: builder returns non-empty system+user, both contain
  "B1", "20 words", "OTAN"; three "Exemplo" markers visible.
- Schema load: `load_schema('translation_pt')['required']` returns
  `['title', 'description', 'article']`.
- `python3 -m pipeline --help` exits 0 (CLI imports clean).

### Issues
- pytest config disables the `logging` plugin (`-p no:logging`), so
  `caplog` errors with a stash KeyError. Worked around by attaching a
  small custom `_LogCapture` handler to `llm.logger` in the two
  cost-warn tests.
- Pulled `TG_CHANNEL_PT_*` config knobs into this commit instead of
  waiting for TASK-10 — additive constants only, and TASK-11 (digest)
  needs them. TASK-10 still ships its `require_pt_channel_id` helper +
  tests.
