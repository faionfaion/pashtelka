# Design: Bilingual Welcome Landing

**Implements:** spec.md
**Status:** todo
**Owner:** Ruslan

## High-level approach

Two static Gatsby pages plus one static redirect, no new runtime services, no
plugin installs. Everything reuses what is already in `package.json`
(`gatsby@5`, `gatsby-plugin-sharp`, `gatsby-transformer-sharp`,
`gatsby-source-filesystem`, `gatsby-plugin-sitemap`, `react@18`).

Welcome pages live alongside the existing UA site at the same root domain
(`pastelka.news`). The site stays UA-only at `/`; we do **not** restructure
existing routes into `/uk/`. We only add three new URLs:

| URL | Render | Source file |
|-----|--------|-------------|
| `/uk/welcome/` | Server-rendered React page | `gatsby/src/pages/uk/welcome.tsx` (or `.js`) |
| `/pt/welcome/` | Server-rendered React page | `gatsby/src/pages/pt/welcome.tsx` (or `.js`) |
| `/welcome/` | Static HTML with meta-refresh + JS lang detection | `gatsby/static/welcome/index.html` |

Pages use `.js` (project is JS-only today, no TS toolchain — adding TS would
balloon scope; spec lists `.tsx` as a suggestion, `.js` is acceptable).

## Page component tree

Each welcome page is intentionally minimal — no shared `<Layout>` wrapper from
`components/layout.js`. The site Layout pulls in the global `layout.css` (large
font import + article styles) which we don't need above-the-fold. Welcome
pages ship their own scoped styles inline via a small CSS module-style import,
keeping the critical-path CSS small.

```
WelcomePage (uk | pt)
├── <Helmet-like Head>          (Gatsby `Head` API: title, description, OG, Plausible <script>)
├── <header>                    (logo + small lang-switcher chip in the corner)
├── <main>
│   ├── <Hero>                  (one-sentence value prop + <picture> hero image)
│   ├── <WhatWeDo>              (three bullets)
│   ├── <CTAPrimary>            (TG button, fires Plausible event before redirect)
│   ├── <CTASecondary>          (link to / for UA, /pt/ for PT — falls back to / if /pt/ doesn't exist yet)
│   └── <Trust>                 (footer line: Editorial since 2026 • Ruslan • contact)
```

Single React file per locale. Components are inline functions inside the same
file; we don't extract them to `src/components/` because they have no other
caller.

## Routing approach

