# Print assets — pashtelka.news

Source files and operator handoff for the Lisbon street-distribution print
campaign. Sticker (75 mm round) + A5 poster, both with QR code pointing at
`pastelka.news/welcome/`.

## Final files for the print shop

These are the operator-exported PDFs that go to the Lisbon print shop:

- `assets/print/sticker.pdf` — 81×81 mm CMYK PDF/X-1a:2003, FOGRA39 ICC.
- `assets/print/poster_a5.pdf` — 154×216 mm CMYK PDF/X-1a:2003, FOGRA39 ICC.

Both are produced by the operator from the matching `*-final.svg` source
in Affinity Publisher (one-time licence, already owned). Step-by-step
below.

## Operator workflow — 6 steps

For each of `sticker-final.svg` and `poster-final-a5.svg`:

1. **Install Affinity Publisher** if not already present (one-time
   licence, already owned).
2. **Place the SVG.** In Affinity: `File → Place` → select
   `assets/print/sticker-final.svg` (or `poster-final-a5.svg`). The SVG
   already has the brand mascot embedded (`<image href="...">` pointing
   at `gatsby/src/images/brand/pashtelka-mascot.png`) and the
   matching QR PNG (`qr-sticker.png` / `qr-poster.png`). All headlines /
   bullets are already typeset — no placeholder swaps needed.
3. **Export as PDF.** `File → Export → PDF`.
4. **Set the preset:** PDF/X-1a:2003.
5. **Set the CMYK profile:** ICC = Coated FOGRA39 (ISO 12647-2:2004 — bundled
   with Affinity defaults). Resolution = 300 DPI. Fonts = convert to
   outlines. Bleed = 3 mm (already in the artboard).
6. **Save** as `assets/print/sticker.pdf` / `assets/print/poster_a5.pdf`.

That's it. The PDFs are then ready for the Lisbon print shop.

### Git LFS for the exported PDFs

`assets/print/*.pdf` is configured as git LFS in `.gitattributes`.
Before the first commit of an exported PDF, the operator runs once:

```bash
git lfs install     # one-time per machine
git add .gitattributes assets/print/sticker.pdf assets/print/poster_a5.pdf
git commit -m "feat: affinity-exported print PDFs"
```

If `git-lfs` is not installed: `sudo apt-get install -y git-lfs` (Debian/
Ubuntu) or `brew install git-lfs` (macOS).

## Specs

| Item | Sticker | Poster |
|------|---------|--------|
| Format | Round, 75 mm diameter | A5 portrait, 148 × 210 mm |
| Bleed | 3 mm → 81 × 81 mm artboard | 3 mm → 154 × 216 mm artboard |
| Safe zone | 5 mm inside trim | 5 mm inside trim |
| Colour | CMYK, 300 DPI, FOGRA39 ICC | CMYK, 300 DPI, FOGRA39 ICC |
| Format | PDF/X-1a:2003, fonts outlined | PDF/X-1a:2003, fonts outlined |
| QR target | `https://pastelka.news/welcome/?utm_source=sticker&utm_campaign=2026-q2` | `https://pastelka.news/welcome/?utm_source=poster&utm_campaign=2026-q2` |
| QR size | 35 mm wide | 35 mm wide |

## Paper recommendations

- **Sticker:** 80 µm gloss white vinyl, weatherproof, with gloss laminate
  on top (Lisbon rain April-Oct, 5-25 mm typical events). The amber brand
  ring at the trim edge is intentional — it gives the cutter a visual
  guide and discourages clean peeling.
- **Poster:** 150-170 g/m² silk-coated for outdoor / café walls. For pure
  indoor use, lightweight matte (130 g/m²) is acceptable and prints
  cheaper.

## Source files

