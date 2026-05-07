# TASK-06 — SVG layouts + assets/print/README.md

**Phase:** 4a
**Subject:** Author the two SVG layout sources (sticker round 75 mm,
A5 portrait poster) plus the operator-facing print handoff README.

## Files touched

- `assets/print/sticker.svg` (new) — 81 × 81 mm artboard (75 mm trim + 3 mm
  bleed each side)
- `assets/print/poster_a5.svg` (new) — 154 × 216 mm artboard (A5 + 3 mm
  bleed)
- `assets/print/README.md` (new) — print specs, paper recommendations,
  Affinity import procedure
- `assets/print/prompts/.gitkeep` (new) — keep `prompts/` tracked

## Approach

### `sticker.svg`

- Root: `<svg width="81mm" height="81mm" viewBox="0 0 81 81">`
- Layers (named `inkscape:label` + `id` so Affinity sees them):
  - `BLEED_GUIDE` — 81 × 81 outer rect, fill `#fefcfa`
  - `TRIM_CIRCLE` — Ø75 mm circle, stroke for visual reference (export as
    cut-line marker for the print shop, not printed colour)
  - `SAFE_ZONE_GUIDE` — Ø65 mm dashed circle (visual only, not printed)
  - `WORDMARK_TOP_ARC` — `<text>` along a curved path: `pashtelka.news`
  - `MASCOT_PLACEHOLDER` — 22 × 22 mm rect with comment placeholder
    `<!-- {{MASCOT_PATH}}: replace with gatsby/src/images/brand/pashtelka-mascot.png in Affinity -->`
  - `QR_PLACEHOLDER` — 35 × 35 mm rect, comment `<!-- {{QR_PATH}}: SVG output of generate_qr.py -->`
  - `TAG_UA` — `<text>{{HEADLINE_UA}}</text>` defaulting to "Українські
    новини в Португалії"
  - `TAG_PT` — `<text>{{HEADLINE_PT}}</text>` defaulting to "Notícias em
    ucraniano e português"
  - `URL_LINE` — `pastelka.news` bold

Templating header comment at the top of the SVG:

```xml
<!--
  pashtelka.news — sticker layout (75 mm round, 3 mm bleed)
  Placeholders the operator replaces in Affinity Publisher:
    {{MASCOT_PATH}}   = gatsby/src/images/brand/pashtelka-mascot.png
    {{QR_PATH}}       = output of: python3 scripts/print/generate_qr.py \
                         --url https://pastelka.news/welcome/?utm_source=sticker&utm_campaign=2026-q2 \
                         --output /tmp/qr-sticker --size 1024
    {{HEADLINE_UA}}   = "Українські новини в Португалії" (default — can
                        keep or rewrite)
    {{HEADLINE_PT}}   = "Notícias em ucraniano e português" (default)
  CMYK conversion: open in Affinity, File → Export → PDF/X-1a:2003 with
  FOGRA39 ICC. See assets/print/README.md.
-->
```

### `poster_a5.svg`

- Root: `<svg width="154mm" height="216mm" viewBox="0 0 154 216">`
- Layers:
  - `BLEED_GUIDE` — 154 × 216 background fill `#fefcfa`
  - `SAFE_ZONE_GUIDE` — inner rect at 5 mm inset, dashed
  - `HERO_PLACEHOLDER` — top 84 mm tall rect, `{{MASCOT_PATH}}`
  - `HEADLINE_UA` — text "Новини Португалії — українською"
  - `HEADLINE_PT` — text "Notícias de Portugal — em ucraniano e em
    português simples"
  - `BULLETS_UA` — three lines: "щоденні новини", "тижневі гайди",
    "imigração tracker"
  - `BULLETS_PT` — three lines: "notícias diárias", "guias semanais",
    "imigração — pontos de contacto"
  - `QR_PLACEHOLDER` — 35 × 35 mm bottom-right
  - `URL_LINE` — `pastelka.news/welcome/`
  - `SCAN_LABEL` — small "Scan • Escaneia"

Same templating header comment listing the placeholders.

### `assets/print/README.md`

Sections:

1. **Specs** — sticker 75 mm round, A5 portrait poster, 3 mm bleed, 5 mm
   safe zone, CMYK FOGRA39, 300 DPI.
2. **Paper recommendations:**
   - Sticker: 80 µm gloss vinyl, weatherproof, gloss laminate.
   - Poster: 150-170 g/m² silk-coated. Optionally lightweight matte for
     indoor.
3. **Required external tools:**
   - Affinity Publisher (one-time licence)
   - Optional CLI tools for proofing: `apt-get install -y inkscape
     ghostscript icc-profiles-free`
4. **Affinity import procedure:**
   1. `File → New` → A5 / 81×81 mm
   2. `File → Place` → sticker.svg or poster_a5.svg
   3. Replace `MASCOT_PLACEHOLDER` layer with brand mascot
   4. Replace `QR_PLACEHOLDER` layer with `generate_qr.py` SVG output
   5. `File → Export → PDF/X-1a:2003`, FOGRA39 ICC, 300 DPI, fonts
      outlined
5. **QR generation** — example commands, sticker URL with UTM params.
6. **Mascot regeneration** — pointer to `scripts/print/generate_mascot.py`
   and `assets/print/prompts/mascot-v*.txt`.

## Success criterion

- Both SVGs validate as XML (`xmllint --noout` exits 0).
- Both SVGs contain all the documented `{{...}}` placeholder strings.
- `width="81mm"` + `height="81mm"` on sticker.
- `width="154mm"` + `height="216mm"` on poster.
- README mentions: "Affinity Publisher", "PDF/X-1a:2003", "FOGRA39",
  "300 DPI", paper specs.
