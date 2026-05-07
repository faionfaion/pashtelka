# Design: Portuguese Translation (B1) + Site + TG Channel

**Implements:** spec.md (AC1..AC9)
**Status:** todo
**Owner:** Ruslan

## High-level approach

Add Portuguese as a fully-fledged second locale on top of the existing UA
pipeline without forking the editorial process. The plan stays UA-side; the
PT version is produced by a mechanical translation stage that runs after
revise and before save. PT readers consume the same articles in simplified
B1 Portuguese on `/pt/<slug>/` and via a dedicated TG channel `@pastelka_pt`.

Five concerns, five layers:

1. **Pipeline** — new stage `s_translate_pt` slotted between revise and save;
   routed through `pipeline/llm.py` (no direct `pipeline.sdk` imports).
2. **Content layout** — flat `content/<slug>.md` becomes
   `content/<slug>/uk.md` + `content/<slug>/pt.md`. Idempotent migration
   script using `git mv` so history survives.
3. **B1 quality gate** — `textstat`-based validator + B1 lemma list; one
   retry with a "simplify further" prompt addendum; final fallback flags
   the article with `b1_warning: true`.
4. **Gatsby** — `gatsby-node.js` learns about the `{uk,pt}.md` shape and
   builds `/uk/<slug>/` and `/pt/<slug>/` pages from the same template
   parametrised by locale. Root `/` redirects to `/uk/`. Hreflang link
   tags between locales. Split sitemaps.
5. **Digest** — `s11_digest` produces UA + PT captions for the same image,
   sends in parallel to `@pashtelka_news` and `@pastelka_pt` at the same
   cron slot.

## Stage chain (after this feature)

```
s0_editorial_plan → s1_collect → s2_research → s3_generate
   → s4_review ⇄ s5_revise (loop)
   → s_translate_pt        ← NEW
   → s6_generate_tg
   → s7_save               (writes both uk.md and pt.md)
   → s7_deploy → s8_verify
```

Translation is **post-review, pre-TG-caption**. Rationale:
- Review must operate on the canonical UA text (saves a roundtrip).
- TG caption (s6) is generated for both locales; doing it after translate
  means we have the PT body ready to summarise.
- Save (s7) is the only stage that writes to disk — good place to keep the
  dual-locale write atomic.

## s_translate_pt implementation

### Module: `pipeline/stages/s_translate_pt.py`

Sync function `run(ctx: PipelineContext) -> None`. Mutates `ctx` by adding
PT-side fields (we extend `PipelineContext` with `article_text_pt`,
`title_pt`, `description_pt`, `summary_pt`, and `b1_metrics: dict`).

```
def run(ctx):
    if not ctx.article_text:
        raise RuntimeError("s_translate_pt requires article_text on ctx")

    system, prompt = build_translate_pt_prompt(ctx)
    schema = load_schema("translation_pt")
    result = dispatch_translate(prompt, system=system, schema=schema, lang="pt")

    metrics = b1_validate(result["article"])
    if not metrics["passed"]:
        # retry once with simplify-further addendum
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

### Dispatcher choice

Add `dispatch_translate(prompt, *, system, schema, lang)` to
`pipeline/llm.py`. It is a thin wrapper around `dispatch_structured` that
fixes `stage="revise"` (Codex on `new`, Claude on `old`). We add the wrapper
because:
- Translation is conceptually distinct from revise; the call site reads
  cleanly.
- We may want to flip translation independently later (e.g. a cheaper PT
  model) without touching every call site.
- `stage="revise"` is the closest neighbour in routing (structured output,
  same vendor preference, same timeout class). Keeps `dispatch_structured`
  unchanged — no need to add a new `_TRANSLATE_STAGE` group right now.

### Prompt template: `pipeline/prompts/templates/s_translate_pt.xml.j2`

System message:
> You are a Portuguese translator. You translate Ukrainian news articles
> into simplified European Portuguese at CEFR B1 level for readers who are
> learning Portuguese.

Rules block (per AC4):
- Tenses: present, past simple (perfeito), future simple (`futuro do
  presente`). Subjunctive only as `que + presente`. Composite tenses
  forbidden except `ter + particípio passado` for recent past.
- Sentence length ≤ 20 words. Long UA sentences split into 2-3 PT.
- Idioms → literal equivalents. No metaphors that lose meaning literally.
- Proper nouns: keep as-is (Lisboa, Porto, AIMA, NATO→OTAN, ONU, UE, EUA,
  RU). Numbers, dates, currencies: preserve exactly.
- Tone: neutral-friendly. Strip UA insider asides ("у нас", "як ми звикли")
  — the article must read as if written for an outside Lisbon reader.
- Preserve structure: headings, lists, links, bold/italic, line breaks.
- Frontmatter is **not** in the input — body markdown only.

Few-shot examples: 2-3 short UA→PT pairs hand-written in the template
to anchor the output style. Stored as static text inside the `.xml.j2`
file. Examples cover: short news lede, list with three items, sentence
with idiom that must be flattened.

### Schema: `pipeline/schemas/translation_pt.json`

```json
{
  "type": "object",
  "properties": {
    "title":       {"type": "string"},
    "description": {"type": "string"},
    "summary":     {"type": "string"},
    "article":     {"type": "string"}
  },
  "required": ["title", "description", "article"]
}
```

## B1 validator

### Module: `pipeline/b1_validator.py`

Single public function:

```
def b1_validate(text: str) -> dict:
    return {
        "passed": bool,
        "flesch": float,
        "avg_sentence_words": float,
        "b1_coverage_pct": float,
        "retry_addendum": str | None,
    }
