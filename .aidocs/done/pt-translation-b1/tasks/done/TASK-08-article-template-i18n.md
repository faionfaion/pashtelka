# TASK-08 — Article template locale-aware + index pages

**Subject:** Make the article template use `pageContext.lang` for date
formatting, UI strings, and hreflang link tags. Add a PT index page
listing PT articles. Restructure the root index to filter UA-only and
add a lang chip to switch.

## Files touched

- `gatsby/src/templates/article.js`
- `gatsby/src/pages/index.js` (filter to UA, lang chip)
- `gatsby/src/pages/pt/index.js` (new — PT homepage)
- `gatsby/src/pages/uk/index.js` (new — explicit UA homepage; root may
  redirect here in future, for now both work)
- `gatsby/src/components/layout.js` (lang chip in header, conditionally)

## Approach

Article template:

```jsx
const ArticleTemplate = ({ data, pageContext }) => {
  const { lang, otherLocaleAvailable } = pageContext;
  const i18n = lang === "pt" ? pt : uk;
  const locale = lang === "pt" ? "pt-PT" : "uk-UA";
  ...
  <html lang={lang} />
  <link rel="alternate" hrefLang="uk"
        href={`https://pastelka.news/uk/${slug}/`} />
  {otherLocaleAvailable && (
    <link rel="alternate" hrefLang="pt"
          href={`https://pastelka.news/pt/${slug}/`} />
  )}
  <link rel="alternate" hrefLang="x-default"
        href={`https://pastelka.news/uk/${slug}/`} />
```

GraphQL query filters by `lang` from `pageContext`:

```graphql
query ($slug: String!, $lang: String!) {
  markdownRemark(
    frontmatter: { slug: { eq: $slug }, lang: { eq: $lang } }
  ) { … }
}
```

Note: legacy UA articles use `lang: "ua"` while page context uses
`"uk"`. We map: at query time, pass `lang === "uk" ? "ua" : lang`. (Or
normalise at gatsby-node level — simpler. Pick the gatsby-node
normalisation: store as `pageContext.frontmatterLang = lang === "uk" ?
"ua" : "pt"`.)

Index pages: copy of current `index.js` with two changes — filter
articles by `frontmatter.lang` (UA → `eq: "ua"`, PT → `eq: "pt"`), use
i18n strings, link to `/uk/<slug>/` or `/pt/<slug>/`.

Lang chip in `layout.js` header: small `<a>` linking to the other
locale's homepage. On article pages, use the `otherLocaleAvailable`
context to link to the matching PT/UK article instead of the homepage.

## Success criterion

- `npm run build` exits 0.
- `public/uk/index.html` and `public/pt/index.html` both exist.
- `grep -c 'hreflang="uk"' public/uk/<slug>/index.html` ≥ 1.
- `grep -c 'hreflang="pt"' public/pt/<slug>/index.html` ≥ 1 (when both
  variants exist).
- PT index page contains only PT articles (or zero, before backfill).

## Rollback

`git revert <commit>`. Article template falls back to UA-only via
gatsby-node revert.

## Execution Report

### Status: COMPLETED

### What Was Done
- `gatsby/src/components/layout.js` — accepts `lang` and
  `otherLocaleHref` props, defaults `lang="uk"` so legacy callers
  (root index, tag pages) keep working. Header gains a small
  `site-lang-chip` linking to the other locale; footer brand,
  description, TG handle, and sitemap link all switch on locale.
- `gatsby/src/templates/article.js` — uses `pageContext.lang` /
  `frontmatterLang` / `otherLocaleAvailable`. GraphQL query filters by
  `slug AND lang` so each page binds to the correct markdown node.
  Date formatting picks `pt-PT` or `uk-UA` locale. Reading-time label
  switches via i18n. Sources/tags labels translated. Prev/next links
  point at `/{lang}/{slug}/`. `Head` exports proper hreflang triplet
  (uk + pt-when-available + x-default), per-locale OG tags,
  per-locale canonical, `<html lang>` set.
- `gatsby/src/templates/tag.js` — UA-only filter on tag query, all
  links point at `/uk/<slug>/`, Layout receives `lang="uk"`.
- `gatsby/src/pages/index.js` — root `/` filters `lang IN ["ua","uk"]`,
  links at `/uk/<slug>/`, full hreflang triplet in Head, lang chip
  switches to `/pt/`.
- `gatsby/src/pages/uk/index.js` (new) — explicit UA homepage at
  `/uk/`. Same content shape as root, canonicalised to `/uk/`.
- `gatsby/src/pages/pt/index.js` (new) — PT homepage at `/pt/`.
  Filters `lang: { eq: "pt" }`, shows an empty state in Portuguese
  when no PT articles exist yet.
- `gatsby/src/components/layout.css` — added `.site-lang-chip` and
  `.empty-state` rules. Existing site-header gains
  `position: relative` so the chip can absolute-position.
- Verified with a hand-written PT sample at
  `content/aima-deadline-passed-april-16-day-after-checklist/pt.md`
  — bequest from TASK-08 verification, used again by TASK-13's smoke
  test.

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `gatsby/src/components/layout.js` | rewritten (~70 lines, was ~50) |
| pashtelka-faion-net | `gatsby/src/components/layout.css` | +30 lines (lang chip + empty state + position fix) |
| pashtelka-faion-net | `gatsby/src/templates/article.js` | rewritten (~165 lines, was ~140) |
| pashtelka-faion-net | `gatsby/src/templates/tag.js` | locale prefix + UA filter |
| pashtelka-faion-net | `gatsby/src/pages/index.js` | locale-aware (UA filter, lang chip, hreflang) |
| pashtelka-faion-net | `gatsby/src/pages/uk/index.js` | new |
| pashtelka-faion-net | `gatsby/src/pages/pt/index.js` | new |
| pashtelka-faion-net | `content/<sample>/pt.md` | sample PT article for verification |

### Tests
- `npm run clean && npm run build` exits 0.
- `public/uk/<sample>/index.html` and
  `public/pt/<sample>/index.html` both exist.
- HTML output for the sample slug contains:
  - UK page: `<html lang="uk">`, three hreflang link tags (uk, pt,
    x-default), `og:locale=uk_UA`, `og:locale:alternate=pt_PT`,
    canonical `https://pastelka.news/uk/<slug>/`.
  - PT page: `<html lang="pt">`, three hreflang link tags, `og:locale
    =pt_PT`, `og:locale:alternate=uk_UA`, canonical
    `https://pastelka.news/pt/<slug>/`.
- `public/uk/index.html` and `public/pt/index.html` both exist.
- `public/index.html` (root) still serves UA content with full
  hreflang triplet.

### Issues
- Gatsby's React `Head` API emits `hrefLang="uk"` (camelCase
  attribute, not lowercase `hreflang`). Browsers and search engines
  accept both per HTML5; no SEO regression. Could not change without
  a Gatsby plugin override — out of scope.
- Adding `<html lang="...">` from inside `Head` only takes effect at
  hydration time on the document element; SSR HTML wrapping puts it
  at the top correctly per the verification grep above.
