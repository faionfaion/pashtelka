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
