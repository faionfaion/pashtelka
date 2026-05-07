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

## Execution Report

### Status: COMPLETED

### What Was Done
- Wrote `gatsby/scripts/split-sitemaps.mjs` (~75 lines, ESM, no
  external deps). Reads `public/sitemap-0.xml`, partitions URL blocks
  by `/uk/`, `/pt/`, locale-neutral. Writes
  `public/sitemap-uk.xml`, `public/sitemap-pt.xml`,
  `public/sitemap.xml` (index).
- Idempotent: re-running just rewrites. Exits 0 on missing input so
  it never blocks a partial build.
- Wired via `package.json` `postbuild` hook so one `npm run build`
  produces all files.

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `gatsby/scripts/split-sitemaps.mjs` | new (~75 lines) |
| pashtelka-faion-net | `gatsby/package.json` | +1 postbuild line |

### Tests
- `npm run build` exits 0. Postbuild line:
  `split-sitemaps: wrote sitemap-uk.xml (804 urls), sitemap-pt.xml
  (647 urls), sitemap.xml (index of 2)` — counts are inflated by
  642 locale-neutral tag pages duplicated across both locale
  sitemaps.
- UA-prefix URLs in `sitemap-uk.xml`: **160** (158 articles + /uk/ +
  /uk/welcome/).
- PT-prefix URLs in `sitemap-pt.xml`: **3** (1 article + /pt/ +
  /pt/welcome/) — scales up as the pipeline writes more PT
  articles.
- `sitemap.xml` is the proper sitemapindex referencing both locale
  files at absolute URLs.

### Issues
- Locale-neutral pages duplicated across both sitemaps. Harmless —
  search engines deduplicate by URL — but inflates count.
- gatsby-plugin-sitemap's original outputs (`sitemap-0.xml`,
  `sitemap-index.xml`) still exist on disk alongside our three new
  files. They don't hurt anything; removing them risks break-glass
  recovery if the splitter has a bug. Operator can `rm` them after
  a clean deploy if desired.
