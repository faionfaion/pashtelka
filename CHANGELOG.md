# Changelog

All notable changes to the pashtelka pipeline are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/) and the
project uses semantic-ish versioning loosely — one logical change per commit
(see ~/workspace/AGENTS.md for the conventions).

## [Unreleased]

### Added
- `.aidocs/todo/print-stickers-posters/{design,test-plan,implementation-plan}.md`
  + 11 `tasks/todo/TASK-*.md` stubs — SDD planning for the Lisbon
  street-distribution print campaign (75 mm round sticker + A5 portrait
  poster). Two-phase rollout: Phase 4a builds infra + first mascot draft,
  Phase 4b iterates the mascot to operator approval and ships final
  Affinity-exported PDFs. [print-stickers-posters TASK-01]
- `scripts/print/generate_qr.py` — QR code generator for sticker / poster
  print assets. `qrcode` lib at error-correction `H`, emits both raster
  PNG and vector SVG (preferred for Affinity Publisher import).
  [print-stickers-posters TASK-03]
- `qrcode[pil]>=7.4` declared in `requirements.txt`.
  [print-stickers-posters TASK-03]
- `scripts/print/generate_mascot.py` — OpenAI `gpt-image-1.5` (with
  `gpt-image-1` fallback) wrapper for the canonical pashtelka mascot.
  Stdlib only (urllib + multipart). Two modes: fresh
  `/v1/images/generations` (v1) and iterative `/v1/images/edits` with a
  reference PNG (v2+). [print-stickers-posters TASK-04]
- `scripts/print/svg_to_cmyk_pdf.py` — SVG → CMYK proofing PDF tool. Path
  1: Inkscape + ghostscript with FOGRA39 ICC. Path 2: cairosvg + PIL
  CMYK + reportlab fallback (proofing only, no ICC gamut mapping). If
  neither is installed, exits with the documented install hint.
  [print-stickers-posters TASK-05]
- `assets/print/sticker.svg` — 75 mm round sticker layout source
  (81×81 mm artboard with 3 mm bleed). Named placeholder layers for
  Affinity Publisher import. [print-stickers-posters TASK-06]
- `assets/print/poster_a5.svg` — A5 portrait poster layout source
  (154×216 mm artboard, 3 mm bleed). UA + PT headlines + bullets baked
  in. [print-stickers-posters TASK-06]
- `assets/print/README.md` — operator handoff: print specs, paper recs,
  Affinity Publisher import procedure (PDF/X-1a:2003 + FOGRA39 + 300
  DPI), QR + mascot generation commands, print-shop candidates.
  [print-stickers-posters TASK-06]
- `assets/print/prompts/mascot-v1.txt` — first OpenAI prompt for the
  canonical pashtelka mascot (~280 words, bird-shaped, pastel palette,
  Lisbon-coded surroundings). [print-stickers-posters TASK-07]
- `gatsby/src/images/brand/pashtelka-mascot.png` — mascot v1 draft
  (1024×1024 RGBA PNG, generated via OpenAI `gpt-image-1.5`). Pending
  operator approval before Phase 4b finalises the print PDFs and the
  welcome-page hero swap. [print-stickers-posters TASK-07]
- `assets/print/prompts/mascot-v2.txt` — corrected mascot prompt: the
  pastel de nata IS the character (face drawn on the custard surface),
  not a separate creature holding a tart. Comic-book Pashtelka News
  house style, no Lisbon scene around it (clean cut-out subject).
  Replaces the v1 anthropomorphic-bird misread. Approved as canonical
  brand mascot v2. [print-stickers-posters TASK-08]
- `pipeline/b1_validator.py` — sync B1 readability validator. Three
  metrics (Flesch reading ease via textstat, avg sentence length, B1
  lemma coverage) return `passed` flag + `retry_addendum` for prompt
  retry. Strips markdown markup; rule-based PT lemmatiser folds common
  inflections so the 3000-lemma list covers more surface forms.
  [pt-translation-b1 TASK-01]
- `pipeline/data/pt_b1_lemmas.txt` — 3000 top PT lemmas from
  OpenSubtitles 2018 50k frequency list. [pt-translation-b1 TASK-01]
- `tests/test_b1_validator.py` — 15 cases across basics, markdown
  stripping, retry addendum, sentinels. All green.
  [pt-translation-b1 TASK-01]
- `textstat>=0.7.4` declared in `requirements.txt`.
  [pt-translation-b1 TASK-01]