| File | Purpose |
|------|---------|
| `sticker.svg` | Sticker layout TEMPLATE — 81×81 mm with `{{...}}` placeholders |
| `poster_a5.svg` | A5 poster layout TEMPLATE — 154×216 mm with placeholders |
| `sticker-final.svg` | Sticker FINAL — placeholders resolved (mascot + QR + headlines baked in). This is what the operator opens in Affinity. |
| `poster-final-a5.svg` | A5 poster FINAL — placeholders resolved. Operator opens this in Affinity. |
| `qr-sticker.png` | Sticker QR raster (1024×1024, v8, ECC=H), `utm_source=sticker`. |
| `qr-sticker.svg` | Sticker QR vector — preferred for Affinity placement. |
| `qr-poster.png` | Poster QR raster (1024×1024), `utm_source=poster`. |
| `qr-poster.svg` | Poster QR vector — preferred for Affinity placement. |
| `prompts/mascot-v1.txt` | OpenAI prompt for mascot generation (v1, misread). |
| `prompts/mascot-v2.txt` | Mascot v2 prompt — approved canonical brand. |

The SVGs ship with four named layers the operator needs to swap in
Affinity: `MASCOT_PLACEHOLDER`, `QR_PLACEHOLDER`, plus the headline and
URL groups. See the comment at the top of each SVG for the exact
placeholder strings (`{{MASCOT_PATH}}`, `{{QR_PATH}}`, etc.).

The `.afpub` Affinity Publisher source files and final `.pdf` exports are
**not** committed in Phase 4a. They land in Phase 4b after the operator
finishes the layout.

## Required operator tools

1. **Affinity Publisher** (one-time licence, already owned). Used to
   import the SVG, swap placeholders, export PDF/X-1a:2003.
2. **Optional CLI proofing toolchain** — only needed if the agent should
   produce a CMYK proof PDF from the command line (sanity-check before
   handing the file to Affinity):
   ```bash
   sudo apt-get install -y inkscape ghostscript icc-profiles-free
   ```
   Or the pip fallback (proofing only, no ICC gamut mapping):
   ```bash
   pip install --user --break-system-packages cairosvg reportlab
   ```

## QR generation

Sticker QR (full UTM URL):

```bash
python3 scripts/print/generate_qr.py \
  --url "https://pastelka.news/welcome/?utm_source=sticker&utm_campaign=2026-q2" \
  --output /tmp/qr-sticker \
  --size 1024
```

Poster QR (different UTM source):

```bash
python3 scripts/print/generate_qr.py \
  --url "https://pastelka.news/welcome/?utm_source=poster&utm_campaign=2026-q2" \
  --output /tmp/qr-poster \
  --size 1024
```

Each command writes both `.png` (raster) and `.svg` (vector) — use the
`.svg` for Affinity placement to keep the modules crisp at any export
size.

**Module-size note:** the full UTM URL produces a v8 QR (49 modules per
side). At 35 mm physical size that's 0.61 mm per module — below the 1.2
mm rule-of-thumb for 50 cm scan distance. Phone cameras at <30 cm
typically scan it fine. If first physical print fails to scan reliably
from pavement distance, shorten the URL to
`https://pastelka.news/w/?s=lx` (29 chars → v4 → 33 modules → 0.85
mm/module) — adds a 2-line static redirect at `/w/` (parallel to the
existing `/welcome/` redirect).

## Mascot generation

Generate the canonical brand mascot:

```bash
python3 scripts/print/generate_mascot.py \
  --prompt-file assets/print/prompts/mascot-v1.txt \
  --output gatsby/src/images/brand/pashtelka-mascot.png
```

To iterate on a previous version (operator typed "regen" in Claude Code
chat):

```bash
python3 scripts/print/generate_mascot.py \
  --prompt-file assets/print/prompts/mascot-v2.txt \
  --reference gatsby/src/images/brand/pashtelka-mascot.png \
  --output gatsby/src/images/brand/pashtelka-mascot.png
```

OpenAI key loads from env or `~/workspace/.env` (`OPENAI_API_KEY=…`).

## Affinity Publisher import procedure

For each layout (sticker and poster):

