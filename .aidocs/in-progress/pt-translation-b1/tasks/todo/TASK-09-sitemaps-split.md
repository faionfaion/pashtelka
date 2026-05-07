# TASK-09 — Split sitemaps into /sitemap-uk.xml + /sitemap-pt.xml

**Subject:** Post-build script that splits the gatsby-plugin-sitemap
output into two locale-scoped sitemaps plus an index.

## Files touched

- `gatsby/scripts/split-sitemaps.mjs` (new)
- `gatsby/package.json` (postbuild script)

## Approach

Run after `gatsby build` produces `public/sitemap-index.xml` (or
`sitemap.xml`). Read all URLs, partition by `/uk/` vs `/pt/`, write:

- `public/sitemap-uk.xml` — UA URLs only
- `public/sitemap-pt.xml` — PT URLs only
- `public/sitemap.xml` — index referencing the two

ESM script using `fs/promises` only — no extra deps.

```js
const text = await fs.readFile("./public/sitemap-0.xml", "utf-8");
const ukUrls = []; const ptUrls = []; const otherUrls = [];
for (const m of text.matchAll(/<url>[^<]*<loc>([^<]+)<\/loc>([^<]*)<\/url>/g)) {
  const loc = m[1];
  if (loc.includes("/uk/")) ukUrls.push(m[0]);
  else if (loc.includes("/pt/")) ptUrls.push(m[0]);
  else otherUrls.push(m[0]);
}
// otherUrls (homepage, /tag/, /welcome/) go in both locale sitemaps
```

`gatsby-plugin-sitemap` defaults to writing `sitemap-0.xml` +
`sitemap-index.xml`. We rewrite the index to point at the two new
locale files.

Wire into `package.json`:

```json
"scripts": {
  "build": "gatsby build",
  "postbuild": "node scripts/split-sitemaps.mjs"
}
```

## Success criterion

- After `npm run build`: `public/sitemap-uk.xml` and
  `public/sitemap-pt.xml` exist, both well-formed XML.
- `public/sitemap.xml` (or `sitemap-index.xml`) lists both locale
  files.
- `grep -c "/uk/" public/sitemap-uk.xml` ≥ 1.
- `grep -c "/pt/" public/sitemap-pt.xml` ≥ 0 (≥ 1 after first PT
  article shipped).

## Rollback

`git revert <commit>` — single script + package.json one-liner.
