# Implementation Plan: Portuguese Translation (B1)

**Implements:** spec.md, design.md, test-plan.md
**Status:** todo
**Owner:** Ruslan

## Build order

```
TASK-01 b1-validator + lemma list + textstat dep
   ↓
TASK-02 translation prompt template + schema + dispatcher wrapper
   ↓
TASK-03 s_translate_pt stage (uses TASK-01 + TASK-02)
   ↓
TASK-04 wire stage into generate mode + ctx fields
   ↓
TASK-05 content migration script + run it on real content
   ↓
TASK-06 s7_save dual-locale write
   ↓
TASK-07 gatsby-node /uk/, /pt/ routing + i18n strings
   ↓
TASK-08 article template locale-aware + hreflang + index pages
   ↓
TASK-09 sitemaps split (post-build) + npm run build
   ↓
TASK-10 TG_CHANNEL_PT config + clear-fail telegram helper
   ↓
TASK-11 s11_digest dual-language flow
   ↓
TASK-12 backfill_pt.py operator script (no run)
   ↓
TASK-13 cost-warn helper + smoke test on one article
```

Sequential because every later task depends on artefacts from earlier ones
(stage needs validator, save needs stage, gatsby needs nested content,
digest needs translation helpers, etc.). Parallelisable inside a task only.

## Tasks

| ID | Subject | Files | Est. tokens | Depends on | Completion criterion |
|----|---------|-------|-------------|------------|----------------------|
| TASK-01 | B1 validator + lemma list + textstat | `pipeline/b1_validator.py`, `pipeline/data/pt_b1_lemmas.txt`, `requirements.txt`, `tests/test_b1_validator.py` | ~12k | — | `pytest tests/test_b1_validator.py -v` passes 4+ cases. Sample short PT paragraph scores `passed=True`. |
| TASK-02 | Translation prompt + schema + dispatcher | `pipeline/prompts/templates/s_translate_pt.xml.j2`, `pipeline/schemas/translation_pt.json`, `pipeline/llm.py` (add `dispatch_translate`), `pipeline/prompts/builder.py` (add `build_translate_pt_prompt`) | ~10k | — | Template renders, schema loads, `dispatch_translate` routes via `dispatch_structured(stage="revise")` cleanly, 2-3 few-shot examples present in template. |
| TASK-03 | s_translate_pt stage | `pipeline/stages/s_translate_pt.py`, `pipeline/context.py` (add PT fields), `tests/test_stages.py` (add `TestSTranslatePt`) | ~12k | TASK-01, TASK-02 | `python3 -c "from pipeline.stages.s_translate_pt import run; print('ok')"` works. Unit tests cover happy path, retry, b1_warning fallback. |
| TASK-04 | Wire stage into generate mode | `pipeline/modes/generate.py`, `pipeline/run_report.py` (note PT metric optionally) | ~5k | TASK-03 | `s_translate_pt.run(ctx)` called between `_review_loop(ctx)` and `s6_generate_tg.run(ctx)`. `python3 -m pipeline plan` still exits 0. |
| TASK-05 | Content migration script | `scripts/migrate_to_locale_dirs.py` | ~7k | — (independent of stages) | Script exits 0 on dry-run, real run moves all `content/*.md` to `content/<slug>/uk.md` via `git mv`. Re-run is no-op. |
| TASK-06 | s7_save dual-locale write | `pipeline/stages/s7_save.py` | ~6k | TASK-03, TASK-05 | Save writes `<slug>/uk.md` always; writes `<slug>/pt.md` if `ctx.article_text_pt`; commit picks up both. |
| TASK-07 | gatsby-node locale routing | `gatsby/gatsby-node.js`, `gatsby/src/i18n/uk.json`, `gatsby/src/i18n/pt.json` | ~10k | TASK-05 | Build emits `/uk/<slug>/` and `/pt/<slug>/`. No build error on slugs with only `uk.md` (PT skipped silently). |
| TASK-08 | Article template + index pages | `gatsby/src/templates/article.js`, `gatsby/src/pages/index.js`, `gatsby/src/pages/pt/index.js`, `gatsby/src/pages/uk/index.js` (or move `index.js` → `uk/index.js`) | ~12k | TASK-07 | `npm run build` exits 0. Hreflang link tags present. UI strings switch on locale. PT index lists only `lang=pt` articles. |
| TASK-09 | Sitemaps split + build | `gatsby/scripts/split-sitemaps.mjs`, `gatsby/package.json` (postbuild), `gatsby/gatsby-config.js` (sitemap plugin opts if needed) | ~6k | TASK-08 | After `npm run build`: `public/sitemap-uk.xml`, `public/sitemap-pt.xml`, `public/sitemap.xml` (index) all exist, well-formed XML. |
| TASK-10 | TG_CHANNEL_PT config + helper | `pipeline/config.py`, `pipeline/telegram.py` (add `send_photo_pt`/`send_text_pt` or unified arg), `tests/test_telegram.py` (clear-fail test) | ~5k | — | `TG_CHANNEL_PT_USERNAME = "pashtelka_pt"` set. Empty `TG_CHANNEL_PT_ID` raises a `RuntimeError` with operator-actionable text. |
| TASK-11 | s11_digest dual-language | `pipeline/stages/s11_digest.py`, `pipeline/schemas/digest_pt.json` (subset), `tests/test_stages.py` (`TestS11Digest` extended) | ~10k | TASK-02, TASK-10 | Digest run produces UA + PT captions, sends to both channels (PT skipped clearly when id empty). UA send unchanged in behaviour when `TG_CHANNEL_PT_ID` is empty. |
| TASK-12 | Operator backfill script | `scripts/backfill_pt.py` | ~6k | TASK-03, TASK-05 | Script imports cleanly, `--help` works, dry-run on one slug calls the stage and writes to the right path. NOT executed on the full corpus in this feature. |
| TASK-13 | Cost-warn + smoke test + done.md | `pipeline/llm.py` (add `_maybe_warn_translation_cost`), `pipeline/config.py` (add `TRANSLATION_COST_WARN_USD`), `.aidocs/in-progress/pt-translation-b1/done.md` | ~10k | TASK-01..TASK-12 | Warning fires above threshold. Smoke test on one real UA article succeeds: writes `pt.md`, `npm run build` produces `/pt/<slug>/`. `done.md` written, feature folder moves to `done/`. |

## Token budget

Total est. ≈ 111k. Breakdown weight is on the gatsby tasks (TASK-07,
TASK-08) and the stage + validator (TASK-01, TASK-03) — those are the
non-trivial logic surfaces.

## Out of scope (explicitly punted)

- Backfill of all 158 historic UA articles' PT versions (operator
  triggers `backfill_pt.py` after channel exists).
- ES / FR / EN locales — URL space reserved, no implementation.
- Live language switcher beyond the lang chip in the header.
- Translating the tag taxonomy (PT readers see UA-language tags for v1).
- PT-specific editorial plan / topic pool.
- Per-article quality A/B comparing translation engines.
- AI-translated audio / comments.
- Plausible PT analytics breakdown (single Plausible site, both locales).

## Rollback (full feature)

`git revert <feature-range>` removes:
- s_translate_pt stage (UA-only behaviour returns)
- /pt/ routes (Gatsby falls back to filtered UA-only)
- TG_CHANNEL_PT references (digest goes back to UA-only)

The content migration is *not* automatically reverted by `git revert` —
operator runs three commands per slug or restores from a pre-migration
git tag. Documented in `done.md`.

## Per-task rollback

Every task lists its own rollback line in its TASK file. Most are a
single `git revert <commit>` because changes are additive.
