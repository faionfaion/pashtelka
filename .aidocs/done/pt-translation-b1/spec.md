# Spec: Portuguese Translation (B1-Level) + Site + TG Channel

**Status:** backlog
**Owner:** Ruslan
**Created:** 2026-05-06

## Goal

Make every pashtelka article available in **simplified Portuguese (max CEFR B1)**, on a `/pt/` site path and in a dedicated PT Telegram channel. Target audience: Portuguese-speaking readers who want concise, accessible local + EU news; secondary audience: Ukrainian diaspora practising Portuguese.

## Users

- **Native PT readers** — Lisbon residents, Portuguese-speaking immigrants from Brazil/Angola, language teachers looking for clean reading material. They get short, simple, daily news updates.
- **UA diaspora learning PT (B1-target)** — same articles in clean B1 language they can actually read.
- **Pipeline operator** — single editorial plan still drives both languages; PT is a translation pass, not a separate generation.

## Acceptance Criteria

### AC1 — Translation pipeline stage
- New stage `pipeline/stages/s_translate_pt.py` runs after `s5_revise.py` and before `s7_save.py`.
- For every article (news, material, guide) the stage produces a PT version saved as `content/<slug>/pt.md` (alongside existing `content/<slug>/uk.md` after the path migration in AC2).
- Translation engine: Codex CLI (gpt-5.5) using a dedicated B1 prompt (see AC4).
- Translation preserves: structure (headings, lists, code blocks, links, frontmatter), proper nouns, numbers, dates.
- Frontmatter `lang: pt` added; `title`, `description`, `summary` translated; `slug` shared with UA version.

### AC2 — Content directory migration
- `content/<slug>.md` → `content/<slug>/uk.md` + `content/<slug>/pt.md`.
- One-shot migration script: `scripts/migrate_to_locale_dirs.py`.
- All existing articles migrate to UA path; PT versions backfilled in a separate batch pass (off-peak run, non-blocking).

### AC3 — B1 readability validator
- After translation, an automated check rejects PT output that fails B1 metrics:
  - **Flesch reading-ease (PT-adapted)** ≥ 65 — using `textstat` or equivalent.
  - **Average sentence length** ≤ 20 words.
  - **Vocabulary**: ≥ 90% of word lemmas appear in a B1 frequency wordlist (we ship `pipeline/data/pt_b1_lemmas.txt` from a public source like OpenSubtitles freq list, top ~3000 lemmas).
- On failure: stage retries once with a "simplify further" prompt addendum. After 2nd failure: logs warning, ships PT article anyway with `b1_warning: true` frontmatter flag for monitoring.

### AC4 — B1 translation prompt
- New prompt template `pipeline/prompts/templates/s_translate_pt.xml.j2` with rules:
  - "Use only present, past, and future simple. Avoid subjunctive except `que + presente`. Avoid composite tenses except `ter + particípio passado` for recent past."
  - "Replace idioms with literal equivalents."
  - "Sentence length max 20 words. Break long UA sentences into 2-3 PT sentences."
  - "Keep proper nouns, dates, numbers, place names exactly. Translate organisation names where standard PT version exists (NATO → OTAN), keep transliteration otherwise."
  - "Tone is neutral-friendly. No UA-insider asides ('у нас', 'як ми звикли') — the article must read as if written for an outside reader. Editorial position belongs in bylines, not body."
- Prompt includes 2-3 few-shot examples from manually translated reference articles.

### AC5 — Gatsby `/pt/` routing
- Site routes:
  - `pastelka.news/uk/<slug>/` (UA, current default moves under `/uk/`)
  - `pastelka.news/pt/<slug>/`
  - `pastelka.news/` redirects to `/uk/` (browser `Accept-Language: pt*` → `/pt/`)
- Templates in `gatsby/src/templates/` render based on locale.
- UI strings (nav, footer, "read also", search) translated for PT — keep in `gatsby/src/i18n/{uk,pt}.json`.
- Sitemaps split: `sitemap-uk.xml` + `sitemap-pt.xml`, referenced from `sitemap.xml` index.
- Hreflang link tags between UA/PT versions on every article.

### AC6 — New TG channel for PT
- Channel handle: **`@pashtelka_pt`** (mirror of UA brand for both audiences).
- Bot: `@nero_open_bot` (shared) added as admin.
- Channel chat_id added to `pipeline/config.py` as `TG_CHANNEL_PT`.
- Avatar + bio set up in PT (mirrors UA channel intent).
- Pinned welcome post links to `/pt/welcome` (see `welcome-landing` feature).

### AC7 — Daily digest in PT
- `pipeline/stages/s11_digest.py` extended to produce two digests (UA + PT) using PT translations of the day's headlines.
- One digest image per language? **No** — same image, only caption translated. Image is mostly visual; UA-text overlays stay UA (rationale: image is brand mark, both audiences see same image; cost saving). Revisit if PT readership ≥ 1k.
- Digest publishing: parallel send to both channels, same cron `0 20 * * *`.

### AC8 — Editorial plan unchanged
- Plans in `state/plans/` stay UA-side. Translation is mechanical post-process.
- Cross-references (follow-up linking) work in both locales via shared slugs.

### AC9 — Cost guardrails
- PT translation adds N translation calls per day (1 per article + 1 per digest).
- Estimated cost ceiling: keep total daily LLM spend within 1.5× of UA-only baseline. Fail loudly if exceeded.

## Out of Scope

- v1 stays at static /pt/ pages built on each generate. No live language switcher beyond a small dropdown linking to the matching `/uk/` or `/pt/` URL.
- Non-PT/UA locales (ES, FR, EN) — out of scope for v1; route structure leaves space.
- AI-translated comments/audio.
- Per-article quality A/B comparing translation engines.

## Decisions

- **PT channel name:** `@pashtelka_pt` (decided 2026-05-07).
- **Target audience:** both equal weight — native PT speakers AND UA diaspora practising PT. B1 constraint serves both. Tone neutral-friendly, no insider UA framing in body copy; UA framing only in editorial bylines / about page.

## Open Questions

- Should we drop the `b1_warning: true` flag and just hard-block publication on failure? Default: warn, ship — quantity beats perfect at v1.
