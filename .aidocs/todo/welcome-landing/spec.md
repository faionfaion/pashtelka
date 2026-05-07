# Spec: Bilingual Welcome Landing Page

**Status:** backlog
**Owner:** Ruslan
**Created:** 2026-05-06

## Goal

Two short single-purpose pages — `/uk/welcome/` and `/pt/welcome/` — that introduce pashtelka.news to a first-time visitor in 10 seconds and convert them to a Telegram subscriber or site reader. These URLs are printed as QR codes on stickers/posters distributed in Lisbon, so they must:

- load fast on mobile over weak Wi-Fi/3G,
- look good on a 360px-wide screen,
- give one clear next action.

## Users

- Person who scans a QR code on a sticker / poster in Lisbon. Their first contact with the brand. Target: 1 of 4 of them join the TG channel or bookmark the site.

## Acceptance Criteria

### AC1 — Two locale routes
- `/uk/welcome/` — Ukrainian copy.
- `/pt/welcome/` — Portuguese copy (B1, same constraints as `pt-translation-b1` feature).
- Each renders independently — both are standalone landing pages, not language switchers on a single page.
- Each has a small "🇺🇦 / 🇵🇹" link in the corner that swaps to the other locale (preserving any `?utm` params).

### AC2 — Content blocks per page
1. **Hero** — one-sentence value prop ("Новини Португалії українською, без води" / equivalent PT B1).
2. **What we do** — 3 short bullets: daily news, weekly guides, immigration-tracker.
3. **CTA primary** — TG button: UA page → @pashtelka_news, PT page → @pastelka_pt.
4. **CTA secondary** — link to `/uk/` or `/pt/` (latest articles).
5. **Trust** — small footer: "Editorial since 2026 • Ruslan • contact email".

### AC3 — Mobile-first design
- Renders cleanly at 360×640 (smallest realistic Lisbon-Android target).
- Hero image present but lazy, AVIF + WebP fallback, ≤ 80KB above-the-fold.
- Total page weight (HTML + CSS + critical JS + hero image) ≤ 250KB.
- Lighthouse Performance ≥ 90 on 4G throttled, mobile.

### AC4 — Open Graph & sharing
- OG title, description, image set per locale.
- OG image dimensions: 1200×630 PNG, brand-coloured, includes the same hero artwork as the page.
- Twitter card `summary_large_image`.
- Telegram link preview validates (test with t.me/iv?url=...).

### AC5 — UTM-ready
- Page accepts `?utm_source=sticker_lisboa&utm_campaign=2026-q2` and similar without breaking.
- Outbound TG button preserves utm params as query params on `t.me/pashtelka_news?start=<utm_source>` if Telegram's deep-link supports it; otherwise log via Plausible event before redirect.

### AC6 — No tracking pixels beyond Plausible
- Plausible event "welcome_view" on load, "welcome_tg_click" / "welcome_site_click" on CTA tap.
- No Google Analytics, no Meta Pixel.

### AC7 — Build & deploy
- Two new pages under `gatsby/src/pages/uk/welcome.tsx` and `gatsby/src/pages/pt/welcome.tsx`, OR templates if it's cleaner with the existing routing scheme.
- Deploys via the standard `deploy-gh.sh`.
- Live at production after merge.

### AC8 — Anti-link-rot
- The pages also resolve at the redirected `/welcome/` (browser `Accept-Language` decides which locale to redirect to). Stickers can carry the shorter `/welcome/` URL if a typesetter prefers it.
- 404 on either page → automatic Telegram alert via existing pipeline notification path.

## Out of Scope

- Form-based signups (email capture, etc.) — TG and direct-site reads are the only success metrics for v1.
- A/B variants of the hero copy.
- A separate "thank you" page after CTA click.
- Branded short domain (e.g., `pshtl.com`) — `pastelka.news/welcome/` is short enough.

## Decisions

- **Hero artwork:** new pashtelka-specific mascot. Generated once via OpenAI iterative reviewer loop (same flow as `print-stickers-posters`). Mascot reference saved at `gatsby/src/images/brand/pashtelka-mascot.png` and reused on welcome page, stickers, posters, and digest images going forward.
- **PT channel handle:** `@pastelka_pt`.

## Open Questions

- Should the page detect the visitor's locale and auto-redirect from `/welcome/` to `/uk/welcome/` or `/pt/welcome/`? Default: yes, with a small "wrong language? click here" link.
