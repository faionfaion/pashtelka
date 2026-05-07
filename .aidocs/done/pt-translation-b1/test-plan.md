# Test Plan: Portuguese Translation (B1)

**Implements:** spec.md (AC1..AC9), design.md
**Status:** todo

Each AC has at least one verification command + expected result. Manual-only
checks are flagged. Pipeline tests are unit-level (mocked LLM); integration
checks are smoke-tests on a single real article via `--dry-run` paths.

## Pre-flight

```bash
cd ~/workspace/projects/pashtelka-faion-net

# Sanity: pipeline still imports
python3 -m py_compile pipeline/llm.py
python3 -m py_compile pipeline/stages/s_translate_pt.py
python3 -m py_compile pipeline/b1_validator.py

# Plan mode never crashes (no LLM call)
python3 -m pipeline plan -v   # exits 0 or 2 (preflight); 1 means real bug

# Schema loads
python3 -c "from pipeline.schemas import load_schema; print(load_schema('translation_pt')['required'])"
```

## AC1 — Translation pipeline stage

### Unit tests

`tests/test_stages.py` adds `TestSTranslatePt`:

- `test_calls_dispatch_translate` — mock `dispatch_translate`, verify
  call shape (system non-empty, schema is the loaded translation_pt
  schema, lang="pt"), verify ctx mutated.
- `test_writes_pt_fields` — confirm `ctx.article_text_pt` /
  `ctx.title_pt` / `ctx.description_pt` / `ctx.b1_metrics` set after
  successful run.
- `test_retries_once_on_b1_failure` — first dispatch returns "hard"
  text, validator reports `passed=False`, second dispatch is called with
  the addendum. Final result kept.
- `test_b1_warning_on_double_failure` — both attempts fail validator;
  `ctx.b1_warning` is True; article still set.

```bash
python3 -m pytest tests/test_stages.py::TestSTranslatePt -v
```

### Smoke (one real article, dry-run)

```bash
# Pick the most recent UA article
SAMPLE=$(ls -t content/*.md 2>/dev/null | head -1)   # pre-migration
# Or after migration:
SAMPLE=$(ls -t content/*/uk.md | head -1)

# Run the standalone translate helper
python3 -c "
from pathlib import Path
from pipeline.stages.s_translate_pt import translate_one_file
src = Path('$SAMPLE')
out = translate_one_file(src)
print('out:', out, 'exists:', out.exists())
"
```

Expected: `content/<slug>/pt.md` exists, frontmatter has `lang: \"pt\"`,
body is non-empty PT text, structure preserved (same headings count,
same number of links).

## AC2 — Content directory migration

```bash
# Idempotent dry-run
python3 scripts/migrate_to_locale_dirs.py --dry-run | head -20

# Real migration (one-shot)
python3 scripts/migrate_to_locale_dirs.py

# Re-run is a no-op
python3 scripts/migrate_to_locale_dirs.py | grep -c "skip" \
    # expect: ≥150 (all already migrated)

# Spot check structure
ls content/aima-deadline-passed-april-16-day-after-checklist/
# expect: uk.md   (no pt.md yet — that comes from new pipeline runs)

# Git history preserved (rename, not add+delete)
git log --follow --oneline -- content/aima-deadline-passed-april-16-day-after-checklist/uk.md \
    | head -5
# expect: at least one commit before the migration (rename detected)
```

## AC3 — B1 readability validator

### Unit tests

`tests/test_b1_validator.py`:

- `test_passes_simple_text` — short PT sentences, common words → passes.
- `test_fails_on_long_sentences` — paragraph with 30+ word sentence →
  `avg_sentence_words` > 20 → `passed=False`.
- `test_fails_on_low_flesch` — long words, complex syntax → flesch < 65
  → fails.
- `test_fails_on_oov` — sentences full of off-list lemmas →
  `b1_coverage_pct` < 90 → fails.
- `test_retry_addendum_present` — failing case returns non-None
  `retry_addendum` mentioning the failed metric.
- `test_skips_markdown` — markdown headings + links don't break
  tokenisation.

