# TASK-13 — Cost-warn helper + end-to-end smoke + done.md

**Subject:** Wire the soft cost-warn helper into the translation path,
run a full smoke test on one real UA article (translate → save → build),
write `done.md` and promote the feature folder.

## Files touched

- `pipeline/llm.py` (add `_maybe_warn_translation_cost`)
- `pipeline/config.py` (add `TRANSLATION_COST_WARN_USD`)
- `.aidocs/in-progress/pt-translation-b1/done.md` (new)
- `.aidocs/in-progress/pt-translation-b1/` → `.aidocs/done/`

## Approach

`_maybe_warn_translation_cost(in_tokens, out_tokens, model)` computes
USD via existing `estimate_usd` and logs a `WARNING` when the cost
exceeds `TRANSLATION_COST_WARN_USD`. Called from `dispatch_translate`
after the LLM call returns, using the request's input/output character
counts (pre-existing patterns in `llm.py`).

Smoke test (manual, via Python REPL or one-shot script in `/tmp/`):

```python
from pathlib import Path
from pipeline.stages.s_translate_pt import translate_one_file

src = Path("content/<sample-slug>/uk.md")
out = translate_one_file(src)
assert out.exists()
print("smoke ok:", out)
```

Then `cd gatsby && npm run build` and verify both
`public/uk/<sample>/index.html` and `public/pt/<sample>/index.html`
exist.

`done.md` covers:
- Commits + hashes + titles.
- Env-var contract (`TG_CHANNEL_PT_ID` operator-side).
- B1 metrics on the smoke article.
- Gatsby build summary.
- Open follow-ups (channel creation, backfill, lemma list swap-in).
- Full rollback procedure.

## Success criterion

- Cost warn fires above threshold (test with `TRANSLATION_COST_WARN_USD=
  0.001`).
- Smoke article: `pt.md` exists, frontmatter valid, body non-empty.
- `npm run build` exits 0; both URLs render.
- `done.md` written.
- Folder promoted: `.aidocs/in-progress/pt-translation-b1/` →
  `.aidocs/done/pt-translation-b1/`.

## Rollback

Last commit reverts the smoke + done.md only — no functional change.
Full feature rollback documented in `done.md`.
