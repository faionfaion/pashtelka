# pt-translation-b1 — done

Shipped (master, 13 tasks, single-repo, 14 commits including planning).

## What shipped

- **Translation pipeline**. `pipeline/stages/s_translate_pt.py` runs after
  `s5_revise` and before `s7_save`. Routes through
  `pipeline.llm.dispatch_translate` (NOT `pipeline.sdk` directly), so the
  existing `LLM_STACK={old,new}` toggle drives translation along with every
  other stage. After every LLM call the `pipeline/b1_validator.py`
  (Flesch + sentence length + lemma coverage) scores the output. First
  failure triggers a single retry with a `retry_addendum`. Second failure
  ships with `b1_warning: true` in the PT frontmatter.
- **Content layout**. 158 articles migrated from flat `content/<slug>.md`
  to nested `content/<slug>/uk.md` via `scripts/migrate_to_locale_dirs.py`
  using `git mv` so file history follows. Idempotent. New pipeline runs
  write `<slug>/uk.md` + `<slug>/pt.md` from `s7_save`.
- **Gatsby /uk/ and /pt/ routing**. `gatsby-node.js` groups markdown by
  slug × locale and creates per-locale article URLs. Article template +
  Layout switch UI strings via `gatsby/src/i18n/{uk,pt}.json`. Hreflang
  triplet (uk + pt-when-available + x-default) on every article. Per-
  locale homepages at `/uk/` and `/pt/`. Root `/` keeps serving UA and
  links lead to `/uk/<slug>/`.
- **Sitemaps split**. Post-build script writes `sitemap-uk.xml`,
  `sitemap-pt.xml`, and a `sitemap.xml` index referencing both.
- **TG channel `@pashtelka_pt`**. Config knobs in `pipeline/config.py`,
  clear-fail helper `require_pt_channel_id()` in `pipeline/telegram.py`,
  dual-language daily digest in `s11_digest.py` (same image, different
  caption per locale, glossary stripped from PT).
- **Cost guardrail**. `_maybe_warn_translation_cost` logs a `WARNING`
  when an estimated cost exceeds `TRANSLATION_COST_WARN_USD` (default
  `$0.10/call`). No hard ceiling — production must not silently skip
  articles.