```bash
python3 -m pytest tests/test_b1_validator.py -v
```

### Manual sample check

```bash
python3 - <<'EOF'
from pipeline.b1_validator import b1_validate
sample = """
Bom dia. Hoje, em Lisboa, a chuva voltou.
A AIMA abriu um novo portal para a reagrupamento familiar.
Os imigrantes podem agora marcar a entrevista online.
O processo demora cerca de duas semanas.
"""
print(b1_validate(sample))
EOF
```

Expected: `passed: True`, `flesch ≥ 65`, `avg_sentence_words ≤ 12`,
`b1_coverage_pct ≥ 90`.

## AC4 — B1 translation prompt

### Static checks

```bash
# Template renders
python3 - <<'EOF'
from pipeline.prompts.builder import render
system, user = render(
    "s_translate_pt.xml.j2",
    title="Test", body="Корот��е речення для тесту.",
    description="Опис.",
)
assert "B1" in system or "simplified" in system
assert "20 words" in (system + user) or "20 palavras" in (system + user)
assert "OTAN" in (system + user)   # NATO mapping example
print("ok")
EOF

# Few-shot examples present
grep -c "Exemplo" pipeline/prompts/templates/s_translate_pt.xml.j2   # ≥2
```

### Prompt-output sanity (mocked at LLM layer; checks rules visible)

`tests/test_prompts.py` adds `test_translate_pt_prompt_contains_rules`
asserting all 6 rule blocks (tenses, sentence length, idioms, proper
nouns, tone, structure) are in the rendered system or user prompt.

## AC5 — Gatsby /pt/ routing

### Build check

```bash
cd ~/workspace/projects/pashtelka-faion-net/gatsby
npm run clean
npm run build
```

Expected: build exits 0, no errors.

### Route presence

```bash
# Pick one slug that has both uk.md and pt.md (after smoke test)
SLUG=$(ls /home/nero/workspace/projects/pashtelka-faion-net/content/ \
        | head -1 | tr -d '/')

test -f gatsby/public/uk/$SLUG/index.html
test -f gatsby/public/pt/$SLUG/index.html

# Hreflang link tags
curl -s file://$(pwd)/gatsby/public/uk/$SLUG/index.html | \
  grep -E 'hreflang="(uk|pt|x-default)"' | wc -l
# expect: ≥3 (uk + pt + x-default)
```

### Index pages

```bash
test -f gatsby/public/uk/index.html
test -f gatsby/public/pt/index.html

grep -c 'lang="uk"' gatsby/public/uk/index.html   # ≥1
grep -c 'lang="pt"' gatsby/public/pt/index.html   # ≥1
```

### Sitemaps

```bash
test -f gatsby/public/sitemap-uk.xml
test -f gatsby/public/sitemap-pt.xml
test -f gatsby/public/sitemap-index.xml || test -f gatsby/public/sitemap.xml

grep -c "/uk/" gatsby/public/sitemap-uk.xml   # ≥1
grep -c "/pt/" gatsby/public/sitemap-pt.xml   # ≥1 (after first PT article)
```

### Root redirect

```bash
# Either /index.html still serves UA content, or it redirects to /uk/.
# The chosen approach (filter UA-only at /) requires:
grep -c 'lang="uk"' gatsby/public/index.html   # ≥1
```

## AC6 — TG channel @pastelka_pt

Manual until the operator creates the channel:

```bash
# Config knob exists
python3 -c "from pipeline.config import TG_CHANNEL_PT_USERNAME, TG_CHANNEL_PT_ID; \
  print('username:', TG_CHANNEL_PT_USERNAME, 'id:', TG_CHANNEL_PT_ID or 'EMPTY')"
# expect: username=pastelka_pt, id=EMPTY (until operator sets env)

# Empty id triggers clear failure
python3 -c "
from pipeline.telegram import send_photo_pt_safe   # tiny helper added in s11
try:
    send_photo_pt_safe('/tmp/x.jpg', 'caption', silent=False)
except RuntimeError as e:
    print('correctly failed:', e)
"
# expect: 'TG_CHANNEL_PT_ID is not set...' message
```