```

Implementation:
- Strip markdown markup (headings, links, bold) before metrics — measure
  reading prose only.
- `flesch_reading_ease` from `textstat` (PT support since 0.7.4). Threshold:
  ≥ 65.
- Sentence split on `[.!?]+`. Average words per sentence ≤ 20. Skip empty
  segments.
- Lemmatisation lite: lowercase, strip punctuation, remove diacritics
  is NOT applied (PT diacritics are lemma-defining). Tokenise on whitespace
  + Unicode word boundaries; for each token compute its lemma surface form
  using a tiny rules pass (singular, drop common verb suffixes
  -ar/-er/-ir → infinitive form). Coverage threshold: ≥ 90% in the B1
  list. Numbers, proper nouns (capitalised mid-sentence), and tokens ≤ 2
  chars are excluded from the denominator.
- `retry_addendum`: built only when `passed` is False. Mentions exactly
  which metric failed and what to do, e.g.
  ```
  This translation is too hard for B1.
  Avg sentence length is {n} words (target ≤ 20).
  Vocabulary outside B1: {top-5 OOV lemmas}.
  Rewrite using shorter sentences and simpler verbs.
  ```

### Lemma list: `pipeline/data/pt_b1_lemmas.txt`

One lemma per line, lowercased PT, ~3000 entries. Source (preferred):
`https://github.com/hermitdave/FrequencyWords/raw/master/content/2018/pt/pt_50k.txt`,
top 3000 by frequency, deduplicated.

If the live download fails inside the build sandbox, we ship a curated
~500-word seed list (high-confidence everyday + news vocabulary) and
the validator continues to function albeit with a stricter coverage gate.
Operator drops in the full list later via:

```bash
curl -sL https://github.com/hermitdave/FrequencyWords/raw/master/content/2018/pt/pt_50k.txt \
  | head -3000 | awk '{print $1}' \
  > pipeline/data/pt_b1_lemmas.txt
```

Validator does not import the file at module load — it uses
`functools.lru_cache` on first call so tests can monkey-patch.

## Content directory migration

### Script: `scripts/migrate_to_locale_dirs.py`

Idempotent, sync, no LLM calls.

```
for path in CONTENT_DIR.glob("*.md"):
    slug = path.stem
    target_dir = CONTENT_DIR / slug
    target_uk  = target_dir / "uk.md"
    if target_uk.exists():
        logger.info("skip %s: already migrated", slug)
        continue
    target_dir.mkdir(parents=True, exist_ok=True)
    git_mv(path, target_uk)   # subprocess; falls back to shutil.move if not git
```

Idempotency: re-running on already-migrated content is a no-op (the loop
hits no files because `glob("*.md")` excludes subdirs).

`git mv` is used so each rename is recorded as a rename in git history,
not an add+delete. We do **not** modify body content during migration.

After this script runs once on the real content, every existing UA article
is at `content/<slug>/uk.md`. PT versions are written by `s_translate_pt`
into `content/<slug>/pt.md` for new articles. Existing UA articles get
their PT counterpart via the backfill script (see below).

### Script: `scripts/backfill_pt.py`

Operator-triggered. Iterates over `content/<slug>/uk.md` and, where
`pt.md` does not yet exist, calls the translation stage in standalone
mode. Operator chooses scope:

```bash
# All missing — expensive, ~158 calls
python3 scripts/backfill_pt.py --all

# Only the last N articles by date
python3 scripts/backfill_pt.py --since 2026-04-20

# A single slug
python3 scripts/backfill_pt.py --slug aima-deadline-passed-april-16-day-after-checklist
```

We ship the script but do **not** run it in this feature. Documented in
`done.md` for the operator to schedule when they want.

## Frontmatter on PT files