**Not** `createPage` in `gatsby-node.js`. We use Gatsby's filesystem-based
routing (`src/pages/uk/welcome.js` ⇒ `/uk/welcome/`). This keeps
`gatsby-node.js` untouched (it currently powers article + tag pages and we
don't want to risk regressing the news pipeline).

## Hero image strategy (placeholder)

Spec calls for a brand mascot (`gatsby/src/images/brand/pashtelka-mascot.png`)
designed in the separate `print-stickers-posters` feature. That feature has
not shipped. To unblock welcome-landing today:

1. Generate a **placeholder** hero via OpenAI `gpt-image-1` (same auth pattern
   as `pipeline/image_gen.py`). Save raw to
   `gatsby/src/images/welcome/hero-placeholder.png` (1024×1024 → cropped to
   ~3:2 for above-the-fold display).
2. Convert to AVIF + WebP + PNG (small, ≤80 KB above-the-fold) using `sharp`
   (already a transitive dep via `gatsby-plugin-sharp`). Output:
   - `gatsby/src/images/welcome/hero-placeholder.avif`
   - `gatsby/src/images/welcome/hero-placeholder.webp`
   - `gatsby/src/images/welcome/hero-placeholder.png` (raw)
3. Bundle the optimized variants as static assets the page imports directly,
   served from `/static/...` after build. Use `<picture>` with AVIF first,
   WebP second, PNG fallback. `loading="lazy"` is wrong here (above-the-fold
   on first paint) — use `loading="eager"` and `fetchpriority="high"`.
4. When the canonical mascot lands, swap the file at
   `gatsby/src/images/brand/pashtelka-mascot.png` and update the import path
   in both welcome pages. `done.md` documents this swap.

**Prompt for the placeholder** (English, sent to gpt-image-1 quality=auto,
1536×1024):

```
Friendly cartoon bird mascot, soft pastel colors with warm amber and cream
accent, clean flat illustration, large expressive eyes. Background: sunny
Lisbon street with azulejo tile pattern wall, yellow tram tracks, distant
silhouette of the 25 de Abril bridge across the Tagus. Daytime, soft golden
light. Friendly, welcoming, mobile-first composition, mascot centered, plenty
of negative space on the right for text overlay if needed. Style: modern flat
vector illustration, light texture, no photorealism, no text in the image.
```

Image budget: aim for ≤60 KB AVIF after `sharp` re-encode at 50% quality and
940px max width.

## Lang switcher

Tiny inline component:

```jsx
function LangSwitch({ to, label, flag }) {
  const onClick = (e) => {
    if (typeof window === "undefined") return;
    const search = window.location.search; // preserve ?utm_*
    if (search) { e.preventDefault(); window.location.href = to + search; }
  };
  return <a href={to} onClick={onClick} aria-label={label}>{flag} {label}</a>;
}
```

UA page links to `/pt/welcome/` (label "Português"). PT page links to
`/uk/welcome/` (label "Українська"). Click handler preserves UTM query params.

## `/welcome/` redirect

`gatsby/static/welcome/index.html` — pure static HTML, no React, no Gatsby
hydration. Gatsby's `static/` is rsynced to the public output unchanged.

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Pastelka.news — Welcome / Bem-vindo / Ласкаво просимо</title>
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="3;url=/uk/welcome/">
<link rel="canonical" href="https://pastelka.news/welcome/">
<style>body{font-family:system-ui,sans-serif;text-align:center;padding:40px 20px;color:#1a1a2e;background:#fefcfa}a{color:#d97706}</style>
</head>
<body>
<script>
  (function(){
    var langs = (navigator.languages || [navigator.language || "en"]).map(function(l){return (l||"").toLowerCase();});
    var pt = langs.some(function(l){return l.startsWith("pt");});
    var search = window.location.search || "";
    var dest = (pt ? "/pt/welcome/" : "/uk/welcome/") + search;
    window.location.replace(dest);
  })();
</script>
<p>Redirecting to <a href="/uk/welcome/">/uk/welcome/</a> …</p>
<p style="font-size:13px;color:#6b7280">
  Wrong language? <a href="/uk/welcome/">UA</a> · <a href="/pt/welcome/">PT</a>
</p>
</body>
</html>
```

JS path runs synchronously, redirects in ~1 frame. JS-disabled visitors fall
through to `<meta http-equiv="refresh">` (3s default to UA) + visible
"wrong language?" links. Total weight: ≤1.5 KB gzipped.

**Why not `gatsby-plugin-meta-redirect`?** Adds a dep + post-build pass; we
get the same outcome with one static HTML file.

## Plausible analytics

The site does **not** currently use Plausible. We add it **only on the two
welcome pages** (not site-wide — that's outside this feature's scope).

```html
<script defer data-domain="pastelka.news"
        src="https://plausible.io/js/script.tagged-events.outbound-links.js"></script>
```

Loaded via Gatsby `Head` API. ~1.3 KB gzipped, deferred — does not block
above-the-fold render. The `tagged-events` plugin lets us tag any element
with `class="plausible-event-name=welcome_tg_click"` and Plausible records the
click without manual JS.

Three events:

- `welcome_view` — fired on mount. Either rely on Plausible's auto-pageview
  (default) and rename via dashboard, OR fire manually via
  `window.plausible && window.plausible("welcome_view")` in a `useEffect`.
- `welcome_tg_click` — `<a class="plausible-event-name=welcome_tg_click">`.
  `outbound-links.js` already auto-fires for outbound clicks; the tagged-event
  variant gives us a stable name regardless of TG handle.
- `welcome_site_click` — same pattern, on the secondary CTA.

If Plausible domain `pastelka.news` is not configured in the operator's
Plausible workspace yet, events 404 silently — no breakage. `done.md`
documents the dashboard-side setup task.

## UTM passthrough

CTA primary URL is `https://t.me/pashtelka_news` (UA) /
`https://t.me/pastelka_pt` (PT). Telegram's deep-link `?start=` parameter
only accepts a short token (≤64 chars, alphanumeric + underscore), so we
cannot pass arbitrary UTM strings via `start`. Instead:

- The TG link itself stays clean: `https://t.me/pashtelka_news`.
- Plausible event `welcome_tg_click` captures the originating UTM via
  Plausible's built-in UTM parsing (Plausible auto-records `utm_source` /
  `utm_campaign` from the page URL on every event). Operator can then
  segment dashboard by `Source = sticker_lisboa`.
- Optional follow-up (out of scope for v1): if Telegram analytics needs
  per-sticker attribution, add a hashed token to `?start=`. Tracked as an
  open item in `done.md`.

## Open Graph / Twitter cards

Each page emits in `Head`:

```html
<meta property="og:title" content="...">
<meta property="og:description" content="...">
<meta property="og:image" content="https://pastelka.news/og/welcome-uk.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:type" content="website">
<meta property="og:url" content="https://pastelka.news/uk/welcome/">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://pastelka.news/og/welcome-uk.png">
```

OG images: 1200×630 PNG, generated via the same OpenAI flow (`quality=auto`,
size `1536x1024` cropped to 1200×630 with `sharp`). Saved under
`gatsby/static/og/welcome-uk.png` and `gatsby/static/og/welcome-pt.png`.
`gatsby/static/` is published verbatim, so the URLs are
`https://pastelka.news/og/welcome-uk.png` post-deploy.

OG image prompt (UA — Ukrainian text overlay at bottom-left, big and clean):

```
Banner-style illustration, 1200x630 wide, friendly pastel bird mascot on the
left third, sunny Lisbon street + azulejo tile + yellow tram + distant 25 de
Abril bridge in the background. Big bold Cyrillic Ukrainian text in the
bottom-left: "Новини Португалії українською". Warm amber + cream palette,
modern flat illustration, no photorealism. Text must be perfectly legible at
small thumbnail size.
```

PT variant: same composition, Latin text "Notícias de Portugal em ucraniano —
para a comunidade".

## Performance budget

| Asset | Target | Strategy |
|-------|--------|----------|
| HTML | ≤8 KB gzipped | Minimal markup, no `<Layout>` wrapper |
| Critical CSS | ≤4 KB gzipped | Inline page-scoped CSS, no Montserrat web font |
| JS | ≤30 KB gzipped | Gatsby chunk; defer plausible (~1.3 KB) |
| Hero image | ≤80 KB | AVIF first, ≤940px wide, q=50 |
| **Total above-the-fold** | **≤250 KB** | Verified via `du -b` on built assets |

System fonts (`system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
sans-serif`). Skip Montserrat — saves ~80 KB on first paint.

## File layout (final)

```
gatsby/
├── src/
│   ├── pages/
│   │   ├── index.js                       (unchanged)
│   │   ├── uk/
│   │   │   └── welcome.js                 (new)
│   │   └── pt/
│   │       └── welcome.js                 (new)
│   ├── components/
│   │   └── welcome.css                    (new — scoped to welcome pages)
│   └── images/
│       └── welcome/
│           ├── hero-placeholder.png       (new — raw, 1024+ wide)
│           ├── hero-placeholder.avif      (new — encoded)
│           └── hero-placeholder.webp      (new — encoded)
├── static/
│   ├── welcome/
│   │   └── index.html                     (new — redirect)
│   └── og/
│       ├── welcome-uk.png                 (new — 1200×630)
│       └── welcome-pt.png                 (new — 1200×630)
└── scripts/
    └── gen-welcome-assets.mjs             (new — one-shot OpenAI + sharp pipeline)
```

`gen-welcome-assets.mjs` is committed (one-shot, idempotent — re-running
overwrites). Documented in `test-plan.md` so it can be re-executed when the
canonical mascot replaces the placeholder.

## Decisions

- **Locale strategy:** keep root unchanged. Add only `/uk/welcome/`,
  `/pt/welcome/`, `/welcome/`. Restructuring the whole site to `/uk/` is a
  separate feature with non-trivial SEO + redirect work.
- **No `gatsby-plugin-image`** — adds 100+ KB of Gatsby build machinery and a
  GraphQL refactor. We pre-generate AVIF/WebP/PNG with `sharp` directly.
- **No `gatsby-plugin-meta-redirect`** — one static HTML file is simpler.
- **No web fonts on welcome pages** — `system-ui` stack only.
- **Placeholder mascot** — generated via OpenAI today; canonical mascot path
  documented for `print-stickers-posters` to swap in later.
- **Plausible only on welcome pages** — site-wide rollout is out of scope.
- **PT TG handle `@pastelka_pt`** — channel doesn't exist yet; link will 404
  gracefully (TG shows "Channel not found"). Operator creates the channel as
  part of the Lisbon launch.
