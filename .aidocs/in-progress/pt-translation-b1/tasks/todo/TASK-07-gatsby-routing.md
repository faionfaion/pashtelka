# TASK-07 — Gatsby /uk/ + /pt/ article routing + i18n strings

**Subject:** Update `gatsby-node.js` to create `/uk/<slug>/` and
`/pt/<slug>/` article pages from the locale-nested content structure.
Add small i18n string dictionaries.

## Files touched

- `gatsby/gatsby-node.js`
- `gatsby/src/i18n/uk.json` (new)
- `gatsby/src/i18n/pt.json` (new)

## Approach

Gatsby's transformer-remark already picks up nested `*.md` files
(filesystem source is `${__dirname}/../content` which globs recursively).
Each `uk.md` and `pt.md` becomes a `MarkdownRemark` node.

Group nodes by slug, then create pages:

```js
const bySlugLang = {};
for (const n of result.data.allMarkdownRemark.nodes) {
  const lang = (n.frontmatter.lang || "ua").toLowerCase();
  const slug = n.frontmatter.slug;
  bySlugLang[slug] = bySlugLang[slug] || {};
  bySlugLang[slug][lang] = n;
}

for (const slug of Object.keys(bySlugLang)) {
  const variants = bySlugLang[slug];
  const ua = variants.ua;
  const pt = variants.pt;
  if (ua) {
    createPage({
      path: `/uk/${slug}/`,
      component: path.resolve("./src/templates/article.js"),
      context: { slug, lang: "uk", otherLocaleAvailable: !!pt, prev: …, next: … },
    });
  }
  if (pt) {
    createPage({
      path: `/pt/${slug}/`,
      component: path.resolve("./src/templates/article.js"),
      context: { slug, lang: "pt", otherLocaleAvailable: !!ua, prev: …, next: … },
    });
  }
}
```

Prev/next pagination is per-locale (PT articles list among PT articles
only). Tag pages stay flat at `/tag/<tag>/` for v1.

We **drop** the legacy `/<slug>/` URL — instead, we keep a small
backwards-compat in TASK-08 (root index lists UA articles, links to
`/uk/<slug>/`). The root template's old links would break otherwise.

i18n dictionaries:
```json
// uk.json
{
  "minRead": "хв читання",
  "sources": "Джерела",
  "back": "← Назад",
  "tagsLabel": "Теги:",
  "siteName": "Паштелька News"
}
// pt.json — Portuguese B1 equivalents
{
  "minRead": "min de leitura",
  "sources": "Fontes",
  "back": "← Voltar",
  "tagsLabel": "Etiquetas:",
  "siteName": "Pastelka News"
}
```

## Success criterion

- `cd gatsby && npm run clean && npm run build` exits 0.
- After build with at least one slug having both `uk.md` and `pt.md`:
  - `public/uk/<slug>/index.html` exists
  - `public/pt/<slug>/index.html` exists
- For slugs with only `uk.md`: only `/uk/<slug>/` exists, no error.
- Build log shows the right number of pages created.

## Rollback

`git revert <commit>` — gatsby-node falls back to flat routing.