- `pipeline/prompts/templates/s_translate_pt.xml.j2` — UA→PT B1
  translation prompt with five rule blocks (tenses, sentence length,
  vocabulary, proper nouns / numbers / dates, tone, structure) and
  three few-shot examples (lede, 3-item list, idiom flattened).
  [pt-translation-b1 TASK-02]
- `pipeline/schemas/translation_pt.json` — title/description/article
  required, optional summary. [pt-translation-b1 TASK-02]
- `pipeline.llm.dispatch_translate(prompt, *, system, schema, lang)` —
  PT-only v1, routes via `dispatch_structured(stage="revise")` so
  LLM_STACK toggle drives translation too. Soft cost-warn after each
  call. [pt-translation-b1 TASK-02]
- `TRANSLATION_COST_WARN_USD`, `TG_CHANNEL_PT_USERNAME`,
  `TG_CHANNEL_PT_ID` env-driven knobs in `pipeline/config.py`.
  [pt-translation-b1 TASK-02]
- `pipeline/prompts/templates/s11_digest_translate_pt.xml.j2` — PT
  digest translation template (used in TASK-11).
  [pt-translation-b1 TASK-02]
- `tests/test_llm.py` — +4 cases for dispatch_translate routing /
  rejection / cost-warn fires / cost-warn silent. 20/20 green.
  [pt-translation-b1 TASK-02]
- `pipeline/stages/s_translate_pt.py` — UA→PT B1 translation stage.
  `run(ctx)` pipeline entry + `translate_one_file(path)` standalone
  helper. Routes through `dispatch_translate` (not `pipeline.sdk`),
  validates with `b1_validate`, retries once with addendum on failure,
  ships with `b1_warning: true` if both attempts fail.
  [pt-translation-b1 TASK-03]
- `PipelineContext` PT fields: `article_text_pt`, `title_pt`,
  `description_pt`, `summary_pt`, `b1_metrics`, `b1_warning`.
  [pt-translation-b1 TASK-03]
- `tests/test_stages.py::TestSTranslatePt` — 6 cases (dispatcher call
  shape, ctx mutation, retry-with-addendum, b1_warning on double
  failure, empty-body guard, file roundtrip). 6/6 green.
  [pt-translation-b1 TASK-03]

### Changed
- `pipeline/modes/generate.py` — `s_translate_pt.run(ctx)` now runs
  between the revise loop and TG-caption generation in
  `_generate_one_article`. Translation duration captured in the run
  report. Translation failure aborts the article (avoids asymmetric
  UA-only shipping). [pt-translation-b1 TASK-04]
- `content/` layout migrated from flat `<slug>.md` to nested
  `<slug>/uk.md` for 158 articles. Per-locale dirs let
  `s_translate_pt` write `<slug>/pt.md` alongside the UA original.
  Renames preserved via `git mv` so file history follows.
  Migration script `scripts/migrate_to_locale_dirs.py` is idempotent
  and re-runnable. [pt-translation-b1 TASK-05]

### Added (TASK-05)
- `scripts/migrate_to_locale_dirs.py` — one-shot migration helper.
  `--dry-run` preview + live mode. Uses `git mv` with
  `shutil.move` fallback. [pt-translation-b1 TASK-05]

### Changed (TASK-05 migration result)
- 158 articles relocated from `content/<slug>.md` to
  `content/<slug>/uk.md` via the migration script. Pure renames, zero
  body changes. [pt-translation-b1 TASK-05]
- `pipeline/stages/s7_save.py` — writes per-locale markdown into
  `content/<slug>/uk.md` (always) and `content/<slug>/pt.md` (when
  `ctx.article_text_pt`). Frontmatter builder extracted to
  `_build_md(ctx, *, lang, date_str)`. Git commit message reads
  `content: <slug> [uk]` or `[uk+pt]`. Per-locale teaser URL bumped
  to `/uk/<slug>/`. PT frontmatter adds `b1_warning: true` only when
  the validator failed twice. [pt-translation-b1 TASK-06]
- `tests/test_stages.py::TestS7Save` — 3 existing tests updated for
  nested layout, 3 new cases for dual-locale write + b1_warning
  flag. 10/10 green. [pt-translation-b1 TASK-06]
- `gatsby/gatsby-node.js` — locale-aware page creation. Articles
  build at `/uk/<slug>/` and `/pt/<slug>/` (where the PT variant
  exists). Per-locale prev/next pagination. Tag pages stay flat with
  UA tags only for v1. [pt-translation-b1 TASK-07]
- `gatsby/src/i18n/{uk,pt}.json` — 10 UI strings per locale.
  [pt-translation-b1 TASK-07]