```yaml
---
title: "<translated title>"
slug: "<shared slug>"
date: "<original date>"
type: "<original type>"
lang: "pt"
tags: [<original tags>]    # tag taxonomy stays UA — easier to merge analytics
description: "<translated description>"
author: "Pastelka News"
source_urls: [<unchanged>]
source_names: [<unchanged>]
image: "<unchanged>"
tg_post: "<empty — PT TG caption generated by s6/s10>"
b1_warning: true   # only when validator fails twice
---
```

## s7_save changes

`s7_save.run(ctx)` writes both files when the PT fields are present.

```
slug_dir = CONTENT_DIR / ctx.slug
slug_dir.mkdir(parents=True, exist_ok=True)
write(slug_dir / "uk.md", build_md(ctx, lang="ua"))
if ctx.article_text_pt:
    write(slug_dir / "pt.md", build_md(ctx, lang="pt"))
```

Frontmatter helper extended to switch fields by lang. The git commit step
remains; the commit picks up both new files in one commit.

## Gatsby /pt/ routing

### gatsby-node.js

Replace the current "create one page per article" with locale-aware
creation:

```js
const result = await graphql(`{
  allMarkdownRemark(sort: {frontmatter: {date: DESC}}) {
    nodes {
      frontmatter { slug, title, date, type, tags, lang, ... }
      html
      wordCount { words }
      fileAbsolutePath
    }
  }
}`);

const bySlugLang = {};
for (const n of result.data.allMarkdownRemark.nodes) {
  const lang = n.frontmatter.lang || "ua";   // legacy fallback
  const slug = n.frontmatter.slug;
  bySlugLang[slug] = bySlugLang[slug] || {};
  bySlugLang[slug][lang] = n;
}

for (const slug of Object.keys(bySlugLang)) {
  const variants = bySlugLang[slug];
  for (const lang of ["uk", "pt"]) {
    const node = variants[lang === "uk" ? "ua" : "pt"];
    if (!node) continue;
    createPage({
      path: `/${lang}/${slug}/`,
      component: path.resolve("./src/templates/article.js"),
      context: {
        slug,
        lang,                                       // "uk" | "pt"
        otherLocaleAvailable: lang === "uk" ? !!variants.pt : !!variants.ua,
      },
    });
  }
}
```

We pin the URL prefix to `/uk/` even though the frontmatter `lang` value
is `"ua"` (kept for backwards compat). The mapping is one-line.

Tag pages stay flat at `/tag/<tag>/` for now — translating the tag
taxonomy is out of scope for v1.

### Root `/` redirect

`gatsby/static/_redirects` (Netlify-style) is not honoured by nginx, so
we add a tiny static page at `gatsby/static/index.html` only if no React
index exists. The current `src/pages/index.js` lists ALL articles
regardless of `lang`, which would mix locales — we change the GraphQL
query to filter `frontmatter: {lang: {eq: "ua"}}` and treat `/` as the
UA homepage. That keeps `/` working without a redirect; users who land
on `/` get UA content as before. We add a small lang-switcher chip in
the header pointing at `/pt/` (which is also a new index).

`/pt/` index page: copy of `index.js` with PT strings + `lang=pt` filter.

### Article template (`src/templates/article.js`)

Add `pageContext.lang` and switch UI strings via a tiny i18n dict
(`src/i18n/uk.json`, `src/i18n/pt.json`). Hreflang links in `Head`:

```jsx
<link rel="alternate" hrefLang="uk" href={`https://pastelka.news/uk/${slug}/`} />
{otherLocaleAvailable && (
  <link rel="alternate" hrefLang="pt" href={`https://pastelka.news/pt/${slug}/`} />
)}
<link rel="alternate" hrefLang="x-default" href={`https://pastelka.news/uk/${slug}/`} />
<html lang={lang} />
```

Date formatting: `toLocaleDateString(lang === "pt" ? "pt-PT" : "uk-UA", …)`.
"X хв читання" / "X min de leitura" via i18n.

### Sitemaps

`gatsby-plugin-sitemap` produces a single `sitemap.xml`. We split it via
the plugin's `resolvePages` option into two: `sitemap-uk.xml` (UA pages)
and `sitemap-pt.xml` (PT pages), referenced by a small index
`sitemap.xml`. Plugin supports this natively via `excludes` + multiple
plugin instances; alternative is a post-build node script that splits the
output. We pick the post-build approach for simplicity:
`gatsby/scripts/split-sitemaps.mjs` runs in `package.json` `postbuild`.

## TG channel `@pastelka_pt`

### Config

Add to `pipeline/config.py`:

```python
TG_CHANNEL_PT_USERNAME = "pastelka_pt"
TG_CHANNEL_PT_ID = os.environ.get("TG_CHANNEL_PT_ID", "")
```

We split env-var name from username — username is hard-coded (brand,
public), chat_id is private and goes in `~/workspace/.env`. Until the
operator creates the channel and adds the bot, `TG_CHANNEL_PT_ID` is
empty. Publish path detects the empty value and FAILS with a clear
message:

```
RuntimeError: TG_CHANNEL_PT_ID is not set. Create @pastelka_pt in
Telegram, add @nero_open_bot as admin, look up the chat_id (start with
"-100"), and put it in ~/workspace/.env as TG_CHANNEL_PT_ID=…
```

Ditto: `TG_CHANNEL_PT_USERNAME` always exists for caption-side
references (used in `<a href="https://t.me/pastelka_pt">` links and the
Welcome page CTA — already wired by Wave 2).

## Digest dual-language

### s11_digest changes

The current `run()` produces one digest, sends to `TG_CHANNEL_ID`. New
flow:

```
result_ua = _generate_digest(articles, today, weekday)         # existing
result_pt = _translate_digest_to_pt(result_ua)                  # NEW