After channel exists (operator-side):

```bash
# 1. Operator creates @pastelka_pt
# 2. Adds @nero_open_bot as admin
# 3. Looks up chat_id via getUpdates
# 4. export TG_CHANNEL_PT_ID=-1003xxxxxxxxxx
# 5. Re-runs digest --dry-run, then real digest
```

## AC7 — Daily digest in PT

### Unit (mocked LLM + send)

`tests/test_stages.py` `TestS11Digest` extended with:

- `test_dual_language_send_when_pt_id_set` — env has TG_CHANNEL_PT_ID,
  both `_send_digest` calls happen, both with same image path, different
  captions, different chat_ids.
- `test_pt_skipped_when_id_empty` — TG_CHANNEL_PT_ID empty, only UA
  send happens, warning logged.

### Integration smoke

```bash
# Dry-run: build digest dict locally, don't send to TG
python3 - <<'EOF'
import os
os.environ["TG_CHANNEL_PT_ID"] = ""           # force PT skip
os.environ["LLM_STACK"] = "old"               # use whatever default
from pipeline.stages.s11_digest import _generate_digest, _translate_digest_to_pt
articles = [
    {"slug": "test-1", "title": "Тест 1", "body": "Перше речення тестове."},
] * 10
ua = _generate_digest(articles, "2026-05-06", "Середа")
pt = _translate_digest_to_pt(ua)
assert "intro" in pt and "items" in pt
assert all("title" in i and "slug" in i for i in pt["items"])
print("ok")
EOF
```

## AC8 — Editorial plan unchanged

```bash
# Plan stage is not in the changed-stages list
git diff master -- pipeline/stages/s0_editorial_plan.py
# expect: no diff (plan stays UA-only)

# Cross-references still resolve via shared slugs
grep -E "/$slug/" gatsby/public/uk/<other-slug>/index.html
# expect: ≥0 (depends on article)
```

## AC9 — Cost guardrails

```bash
# Soft warning fires at threshold
python3 - <<'EOF'
import logging, os
os.environ["TRANSLATION_COST_WARN_USD"] = "0.001"   # force trigger
logging.basicConfig(level=logging.WARNING)
from pipeline.llm import _maybe_warn_translation_cost
_maybe_warn_translation_cost(in_tokens=1_000_000, out_tokens=1_000_000, model="gpt-5.5")
EOF
# expect: WARNING log line "translation cost ... exceeds threshold..."
```

## End-to-end smoke

After all tasks land, run on one article:

```bash
# 1. Migrate (idempotent)
python3 scripts/migrate_to_locale_dirs.py

# 2. Pick a slug, force-translate
SLUG=$(ls content | head -1)
python3 -c "
from pathlib import Path
from pipeline.stages.s_translate_pt import translate_one_file
out = translate_one_file(Path('content/$SLUG/uk.md'))
print('out:', out)
"

# 3. Build site
cd gatsby && npm run build

# 4. Verify
test -f content/$SLUG/pt.md
test -f public/uk/$SLUG/index.html
test -f public/pt/$SLUG/index.html
grep -c 'b1_warning' content/$SLUG/pt.md   # 0 or 1 (advisory)
```

## Final verification matrix

| AC | Verification | Pass criterion |
|----|--------------|----------------|
| AC1 | unit + smoke | stage runs, ctx mutated, file written |
| AC2 | migration script + git log | flat → nested, history preserved, idempotent |
| AC3 | unit tests on validator | 4+ passing tests, sample article scored |
| AC4 | template render + grep | rules + 2 examples visible |
| AC5 | npm run build + curl | build green, /uk/ + /pt/ index + article URLs serve |
| AC6 | config sanity + manual | TG_CHANNEL_PT_USERNAME exists, empty id fails clearly |
| AC7 | unit tests + smoke | dual send when id set, skip when empty |
| AC8 | git diff | plan stage untouched |
| AC9 | warn-cost call | warning logged when threshold crossed |