- `gatsby/src/templates/article.js` — locale-aware. GraphQL filters
  by slug AND lang. Hreflang triplet (uk + pt-when-available +
  x-default), per-locale OG, canonical, html lang.
  [pt-translation-b1 TASK-08]
- `gatsby/src/components/layout.js` — accepts `lang` /
  `otherLocaleHref` props. Header lang-chip switches to the other
  locale. Footer + sitemap link + TG handle adapt per locale.
  [pt-translation-b1 TASK-08]
- `gatsby/src/pages/{uk,pt}/index.js` — explicit per-locale homepages.
  Root `/` keeps serving UA-default with hreflang triplet.
  [pt-translation-b1 TASK-08]
- `gatsby/src/components/layout.css` — `.site-lang-chip`,
  `.empty-state`, header `position: relative` for chip anchoring.
  [pt-translation-b1 TASK-08]
- One sample PT article at
  `content/aima-deadline-passed-april-16-day-after-checklist/pt.md`
  used to verify dual-locale build (smoke test for TASK-13 reuses).
  [pt-translation-b1 TASK-08]
- `gatsby/scripts/split-sitemaps.mjs` post-build splitter. Writes
  `public/sitemap-uk.xml`, `public/sitemap-pt.xml`, and the
  `public/sitemap.xml` index referencing both. Wired via
  `gatsby/package.json` `postbuild` hook. [pt-translation-b1 TASK-09]
- `pipeline.telegram.require_pt_channel_id()` — clear-fail helper.
  Returns `TG_CHANNEL_PT_ID` when set, raises `RuntimeError` with an
  operator-actionable message otherwise. Tests in
  `tests/test_telegram.py::TestRequirePtChannelId`. 19/19 telegram
  tests green. [pt-translation-b1 TASK-10]
- `pipeline/stages/s11_digest.py` — dual-language digest. UA send
  unchanged; when `TG_CHANNEL_PT_ID` is set, the same image is sent
  with a PT-translated caption to `@pastelka_pt`. PT failures
  isolated — UA always wins. `_translate_digest_to_pt`,
  `_build_caption(*, lang)`, schema-validated digest_pt output.
  [pt-translation-b1 TASK-11]
- `pipeline/schemas/digest_pt.json` — subset schema for the PT digest
  payload (intro + items only). [pt-translation-b1 TASK-11]
- `tests/test_stages.py::TestS11DigestDualLang` — 5 cases (UA/PT
  caption shape, translate helper routing, dual-send happy path,
  empty-id skip). 5/5 green. [pt-translation-b1 TASK-11]
- `scripts/backfill_pt.py` — operator-triggered helper. Iterates
  `content/<slug>/uk.md` and calls the translation stage for each
  slug that has no `pt.md` sibling. Scope flags: `--all`,
  `--since YYYY-MM-DD`, `--slug <slug>`. `--dry-run` previews;
  `--max N` is a safety net. Late import of the stage helper keeps
  `--help` cheap. [pt-translation-b1 TASK-12]

### Notes
- `pt-translation-b1` feature shipped: see
  `.aidocs/done/pt-translation-b1/` for spec, design, test plan,
  implementation plan, 13 task reports, and `done.md` (env-var
  contract + rollback + operator follow-ups).
- B1 validator thresholds (`FLESCH_MIN=65`, `AVG_SENT_WORDS_MAX=20`,
  `COVERAGE_MIN_PCT=90`) are deliberately conservative for v1.
  Operator should tune them after observing 50+ real pipeline
  translations; documented in `done.md`.
- PT TG channel `@pastelka_pt` must be created by the operator and
  `TG_CHANNEL_PT_ID` exported in `~/workspace/.env` on faion-net
  before the digest cron picks up the dual-language flow.
- 157 historic UA articles do NOT have PT counterparts yet — operator
  triggers `scripts/backfill_pt.py` after the live pipeline is
  healthy.
- SDD plan for `pt-translation-b1`: simplified Portuguese (CEFR B1)
  translation pipeline + `/pt/` site routing + `@pastelka_pt` TG channel
  + dual-language daily digest. Plan covers 13 atomic tasks, content
  migration to `content/<slug>/{uk,pt}.md`, Flesch + lemma B1 validator,
  cost guardrails. [pt-translation-b1]
- SDD plan for `welcome-landing` feature: bilingual `/uk/welcome/` +
  `/pt/welcome/` landing pages, `/welcome/` redirect, OG cards, hero
  placeholder. Docs: `design.md`, `test-plan.md`, `implementation-plan.md`,
  7 task stubs. [welcome-landing]
