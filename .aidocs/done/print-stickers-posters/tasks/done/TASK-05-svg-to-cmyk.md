# TASK-05 — SVG → CMYK PDF script

**Phase:** 4a
**Subject:** `scripts/print/svg_to_cmyk_pdf.py` — convert an SVG layout to
a CMYK PDF. Inkscape CLI primary path; reportlab+PIL fallback for
proofing-only when Inkscape isn't installed.

## Files touched

- `scripts/print/svg_to_cmyk_pdf.py` (new, executable)

## Approach

CLI flags:

- `--in <svg>` — input SVG layout
- `--out <pdf>` — output PDF
- `--icc <path>` — optional ICC profile, default
  `/usr/share/color/icc/ISOcoated_v2_eci.icc` (FOGRA39)

Detection:

```python
inkscape = shutil.which("inkscape")
gs       = shutil.which("gs") or shutil.which("ghostscript")
```

### Path 1 — Inkscape (preferred)

```bash
inkscape --export-type=pdf --export-pdf-version=1.5 \
         --export-text-to-path --export-area-page \
         --export-filename=<tmp>.pdf <in>.svg
```

Then optionally pipe through ghostscript for true CMYK conversion if
ghostscript + ICC are present:

```bash
gs -dSAFER -dBATCH -dNOPAUSE -sDEVICE=pdfwrite \
   -sProcessColorModel=DeviceCMYK -sColorConversionStrategy=CMYK \
   -dPDFX=true -sOutputICCProfile=<icc> \
   -sOutputFile=<out>.pdf <tmp>.pdf
```

If only Inkscape is available (no gs), ship the RGB PDF and warn that
operator must do the final CMYK conversion in Affinity.

### Path 2 — Pillow + reportlab fallback

When Inkscape is missing, the script:

1. Tries `cairosvg` to rasterise SVG → PNG @ 300 DPI.
2. Falls back to printing the install hint and exiting non-zero if
   `cairosvg` isn't installed.
3. Loads PNG with PIL → `image.convert("CMYK")` (naive sRGB→CMYK, no ICC
   gamut mapping).
4. Embeds the CMYK image into a single-page PDF via `reportlab` at the
   correct physical dimensions (parsed from the SVG's `width="…mm"` and
   `height="…mm"` attributes).
5. Prints a clear warning that this is a **proofing PDF only** — the final
   PDFs MUST come from Affinity Publisher with FOGRA39 ICC.

If neither Inkscape nor cairosvg is present, exit non-zero with:

```
FATAL: SVG rasteriser missing.
Install one of:
  sudo apt-get install -y inkscape ghostscript icc-profiles-free
or:
  pip install --user cairosvg
```

## Success criterion

- `python3 scripts/print/svg_to_cmyk_pdf.py --help` lists `--in`, `--out`,
  `--icc`.
- Run on `assets/print/sticker.svg`:
  - If Inkscape installed → produces a valid PDF, exit 0.
  - If Inkscape missing → exits non-zero with the documented install hint,
    OR succeeds via cairosvg fallback (depending on what's available).
- File at `--out` is a valid PDF (`file <pdf>` reports `PDF document`).
- Naive-CMYK fallback documents the FOGRA39 limitation in stderr output
  every run.

## Execution Report

### Status: COMPLETED

### What Was Done
- Wrote `scripts/print/svg_to_cmyk_pdf.py` (~210 lines).
- Path 1 (preferred): Inkscape CLI for SVG → PDF, then ghostscript with
  the FOGRA39 ICC for true CMYK conversion. Both checked with
  `shutil.which`; ghostscript step is skipped (with a clear warning) if
  ghostscript or the ICC are missing.
- Path 2 (fallback): cairosvg → PIL.convert("CMYK") (naive sRGB→CMYK,
  documented as proofing-only in stderr every run) → reportlab single-
  page PDF at the SVG's physical mm dimensions. SVG dimensions parsed
  via regex from `width="…mm"` / `height="…mm"`.
- Path 3 (no toolchain): exits non-zero with both install commands
  printed.

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `scripts/print/svg_to_cmyk_pdf.py` | new (chmod +x) |

### Tests
- `python3 scripts/print/svg_to_cmyk_pdf.py --help` — lists `--in`,
  `--out`, `--icc`. PASS.
- Run on a minimal test SVG with neither Inkscape nor cairosvg installed
  on this box: exits 2 with the install hint. PASS (matches success
  criterion).

### Issues
- Neither Inkscape nor cairosvg is currently installed on the agent box.
  Both code paths are unexercised end-to-end here; they are reachable
  and the imports are guarded so the script's failure mode is the
  documented install-hint exit.
- **Operator action before Phase 4b:** install Inkscape +
  ghostscript + icc-profiles-free OR pip install cairosvg + reportlab,
  so the proofing PDF generates and the SVG layouts can be sanity-checked
  pre-Affinity.