1. **Open Affinity Publisher.**
2. `File → New` → custom dimensions:
   - Sticker: 81 × 81 mm with 3 mm bleed (so trim is 75 mm)
   - Poster: 154 × 216 mm with 3 mm bleed (so trim is A5 148×210 mm)
   - Colour: CMYK
   - DPI: 300
   - ICC: Coated FOGRA39 (ISO 12647-2:2004)
3. `File → Place` → select `assets/print/sticker.svg` (or `poster_a5.svg`).
   The SVG comes in as editable vector layers — every named group becomes
   a layer in the Layers panel.
4. **Replace `MASCOT_PLACEHOLDER`:**
   - Click the `MASCOT_PLACEHOLDER` rectangle layer to select it.
   - `File → Place` → `gatsby/src/images/brand/pashtelka-mascot.png`.
   - Resize the placed PNG to fit inside the placeholder rectangle.
   - Delete the placeholder rectangle (and its dashed-stroke note text).
5. **Replace `QR_PLACEHOLDER`:**
   - Run `generate_qr.py` (see "QR generation" above) — produces
     `/tmp/qr-sticker.svg` (or `/tmp/qr-poster.svg`).
   - Click the `QR_PLACEHOLDER` layer in the SVG.
   - `File → Place` → `/tmp/qr-sticker.svg` (vector preferred).
   - Resize to match the placeholder bounds, delete the placeholder.
6. **Hide guide layers** before export: `TRIM_GUIDE`, `SAFE_ZONE_GUIDE`,
   `BLEED_GUIDE` (if it just shows a colour swatch — the cream background
   is included in the SVG itself, so leave the fill but hide any dashed
   visualisations).
7. **Tweak typography** if needed — the SVG uses generic `system-ui`
   font names; in Affinity replace with Inter or Manrope at SemiBold/Bold
   for a polished result. Then `Layer → Convert to Curves` for every
   text layer (so the print shop doesn't need the same font installed).
8. **Export:**
   - `File → Export → PDF`.
   - Preset: **PDF/X-1a:2003**.
   - Colour space: **CMYK**.
   - ICC profile: **Coated FOGRA39 (ISO 12647-2:2004)**.
   - Resolution: **300 DPI**.
   - Fonts: **Convert all to outlines** (already done in step 7).
   - Bleed: **3 mm** (already in the artboard).
   - Save as `assets/print/sticker.pdf` (or `poster_a5.pdf`).
9. **Save the export preset** as `assets/print/affinity-print.afexport`
   so future re-exports stay byte-identical. (Phase 4b adds this file
   to the repo.)

## Print test loop

First Lisbon run plan:

- Quantity: 50 stickers + 20 posters.
- Distribution area: Arroios or Anjos (single district).
- Tracking: UTM-tagged QR URLs feed into Plausible automatically. Filter
  by `utm_source=sticker` / `utm_source=poster` for a 14-day window.
- Decision rule: if unique-scan → Telegram-subscribe conversion is > 2%,
  scale up to a second district. Else: revisit creative or location.

## Print shop candidates

Quote from at least two before placing the order:

- **PrintMakers** — Lisbon, fast turnaround, vinyl + paper.
- **Imprint Lisboa** — boutique, pricier, higher quality.
- **Pixartprinting / Vistaprint** — online, cheapest at scale, slower.

Send: PDF/X-1a:2003 + the spec table at the top of this doc.

## Decisions

- **Affinity Publisher** is the print-export tool. CLI tools provide a
  proofing path only; final PDFs come from Affinity.
- **SVG-first authoring:** the layout sources are SVGs (text editable,
  agent-authorable). `.afpub` is operator output, optional, not
  committed in Phase 4a.
- **Round 75 mm sticker** — friendlier shape, harder for vandals to peel
  cleanly than rectangles.
- **A5 portrait poster** — sticks better to vertical café walls than
  landscape.
- **Mascot at `gatsby/src/images/brand/pashtelka-mascot.png`** — single
  source of truth across welcome page, stickers, posters, future digest
  covers.
