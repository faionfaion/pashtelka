# TASK-09 — Welcome-landing import swap (Phase 4b)

**Phase:** 4b
**Subject:** Swap the welcome-landing hero placeholder for the now-canonical
brand mascot. Per `welcome-landing/done.md` "Mascot placeholder swap"
section.

## Files touched

- `gatsby/scripts/gen-welcome-assets.mjs` — add `--source` flag to skip
  OpenAI and re-encode from a local file (or new sub-command `from-brand`)
- `gatsby/src/images/welcome/hero-placeholder.{png,webp,avif}` —
  re-emitted from the brand mascot
- `gatsby/src/pages/uk/welcome.js`, `gatsby/src/pages/pt/welcome.js` — if
  needed, update import paths (likely no change — the variants stay at the
  same path, just regenerated)

## Approach

1. Edit `gen-welcome-assets.mjs`: add `--source <path>` flag. When set, skip
   the OpenAI call and use the local PNG as the input for the sharp resize
   chain.
2. Run:
   ```bash
   cd gatsby
   node scripts/gen-welcome-assets.mjs hero --source ../gatsby/src/images/brand/pashtelka-mascot.png
   ```
3. Verify the AVIF/WebP/PNG variants are regenerated and pass the existing
   welcome-landing test plan (≤80 KB AVIF, ≥940 px PNG width).
4. `npm run build` — must exit 0.
5. Visually open `/uk/welcome/` and `/pt/welcome/` in a browser; confirm
   the new mascot loads.

## Success criterion

- `gen-welcome-assets.mjs` accepts `--source` flag.
- Three welcome hero variants re-emitted from brand mascot.
- AVIF still ≤ 80 KB, PNG width ≥ 940.
- `npm run build` exits 0.

## Execution Report

### Status: COMPLETED

### What Was Done

- Added `--source <path>` flag to `gatsby/scripts/gen-welcome-assets.mjs`.
  When set with the `hero` sub-command the script reads the local PNG
  via `fs.readFileSync` and feeds it straight into the existing sharp
  resize chain — skipping the OpenAI call. Idempotent re-runs preserved
  (still overwrites the three hero-placeholder.* outputs in place).
- Lifted the early `OPENAI_API_KEY` fatal exit out of module top-level
  and into `generateImage()`, so a `--source`-only run no longer needs
  the key.
- Decision: kept the output filename `hero-placeholder.{png,webp,avif}`
  unchanged — the welcome page imports stay valid, only the bytes
  behind the names change. Wave 2's design.md called this out
  (path swaps content, not name).
- Re-ran with `--source ../gatsby/src/images/brand/pashtelka-mascot.png`
  to regenerate the three variants from the brand mascot.
- Ran `npm run build` from gatsby/. Build exited 0; postbuild
  split-sitemaps.mjs ran cleanly.

### Files Changed

| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `gatsby/scripts/gen-welcome-assets.mjs` | added `--source` flag |
| pashtelka-faion-net | `gatsby/src/images/welcome/hero-placeholder.png` | regenerated from brand mascot (162.1 KB) |
| pashtelka-faion-net | `gatsby/src/images/welcome/hero-placeholder.webp` | regenerated (143.2 KB) |
| pashtelka-faion-net | `gatsby/src/images/welcome/hero-placeholder.avif` | regenerated (37.8 KB) |
| pashtelka-faion-net | `CHANGELOG.md` | `[Unreleased] / Changed` entry |

### Verification

- `node --check scripts/gen-welcome-assets.mjs` → syntax OK.
- AVIF size: 37.8 KB (≤ 80 KB cap from welcome-landing test plan).
- Hero placeholder sizes much larger than the prior ~17 KB AVIF — the
  bytes really did change.
- `npm run build` ran in 20.9 sec; route summary lists `/`, `/uk/`,
  `/pt/`, `/uk/welcome/`, `/pt/welcome/`, plus 158 articles via
  `src/templates/article.js` and 642 tag pages via `src/templates/tag.js`.
  Total 821 directories under `gatsby/public/`. Sitemap split:
  `sitemap-uk.xml` (804 urls), `sitemap-pt.xml` (647 urls).
- Both `public/uk/welcome/index.html` and `public/pt/welcome/index.html`
  reference the new hashed `hero-placeholder-*.{avif,webp,png}` variants
  served from `/static/`.

### Commit

- to be added in this task close

### Issues

- None.
