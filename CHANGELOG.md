# Changelog

All notable changes to the pashtelka pipeline are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/) and the
project uses semantic-ish versioning loosely — one logical change per commit
(see ~/workspace/AGENTS.md for the conventions).

## [Unreleased]

### Added
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
