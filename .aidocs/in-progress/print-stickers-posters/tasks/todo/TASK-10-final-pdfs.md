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
