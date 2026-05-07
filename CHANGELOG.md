# Changelog

All notable changes to the pashtelka pipeline are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/) and the
project uses semantic-ish versioning loosely — one logical change per commit
(see ~/workspace/AGENTS.md for the conventions).

## [Unreleased]

### Added
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