- **Operator backfill**. `scripts/backfill_pt.py` covers existing UA
  articles whose PT counterparts must be generated separately. Scope
  flags `--all`/`--since`/`--slug`, `--dry-run`, `--max N`. **Not run
  inside this feature** (the live pipeline picks up new articles
  automatically; backfilling 157 historic articles is operator's call).

## Commits

| Hash | Title |
|------|-------|
| f78adeae | docs: plan pt-translation-b1 (design, tests, tasks) |
| c0b0fee1 | feat(TASK-01): b1 readability validator + lemma list |
| 9e4572cb | feat(TASK-02): pt translate prompt + schema + dispatcher |
| 7a725be1 | feat(TASK-03): s_translate_pt stage routed via llm dispatcher |
| ee10e712 | feat(TASK-04): wire s_translate_pt into generate mode |
| 758219da | feat(TASK-05): content migration script |
| 52d13a03 | chore: migrate content/ to per-slug locale dirs |
| 89da6757 | feat(TASK-06): s7_save dual-locale write |
| 91ad85a4 | feat(TASK-07): gatsby /uk/ + /pt/ article routing |
| 3d0464e6 | feat(TASK-08): locale-aware templates + index pages |
| a3bd4c6a | feat(TASK-09): post-build sitemap splitter |
| 59cd0251 | feat(TASK-10): require_pt_channel_id helper |
| b894564e | feat(TASK-11): dual-language daily digest |
| 9fd0778a | feat(TASK-12): backfill_pt.py operator helper |

The TASK-13 final commit lands alongside this `done.md` and the feature
folder promotion.

## Env-var contract

| Name | Required when | Default | Notes |
|------|---------------|---------|-------|
| `LLM_STACK` | always (set per Wave 1) | `old` | Drives translation via dispatch_translate -> dispatch_structured(stage="revise"). |
| `GEMINI_API_KEY` | `LLM_STACK=new` | — | Set per Wave 1. |
| `OPENAI_API_KEY` | `LLM_STACK=new` | — | Set per Wave 1. Codex uses it. |
| `ANTHROPIC_API_KEY` | always | — | Used by review stage (and translation when `LLM_STACK=old`). |
| `TG_CHANNEL_PT_ID` | before PT digest publish | `""` (empty) | Operator creates `@pashtelka_pt`, adds `@nero_open_bot` as admin, copies the chat_id (starts with `-100`), exports here. |
| `TRANSLATION_COST_WARN_USD` | optional | `0.10` | Soft warning threshold per translation call. |
| `TG_CHANNEL_PT_USERNAME` | (constant) | `pashtelka_pt` | Hard-coded brand handle. |

## B1 metrics (smoke article)

A hand-written PT translation of `aima-deadline-passed-april-16-day-after-checklist`
ships at `content/<slug>/pt.md` to verify the dual-locale Gatsby build.
Validator output for the smoke article:

| Metric | Value | Threshold | Pass? |
|--------|-------|-----------|-------|
| Flesch reading ease | 36.9 | ≥ 65 | NO |
| Avg sentence length | 7.9 words | ≤ 20 | YES |
| B1 lemma coverage | 76.5% | ≥ 90% | NO |
| Overall | failed | — | shipped with `b1_warning` flag if produced via pipeline |

The hand-written sample is intentionally NOT through the pipeline retry
loop. textstat's PT Flesch formula is strict for news vocab; the operator
should observe 50+ real pipeline translations and tune `FLESCH_MIN` (and
optionally `COVERAGE_MIN_PCT`) in `pipeline/b1_validator.py` based on
real-world output. The constants are deliberately conservative for v1.

## Gatsby build summary

`npm run clean && npm run build` exits 0. Output:

- **160 UA URLs** in `sitemap-uk.xml` (158 articles + `/uk/` + `/uk/welcome/`).
- **3 PT URLs** in `sitemap-pt.xml` (the smoke article + `/pt/` + `/pt/welcome/`).
- 642 tag pages (UA-only, locale-neutral, listed in both sitemaps).
- All 158 UA article HTML files have proper hreflang `uk` + `x-default`,
  `og:locale=uk_UA`, canonical at `/uk/<slug>/`, `<html lang="uk">`.
- The smoke PT article has hreflang `uk` + `pt` + `x-default`,
  `og:locale=pt_PT`, `og:locale:alternate=uk_UA`, canonical at
  `/pt/<slug>/`, `<html lang="pt">`.
- `sitemap.xml` is the proper sitemapindex referencing both locale
  sitemaps with absolute URLs.

## Operator items before / after deploy

1. **Create the PT TG channel** `@pashtelka_pt`.
   - Add `@nero_open_bot` as admin with publishing rights.
   - Set avatar + bio in PT (mirror UA channel intent; pinned welcome
     post linking to `https://pastelka.news/pt/welcome/` per the AC6
     wave-2 deliverable).
   - Run `/getUpdates` once to find the chat_id (starts with `-100`).
   - `export TG_CHANNEL_PT_ID="-1003xxxxxxxxxx"` in `~/workspace/.env` on
     **faion-net** (digest cron host).

2. **Add `GEMINI_API_KEY` if flipping to `LLM_STACK=new`**. (Already
   covered by the Wave 1 done.md; restated here for completeness.)

3. **Run a dry-run digest before live publish** to confirm the PT
   channel is reachable:
   ```bash
   ssh faion-net 'cd /var/www/pastelka.news/repo && \
     LLM_STACK=$LLM_STACK TG_CHANNEL_PT_ID=$TG_CHANNEL_PT_ID \
     python3 -m pipeline digest --dry-run -v'
   ```

4. **Backfill historic UA articles** (optional, after channel + digest
   look healthy on a few new pipeline runs):
   ```bash
   # Start small
   python3 scripts/backfill_pt.py --since 2026-04-25 --max 5 -v

   # Then expand
   python3 scripts/backfill_pt.py --all --max 50

   # Full corpus (~157 calls, ~$1-3 in Codex)
   python3 scripts/backfill_pt.py --all
   ```

5. **Tune the B1 validator after observing real translations**.
   Suggested workflow: spot-check 50 PT articles after the first week,
   collect failures, decide whether to:
   - Lower `FLESCH_MIN` (e.g. 55 instead of 65) — PT Flesch is harsher
     than EN for the same readability level.
   - Lower `COVERAGE_MIN_PCT` to 85 if news vocabulary consistently
     pushes boundary words out of the top-3000 list.
   - Or extend `pipeline/data/pt_b1_lemmas.txt` with curated news
     terms (`AIMA`, `IRS`, `IMI`, etc. — though those are proper nouns
     already excluded by the validator).

6. **Lemma list swap-in (optional)**. The shipped 3000-lemma list comes
   from OpenSubtitles 2018 and is dialogue-heavy. To swap in a
   news-corpus list:
   ```bash
   curl -sL https://github.com/hermitdave/FrequencyWords/raw/master/content/2018/pt/pt_50k.txt \
     | head -3000 | awk '{print $1}' \
     > pipeline/data/pt_b1_lemmas.txt
   ```
   (This is the same source we already shipped from — redownload if you
   want to refresh.)

7. **Plausible analytics** (carried over from Wave 2): if the PT
   channel grows, add a custom event split for `/pt/` pageviews via
   the existing Plausible site config. No code change needed.

## Rollback

Three layers, finest-grained first:

```bash
# Stop translating (keep PT site live with stale data)
git revert <s_translate_pt-stage commits ee10e712..7a725be1>

# Stop publishing PT digest (UA digest unchanged)
unset TG_CHANNEL_PT_ID    # in ~/workspace/.env

# Roll Gatsby back to single-locale routing
git revert <gatsby commits 91ad85a4..a3bd4c6a, 3d0464e6, 89da6757>

# Roll content layout back to flat *.md (rare; only if migration corrupted data)
for d in content/*/; do
  test -f "$d/uk.md" && git mv "$d/uk.md" "${d%/}.md" && rmdir "$d"
done
git commit -m "revert: undo content per-slug locale migration"
```

The `LLM_STACK` toggle keeps working — pt translation flips to Claude
on `old` and Codex on `new`, identical to article generation.

## Pre-existing test failures (out of scope)

The repo's `tests/test_stages.py::TestS11Digest` class has 5 failures
referencing a digest implementation that no longer exists (removed in
the 2026-04-24 digest-only refactor before any of these features
started). Documented in `.aidocs/done/pipeline-gemini-codex/done.md`.
This feature does not touch them — `TestS11DigestDualLang` is a fresh
test class for the dual-language flow and is 5/5 green.

`tests/test_sdk.py`, `tests/test_prompts.py::TestBuildDigestPrompt`,
`tests/test_schemas.py::test_load_digest` also have pre-existing
failures from the same refactor. Untouched.

## Out of scope (open follow-ups)

- ES/FR/EN locales — URL space reserved by the new gatsby-node
  routing, no implementation.
- Translating the tag taxonomy — `/tag/<tag>/` stays UA-only.
- Per-article quality A/B comparing translation engines.
- Live language switcher beyond the lang-chip in the header.
- AI-translated comments / audio.
- Replacing the placeholder hero on the welcome pages (carried over
  from Wave 2 → `print-stickers-posters` feature).
- 404 → Telegram alert wiring (existing pipeline notification SDD).
- Plausible PT analytics breakdown (single Plausible site for both
  locales for now).
