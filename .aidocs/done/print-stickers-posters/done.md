# done.md — print-stickers-posters

**Shipped:** 2026-05-07. Phase 4a + 4b agent runs complete; final PDFs await
operator-side Affinity export.

## What shipped

- Canonical brand mascot at `gatsby/src/images/brand/pashtelka-mascot.png`
  (1024×1024, ~1.5 MB). v1 was a misread (separate bird-creature); v2 is
  the correct Pashtelka News house style — the pastel de nata IS the
  character. v1 prompt kept on disk for reproducibility.
- Three Python scripts: `scripts/print/{generate_qr,generate_mascot,
  svg_to_cmyk_pdf}.py`. QR + mascot generators run end-to-end on the
  sandbox; CMYK PDF tool exits with the documented "install Inkscape"
  hint when the local rasteriser is missing.
- Two SVG layout templates with `{{...}}` placeholders
  (`assets/print/sticker.svg`, `…/poster_a5.svg`) plus the resolved
  `*-final.svg` companions with mascot + QR + headlines baked in.
- Production QR PNGs + SVGs at `assets/print/qr-{sticker,poster}.{png,
  svg}`, both roundtrip-verified via opencv decoder.
- `assets/print/README.md` carries the 6-step Affinity export workflow
  at the top.
- Welcome-landing hero swapped to the brand mascot — `gatsby/scripts/
  gen-welcome-assets.mjs --source <path>` re-encodes the three variants
  in place. `npm run build` exits 0; both `/uk/welcome/` and `/pt/
  welcome/` reference the regenerated hero.

## Final files for the print shop

Operator exports these from Affinity Publisher (PDF/X-1a:2003 + FOGRA39
ICC + 300 DPI + fonts outlined + 3 mm bleed):

- `assets/print/sticker.pdf` — 81×81 mm, round 75 mm trim.
- `assets/print/poster_a5.pdf` — 154×216 mm, A5 portrait trim.

`.gitattributes` already declares both under git LFS — operator runs
`git lfs install` once, then commits the PDFs.

## QR URLs

| Asset | URL |
|-------|-----|
| Sticker | `https://pastelka.news/welcome/?utm_source=sticker&utm_campaign=2026-q2` |
| Poster | `https://pastelka.news/welcome/?utm_source=poster&utm_campaign=2026-q2` |

Both UTM-tagged so Plausible filtering by `utm_source` separates the
two channels. 14-day window, conversion target ≥ 2% scan→TG sub.

## First print run

50 stickers + 20 posters in a single Lisbon district (Arroios or
Anjos). Materials per spec AC1 / AC2: 80 µm gloss vinyl with laminate
for stickers; 150-170 g/m² silk-coated for posters. Quote at least
two of: PrintMakers, Imprint Lisboa, Pixartprinting / Vistaprint.

## Open items for the operator

- Install Affinity Publisher (one-time licence already owned).
- Open `assets/print/sticker-final.svg` and `…/poster-final-a5.svg`
  via `File → Place`. Export each as PDF/X-1a:2003 per the README.
- `git lfs install`, then commit the two PDFs.
- Get a quote from at least two Lisbon print shops; place the order
  for 50 stickers + 20 posters.
- Track Plausible UTM-tagged scans for 14 days; decide scale-up vs
  revisit based on the 2% conversion threshold.

## Where the canonical mascot lives

`gatsby/src/images/brand/pashtelka-mascot.png` — single source of truth.
The welcome-landing hero (`gatsby/src/images/welcome/hero-placeholder.
{png,webp,avif}`) is a re-encoded variant of the same canonical PNG;
filename kept stable so welcome page imports don't need to change.