image_path = generate_image(...)                                # SAME image

caption_ua = _build_caption(result_ua, lang="uk")
caption_pt = _build_caption(result_pt, lang="pt")

msg_ua = _send_digest(image_path, caption_ua, TG_CHANNEL_ID,    silent)
msg_pt = _send_digest(image_path, caption_pt, TG_CHANNEL_PT_ID, silent) \
            if TG_CHANNEL_PT_ID else None
```

Image stays the same per spec AC7 ("brand mark", revisit at 1k PT
readers).

`_translate_digest_to_pt(result_ua)` is a small wrapper around
`dispatch_translate` that translates only the human-readable strings
(intro, item titles, item hooks, glossary lines stay as PT→UA pairs but
flipped to PT→PT/UA dual where useful — for v1 we keep glossary unchanged
because PT readers don't need a PT→UA word card). We translate `intro`,
each item's `title` and `hook`, and pass through `slug`/`emoji` unchanged.
The image_prompt is not used in the second send — we already have the
image.

Schema for the translated digest is a simpler subset of the UA digest
schema: just `intro`, `items[{emoji, title, hook, slug}]`. Glossary is
stripped from the PT version.

Failure mode: if PT TG send fails (channel doesn't exist yet, network
flake) the UA send still happens and is reported as success. The PT
failure is logged as a warning so the operator notices.

## Cost guardrails

Translation adds 1 LLM call per article on the generate path
(~ 12 articles/day) plus 1 call for the digest. Total adds ~13 calls/day
on top of the existing ~50. With Codex CLI gpt-5.5 ($1.25/M in,
$10/M out), per-translation cost ~ $0.005-0.02 depending on article
length. Daily added cost ≈ $0.10-0.30. UA-only baseline ≈ $0.50-1.00
day. Total stays well within 1.5× baseline.

We add a soft warning log if `_translation_cost(in_tokens, out_tokens) >
TRANSLATION_COST_WARN_USD` (default $0.10/call). No hard ceiling — production
must not silently skip articles.

```python
# pipeline/config.py
TRANSLATION_COST_WARN_USD = float(os.environ.get("TRANSLATION_COST_WARN_USD", "0.10"))
```

## Open questions resolved by spec

| Open Q | Default applied |
|--------|-----------------|
| Drop b1_warning, hard-block on failure? | Keep warn-and-ship — quantity beats perfect at v1 (per spec). |
| PT lemma list source unavailable? | Ship 500-lemma seed; document URL for operator to swap in. |
| PT digest image overlay? | Same image, only caption translated. |

## Out of scope (v1)

- Translating the tag taxonomy.
- Translating the editorial plan (PT operator-side).
- ES/FR/EN locales (URL space reserved).
- Per-article quality A/B between Codex and Claude PT translations.
- Live language switcher beyond a small lang chip in the header.
- Rebuild of historic UA articles' PT versions — handled by the operator-
  triggered `backfill_pt.py`.

## Rollback

Each commit is reversible. The translation stage is gated by the presence
of `s_translate_pt` in `pipeline/modes/generate.py` — comment one line and
the pipeline reverts to UA-only. The `content/<slug>/{uk,pt}.md` shape is
forward-compatible: gatsby-node falls back to a flat `*.md` lookup if
neither variant is present (defensive code path retained for one release).

Full rollback procedure:

```
# Stage 1 — disable translation only (PT site keeps working with stale data)
git revert <s_translate_pt-stage commits>

# Stage 2 — full revert (PT site goes away)
git revert <gatsby /pt/ commits>

# Stage 3 — undo content migration (rare; only if migration corrupted data)
python3 scripts/migrate_to_locale_dirs.py --reverse
```

`migrate_to_locale_dirs.py --reverse` is a documented but not
implemented flag in v1 (operator can do it manually with three `git mv`
commands per slug).
