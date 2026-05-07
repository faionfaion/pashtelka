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
