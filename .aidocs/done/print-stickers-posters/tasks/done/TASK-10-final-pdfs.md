# TASK-10 — Affinity preset + final PDF exports (Phase 4b)

**Phase:** 4b
**Subject:** Operator-driven step. Operator opens the SVGs in Affinity
Publisher, replaces placeholders with brand mascot + QR, exports
PDF/X-1a:2003 with FOGRA39 ICC, commits the PDFs (git LFS) plus the
Affinity export preset.

## Files touched

- `assets/print/sticker.pdf` (new, git LFS)
- `assets/print/poster_a5.pdf` (new, git LFS)
- `assets/print/affinity-print.afexport` (new) — Affinity export preset
- `.gitattributes` (new or updated) — `*.pdf filter=lfs diff=lfs merge=lfs -text`

## Approach

1. Operator launches Affinity Publisher.
2. For sticker:
   - `File → Place` → `assets/print/sticker.svg`
   - Replace `MASCOT_PLACEHOLDER` layer with `gatsby/src/images/brand/pashtelka-mascot.png`
   - Run `python3 scripts/print/generate_qr.py --url "https://pastelka.news/welcome/?utm_source=sticker&utm_campaign=2026-q2" --output /tmp/qr-sticker --size 1024`
   - Replace `QR_PLACEHOLDER` with `/tmp/qr-sticker.svg`
   - Adjust typography
   - `File → Export → PDF/X-1a:2003`, FOGRA39 ICC, 300 DPI, fonts outlined,
     bleed 3 mm
   - Save to `assets/print/sticker.pdf`
   - Save preset to `assets/print/affinity-print.afexport`
3. Same for poster.
4. Agent: set up git LFS for `*.pdf` if not already, commit.

## Success criterion

- `pdfinfo assets/print/sticker.pdf` reports page size 81×81 mm (or
  approx. 229.6×229.6 pt).
- `pdfinfo assets/print/poster_a5.pdf` reports page size 154×216 mm.
- Both PDFs are CMYK (visible in `pdfinfo` or via `qpdf --show-object`).
- `affinity-print.afexport` committed.
- `*.pdf` tracked in git LFS.

## Execution Report

### Status: COMPLETED (agent scope) / PENDING (operator-side Affinity export)

### What Was Done

- Generated production QR codes via `scripts/print/generate_qr.py`:
  - `assets/print/qr-sticker.{png,svg}` — payload
    `https://pastelka.news/welcome/?utm_source=sticker&utm_campaign=2026-q2`.
  - `assets/print/qr-poster.{png,svg}` — payload
    `https://pastelka.news/welcome/?utm_source=poster&utm_campaign=2026-q2`.
  - Both: version 8, error-correction H, 49×49 modules, 1024×1024 PNG
    (scales cleanly to any physical size from the SVG counterpart).
- Roundtrip-decoded both QRs with opencv `QRCodeDetector`. Decoded URLs
  match the originals exactly.
- Authored `assets/print/sticker-final.svg` and `assets/print/poster-
  final-a5.svg` — the placeholder-substituted finals. The mascot is
  embedded via relative `<image href="../../gatsby/src/images/brand/
  pashtelka-mascot.png">` and the QR via `<image href="./qr-*.png">`,
  so the SVGs are self-contained at the repo level. Headlines are
  "Новини Португалії — українською" (UA) and "Notícias de Portugal —
  em português simples" (PT). Poster bullets per spec, PT translated
  to B1.
- `grep '{{'` confirms no `{{...}}` placeholder remains as an active
  field — the only `{{` strings are inside the legend comment that
  documents what each placeholder mapped to.
- Added `.gitattributes` declaring `assets/print/*.pdf` as git LFS for
  the operator-exported PDFs (5-15 MB CMYK PDF/X-1a:2003).
- Updated `assets/print/README.md` with a 6-step Affinity Publisher
  workflow at the top of the doc (install → Place `*-final.svg` →
  Export → PDF/X-1a:2003 → FOGRA39 ICC + 300 DPI + fonts outlined +
  3 mm bleed → save as `sticker.pdf` / `poster_a5.pdf`). Source-files
  table now lists the new `*-final.svg`, QR PNGs/SVGs, and v2 prompt.
- Tried `python3 scripts/print/svg_to_cmyk_pdf.py --in <svg> --out
  <pdf>` for both finals — script exited with the expected
  "FATAL: SVG rasteriser missing. Install Inkscape …" hint. Inkscape
  and cairosvg are absent on this sandbox; the operator runs the
  proof OR (preferred) goes straight to Affinity for the production
  CMYK PDF/X-1a:2003. No `*-proof.pdf` files committed.

### Files Changed

| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `assets/print/qr-sticker.png` | new (6.4 KB) |
| pashtelka-faion-net | `assets/print/qr-sticker.svg` | new (18.4 KB) |
| pashtelka-faion-net | `assets/print/qr-poster.png` | new (6.4 KB) |
| pashtelka-faion-net | `assets/print/qr-poster.svg` | new (18.4 KB) |
| pashtelka-faion-net | `assets/print/sticker-final.svg` | new |
| pashtelka-faion-net | `assets/print/poster-final-a5.svg` | new |
| pashtelka-faion-net | `assets/print/README.md` | 6-step operator workflow + LFS notes |
| pashtelka-faion-net | `.gitattributes` | new — `assets/print/*.pdf` → git LFS |
| pashtelka-faion-net | `CHANGELOG.md` | `[Unreleased]` entries |

### Verification

- `grep -c '{{' sticker-final.svg poster-final-a5.svg` → 4 each (only
  inside the legend comment documenting the substitution map). The
  active `<image href="...">` and `<text>` fields use the substituted
  values.
- QR roundtrip via opencv:
  - `qr-sticker.png` decodes to
    `https://pastelka.news/welcome/?utm_source=sticker&utm_campaign=2026-q2`.
  - `qr-poster.png` decodes to
    `https://pastelka.news/welcome/?utm_source=poster&utm_campaign=2026-q2`.
- PNG sanity: `Image.open(...).size == (1024, 1024)` for both QRs.
- `svg_to_cmyk_pdf.py` exits 2 with the documented Inkscape/cairosvg
  install hint — expected branch on this sandbox.

### Open items for the operator (TASK-10 final-mile)

- Install Affinity Publisher (one-time licence already owned).
- Open `sticker-final.svg` and `poster-final-a5.svg` via `File → Place`.
- Export both as PDF/X-1a:2003 with FOGRA39 ICC, 300 DPI, fonts
  outlined, 3 mm bleed. Save as `sticker.pdf` / `poster_a5.pdf`.
- `git lfs install`, then commit the two PDFs.
- Send the PDFs + `assets/print/README.md` spec table to the chosen
  Lisbon print shop (PrintMakers / Imprint Lisboa / Pixartprinting).

### Issues

- No Inkscape on the sandbox → no CMYK proof PDF committed. This is
  fine; final PDFs come from Affinity Publisher anyway. Documented
  in the executor instructions.
