# Spec: QR-Code Stickers + A5 Posters for Lisbon Street Distribution

**Status:** backlog
**Owner:** Ruslan
**Created:** 2026-05-06

## Goal

Produce print-ready files (sticker + A5 poster) carrying a QR code that points to `pastelka.news/welcome/`. Files are sent to a Lisbon print shop, who delivers physical units. Goal: every passer-by who sees one understands "pashtelka = simple Portuguese-language news for newcomers" in under 3 seconds.

## Users

- **Pedestrian in Lisbon** — sees sticker on a lamppost / poster in a café. Decides in 3 seconds whether to scan.
- **Print shop operator** — receives a CMYK-ready PDF and prints without back-and-forth.
- **Sticker distributor (Ruslan, friends)** — needs durable adhesive in 5-25mm rain.

## Acceptance Criteria

### AC1 — Sticker spec
- Format: round, 75 mm diameter (typography-standard size).
- Bleed: 3 mm.
- Safe zone (no critical content): 5 mm inside trim.
- Colour: CMYK, 300 DPI, embedded ICC profile (FOGRA39 or equivalent — confirm with print shop, default FOGRA39).
- Layout (top to bottom):
  1. Logo / wordmark "pashtelka.news" — top arc.
  2. QR code (target: `https://pastelka.news/welcome/?utm_source=sticker&utm_campaign=2026-q2`) — centre, ≥ 25 mm wide.
  3. Two-language tag: "Ukrainian news in Portugal • Notícias para a comunidade ucraniana".
- Material recommendation in handoff: gloss vinyl, weatherproof (Lisbon rain April-Oct).

### AC2 — A5 poster spec
- Format: A5 portrait (148 × 210 mm).
- Bleed: 3 mm. Safe zone: 5 mm.
- Colour: CMYK, 300 DPI, FOGRA39.
- Layout (top to bottom):
  1. Hero artwork (top 40%) — same style as digest images / welcome-page hero (pashtelka mascot in Lisbon-themed scene).
  2. Headline UA (one line, large): "Новини Португалії — українською".
  3. Headline PT (one line, large, B1): "Notícias de Portugal — em ucraniano e em português simples".
  4. 3 bullets per language (small): daily news / weekly guides / immigration tracker.
  5. QR code (35 mm wide, with quiet-zone) bottom-right.
  6. Small text near QR: "Scan • Escaneia" + URL `pastelka.news/welcome/`.

### AC3 — Image generation flow
- Hero artwork generated via OpenAI `gpt-image-1.5` /v1/images/edits with the existing pashtelka mascot as the reference image (or a designed mascot if one doesn't exist yet — see AC4).
- Generation script lives at `scripts/print/generate_print_assets.py`.
- The script runs a **reviewer loop**:
  1. Generate hero image.
  2. Show user (telegram preview via tg-send).
  3. User says "regenerate" / "approve" / "edit prompt: ...".
  4. Loop until "approve".
- Final approved hero saved at `assets/print/hero-uk.png` and `assets/print/hero-pt.png` (one per locale headline) — or shared, if same artwork suits both (default: shared).

### AC4 — Mascot definition (canonical brand asset)
- This feature creates the canonical pashtelka mascot. Working concept:
  - A small, friendly bird or pastel-coloured creature ("pastelka" diminutive vibe).
  - Lisbon-coded accessories (azulejo-tile pattern, Tagus bridge silhouette, tram, pastel de nata).
  - Two-language flair (UA + PT colours subtly).
- Mascot reference image saved to `gatsby/src/images/brand/pashtelka-mascot.png` (single source of truth — also referenced by `welcome-landing` and future digest covers).
- Generation flow: OpenAI gpt-image-1.5 iterative reviewer loop (script `scripts/print/generate_mascot.py`) sending previews via `tg-send` to admin chat, accepting `approve` / `regenerate` / `edit prompt: ...` until approved.

### AC5 — QR code quality
- Error-correction level: `H` (30%) — survives partial occlusion (rain stains, scratches).
- Module size: ≥ 4× viewing distance / 100 (rule of thumb). For 75 mm sticker @ ~50 cm scan distance: module ≥ 1.2 mm → at least 21×21 modules → version 1 OK if URL fits, else v2 / v3 with shorter URL.
- Consider shortening URL to `pastelka.news/w/` (single-letter folder) only if QR forces a higher version that becomes unscannable from typical distance. Default: full `/welcome/`, re-evaluate on first physical print test.

### AC6 — File deliverables
- `assets/print/sticker.pdf` — single page, 81×81 mm (with bleed), CMYK 300DPI, fonts outlined, images embedded.
- `assets/print/poster_a5.pdf` — single page, 154×216 mm (with bleed), CMYK 300DPI.
- A small `assets/print/README.md` describes specs for the print shop, including paper weight recommendations:
  - Sticker: 80μm vinyl, gloss laminate.
  - Poster: 150-170 g/m² silk-coated, optionally lightweight matte for indoor.
- Source files (.afpub or .ai or InDesign IDML) optional but nice — at minimum keep the SVG layout source.

### AC7 — Print test loop
- First print run: 50 stickers + 20 posters for a single Lisbon district (Arroios or Anjos).
- Track utm-tagged scans for 14 days.
- If conversion to TG sub > 2% of unique scans: scale up. Else: revisit creative.

### AC8 — Authoring tool & reproducibility
- **Affinity Publisher** is the primary authoring tool (one-time licence, owned).
- Source files: `assets/print/sticker.afpub` and `assets/print/poster_a5.afpub` committed to git.
- PDF export settings documented in `assets/print/README.md`: PDF/X-1a:2003, FOGRA39, 300DPI, fonts outlined, embedded ICC.
- Re-export workflow: open `.afpub` → File → Export → PDF/X-1a → settings preset `pashtelka-print`. The preset itself is exported once to `assets/print/affinity-print.afexport` and committed.
- Pre-commit check: PDFs in `assets/print/` tracked in git LFS to keep repo clean (PDFs ~5-15MB each).

## Out of Scope

- Distribution logistics (where to stick, permits) — handled offline by Ruslan.
- Translating poster body copy beyond the headlines and bullets.
- Animated/digital ad versions of the same artwork.
- A/B variants — only one design per format for v1.

## Decisions

- **Sticker shape:** round 75 mm. Friendlier, harder for vandals to peel cleanly.
- **Poster orientation:** portrait. Sticks better to vertical café walls.
- **Authoring tool:** Affinity Publisher.
- **Mascot:** new canonical pashtelka mascot, reused across welcome / stickers / posters / future digest covers.

## Open Questions

- **Print shop in Lisbon:** candidates — PrintMakers, Imprint Lisboa, online (Pixartprinting, Vistaprint). Decide during execution after first PDF is ready and we can request quotes.
- First-run quantity: 50 stickers + 20 posters — confirm budget before placing the order.