- `gatsby/src/components/welcome.css` page-scoped stylesheet for the
  welcome landing pages (system fonts, ~2 KB minified, no global leak).
  Plus scaffold dirs under `gatsby/src/images/welcome/`,
  `gatsby/static/welcome/`, `gatsby/static/og/`, `gatsby/scripts/`.
  [welcome-landing TASK-01]
- `gatsby/scripts/gen-welcome-assets.mjs` — one-shot ESM generator using
  OpenAI gpt-image-1 + sharp to produce hero AVIF/WebP/PNG variants and
  the OG cards. Sub-commands: `hero | og-uk | og-pt | all`. Idempotent.
- Hero placeholder under `gatsby/src/images/welcome/hero-placeholder.{png,
  webp, avif}` (940×940, AVIF 16.6 KB). Will be swapped for the canonical
  mascot from `print-stickers-posters` later. [welcome-landing TASK-02]
- OG cards `gatsby/static/og/welcome-uk.png` and `welcome-pt.png`, both
  exactly 1200×630 PNG, ~450 KB each. Generated via the same
  `gen-welcome-assets.mjs` script. [welcome-landing TASK-03]
- UA welcome page `gatsby/src/pages/uk/welcome.js` → `/uk/welcome/`. Hero
  + 3 bullets + TG primary CTA (@pashtelka_news) + secondary CTA + trust
  footer. Open Graph + Twitter card + Plausible (tagged-events) wired in
  the `Head` export. Lang chip preserves UTM search params. Above-the-fold
  weight 249 KB uncompressed (≤ 250 KB AC3 budget). [welcome-landing
  TASK-04]
- PT welcome page `gatsby/src/pages/pt/welcome.js` → `/pt/welcome/`. Same
  structure as UA, B1-level Portuguese copy, `@pastelka_pt` handle,
  `welcome-pt.png` OG card. [welcome-landing TASK-05]
- `/welcome/` static redirect (`gatsby/static/welcome/index.html`, 1.3 KB).
  Three layers: navigator.languages JS → meta-refresh fallback → visible
  UA/PT links. Preserves UTM search params on redirect. `noindex`.
  [welcome-landing TASK-06]

### Notes
- `welcome-landing` feature shipped: see `.aidocs/done/welcome-landing/`
  for spec, design, test plan, implementation plan, 7 task reports, and
  `done.md` (rollback + mascot-swap path + operator follow-ups).
  Lighthouse mobile-perf run is deferred to the operator (no Chrome in
  build sandbox). Hero image is a placeholder; canonical mascot lives at
  `gatsby/src/images/brand/pashtelka-mascot.png` once
  `print-stickers-posters` ships.
- LLM dispatcher module `pipeline/llm.py` with three backends:
  Gemini 2.5 Flash (web-search grounded research), Codex CLI gpt-5.5
  (generation/revision/TG/digest), Claude Opus (review).
  [pipeline-gemini-codex]
- Feature flag `LLM_STACK={old,new}` (default `old`). Flip to `new` once
  AC5+AC6 bench shows cost reduction without quality regression.
- Pre-flight startup check verifies `codex` CLI and `GEMINI_API_KEY` when
  `LLM_STACK=new`; exits 2 with an actionable error otherwise.
- `--bench` flag on `python3 -m pipeline generate` produces
  `state/bench/<date>.json` with old-vs-new latency and cost comparison.
- Per-vendor model overrides via env: `GEMINI_MODEL`, `CODEX_MODEL`,
  `CLAUDE_MODEL`. Per-vendor timeouts: `GEMINI_TIMEOUT`, `CODEX_TIMEOUT`.
  `CODEX_BIN` for non-default codex install paths.
- Unit tests `tests/test_llm.py` covering routing, command shape,
  schema-validation rejection, and retry-on-transient.

### Changed
- Stages s2/s3/s5/s6/s11 now call `pipeline.llm.dispatch_*` instead of
  `pipeline.sdk` directly. Behavior identical when `LLM_STACK=old`.
- `tests/test_stages.py` mocks for migrated stages updated to target the
  dispatcher API.
- `requirements.txt` declares `jsonschema>=4.0.0` (was transitively present).

### Notes
- Review stage (s4) and editorial planning (s0) intentionally remain on
  Claude Opus (AC3 + s0 not in AC2 scope).
- Rollback: `unset LLM_STACK` (or `export LLM_STACK=old`) — single env-var
  flip, no code change.
