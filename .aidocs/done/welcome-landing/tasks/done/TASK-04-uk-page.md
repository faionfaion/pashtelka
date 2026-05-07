# TASK-04 — UA welcome page

**Subject:** Build `gatsby/src/pages/uk/welcome.js` end-to-end: header +
hero + bullets + CTAs + trust footer + Plausible + OG meta.

## Files touched

- `gatsby/src/pages/uk/welcome.js` (new)

## Approach

Single React functional component — no shared `<Layout>`. Imports
`welcome.css` and the three hero variants. `<picture>` element with
AVIF/WebP/PNG sources.

CTAs:

- Primary: `<a class="cta-primary plausible-event-name=welcome_tg_click"
  href="https://t.me/pashtelka_news" rel="noopener">…</a>`
- Secondary: `<a class="cta-secondary plausible-event-name=welcome_site_click"
  href="/">…</a>`

Lang switcher: top-right, links to `/pt/welcome/`, JS handler preserves
search string.

`useEffect` fires `window.plausible && window.plausible("welcome_view")`
on mount.

`Head` API:

- `<title>` Ukrainian
- meta description, lang="uk"
- OG title/description/image/url + twitter:card summary_large_image
- Plausible script tag (deferred)
- canonical link

## Copy (UA)

- Hero: "Новини Португалії українською, без води."
- Sub: "10 секунд — і ти в курсі, що відбувається там, де ти живеш."
- Bullets:
  - "Щодня — головні новини Португалії: коротко, ясно."
  - "Щотижня — гайди для життя: податки, AIMA, школи, медицина."
  - "Імміграційний трекер: дедлайни, штрафи, апеляції."
- CTA primary: "Підписатися в Telegram → @pashtelka_news"
- CTA secondary: "Читати останні статті →"
- Trust: "Редакція з 2026 • Руслан • hello@pastelka.news"

## Success criterion

- `npm run build` produces `public/uk/welcome/index.html`.
- AC1, AC2, AC4, AC5, AC6 grep tests in `test-plan.md` pass for `/uk/welcome/`.
- `view-source` shows: `lang="uk"`, OG meta tags, Plausible script,
  `plausible-event-name=welcome_tg_click` class, `plausible-event-name=
  welcome_site_click` class.

## Execution Report

### Status: COMPLETED

### What Was Done
- Wrote `gatsby/src/pages/uk/welcome.js` — single React component, no shared `<Layout>`. Imports the three hero variants + `welcome.css`. `<picture>` with AVIF → WebP → PNG fallback chain. CTAs use `class="… plausible-event-name=welcome_*_click"` for tagged-events.
- `Head` exports the full Open Graph + Twitter card meta + canonical + hreflang alternates + Plausible script (deferred). Plausible is `script.tagged-events.outbound-links.js` so it auto-fires on outbound TG click without manual JS.
- `useEffect` fires `window.plausible("welcome_view")` on mount when Plausible is present (defensive: no-op without it).
- Lang switcher: top-right chip linking to `/pt/welcome/`. Click handler appends `window.location.search` if present (preserves UTMs).

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `gatsby/src/pages/uk/welcome.js` | new (~120 lines) |

### Tests
Build:
- `npm run build`: PASS (20.3s, route `/uk/welcome/` listed under "Pages").
- `public/uk/welcome/index.html` exists (16.7 KB).

Grep matrix (all expected ≥1):
- `lang="uk"`: 1 — PASS
- `t.me/pashtelka_news`: 1 — PASS
- `plausible-event-name=welcome_tg_click`: 1 — PASS
- `plausible-event-name=welcome_site_click`: 1 — PASS
- `plausible.io/js/script`: 1 — PASS
- `og:image`: 1 (plus `og:image:width`, `og:image:height`)
- `twitter:card summary_large_image`: 1 — PASS
- `href="/pt/welcome/"`: 1 (lang switcher) — PASS
- `Редакція з 2026`: 1 — PASS

Above-the-fold weight (HTML + 3 JS chunks + global CSS + AVIF hero), measured via curl on `gatsby serve`:
- HTML: 16 773 B
- `app.js`: 59 390 B
- `framework.js`: 140 311 B
- `webpack-runtime.js`: 4 806 B
- `styles.972d…css`: 10 824 B
- AVIF hero: 17 047 B
- **Total: 249 151 bytes** — under the 250 KB budget by 849 bytes (uncompressed). Real-world over the wire (gzip on nginx) ~75-90 KB.

UTM passthrough sanity:
- `curl 'http://localhost:9000/uk/welcome/?utm_source=sticker_lisboa&utm_campaign=2026-q2'` returns the page cleanly with both CTAs intact.

### Issues
- Gatsby's global CSS bundling pulls in `layout.css` from the rest of the site (Montserrat web-font import is in there). The welcome page's own `.wl-page` selectors override `font-family` to system fonts, so the Montserrat font does NOT block first paint and the welcome page renders in system fonts immediately. Browser may still fetch Montserrat asynchronously — this is invisible to AC3 (above-the-fold) but technically wastes bandwidth on welcome pages. Removing the global Montserrat import would change every other page on the site, so it's out of scope. Documented for follow-up.
