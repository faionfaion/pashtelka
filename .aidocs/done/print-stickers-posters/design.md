# Design: Print Stickers + Posters for Lisbon Distribution

**Implements:** spec.md
**Status:** todo
**Owner:** Ruslan

## High-level approach

Three-script Python toolchain + two SVG layout sources + an iterative mascot
generator. Operator opens the SVGs in Affinity Publisher (one-time licence,
already owned), runs `Place` for the mascot/QR, and exports PDF/X-1a:2003
with FOGRA39 ICC. The repo ships everything except the final PDFs and
`.afpub` files (Affinity files are binary and cannot be authored by an agent
— SVGs are the canonical sources, `.afpub` is operator output).

```
scripts/print/
├── generate_mascot.py       Python wrapper — OpenAI gpt-image-1.5
├── generate_qr.py           qrcode lib — PNG + SVG output
└── svg_to_cmyk_pdf.py       Inkscape CLI primary, reportlab+PIL fallback

assets/print/
├── sticker.svg              75 mm round, placeholders {{MASCOT_PATH}} etc.
├── poster_a5.svg            A5 portrait, placeholders
├── prompts/
│   └── mascot-v{N}.txt      Iteration prompts (kept for reproducibility)
└── README.md                Operator handoff: paper, ICC, Affinity steps

gatsby/src/images/brand/
└── pashtelka-mascot.png     Canonical mascot (single source of truth, ≥1024²)
```

## Authoring tool decision

**Affinity Publisher** for the final PDF/X-1a:2003 export. The repo carries
the `.svg` layout sources (text editable, agent-authorable). Operator
imports the SVG into Affinity (`File → Place`), tweaks if needed, exports
via the project's `pashtelka-print` PDF preset. Documented in
`assets/print/README.md`.

**Why not pure CLI (Inkscape) end-to-end?** Inkscape's PDF/X-1a output
chain is workable but the operator wants Affinity for fine typography
control + brand-preset reuse across future jobs. We keep CLI as a
fallback/preview path: `svg_to_cmyk_pdf.py` produces a CMYK proof PDF for
sanity-checking before opening Affinity.

## Sticker layout (75 mm round)

Trim 75 mm. Bleed 3 mm → artboard 81 × 81 mm. Safe zone 5 mm → critical
content lives in a 65 mm circle.

```
┌─────────────── 81 mm ───────────────┐
│  · · · · · BLEED 3 mm · · · · · · │
│   ╭──────── trim Ø75 ────────╮    │
│   │   pashtelka.news            │ ← top arc text, 6 mm tall
│   │      ───────────             │
│   │                              │
│   │       MASCOT (top)           │
│   │       ────────               │
│   │                              │
│   │       ▓▓▓▓▓▓▓▓▓               │
│   │       ▓ QR    ▓  35 mm wide   │
│   │       ▓▓▓▓▓▓▓▓▓               │
│   │                              │
│   │   ▼ two-language tag ▼        │
│   │  Ukrainian news in Portugal  │ ← 3.2 pt
│   │  Notícias para a comunidade  │
│   │       pastelka.news           │
│   ╰──────────────────────────────╯ │
│  · · · · · BLEED 3 mm · · · · · · │
└──────────────────────────────────────┘
```

Vertical rhythm (top to bottom inside the safe circle):

| Element | Size | Position from top of artboard |
|---------|------|-------------------------------|
| Top-arc wordmark "pashtelka.news" | 5.5 mm cap-height | 14 mm |
| Mascot illustration | 22 mm tall | 24 mm |
| QR code | 35 mm × 35 mm | 36 mm |
| UA tag line | 3.2 mm | 60 mm |
| PT tag line | 2.8 mm | 65 mm |
| URL | 3.0 mm bold | 70 mm |

Background: warm cream (`#fefcfa`, brand cream) → matches the welcome page.
Stroke: 1 mm warm-amber ring at trim edge for visual containment (sits just
inside trim so the cutter doesn't slice it).

## Poster layout (A5 portrait, 148 × 210 mm)

Trim 148 × 210 mm. Bleed 3 mm → artboard 154 × 216 mm. Safe zone 5 mm.

```
┌────────── 154 mm ──────────┐
│ · · · BLEED · · · · · · · │
│  ╭────── 148 trim ──────╮  │
│  │                      │  │
│  │   HERO (40% top)     │  │ ← mascot in Lisbon scene
│  │   ───────────         │  │   84 mm tall
│  │                      │  │
│  │   Новини Португалії  │  │ ← UA headline, 11 mm cap
│  │      українською     │  │
│  │                      │  │
│  │   Notícias de        │  │ ← PT headline B1, 9 mm cap
│  │      Portugal — em   │  │
│  │      ucraniano       │  │
│  │                      │  │
│  │   • daily news       │  │ ← UA bullets, 4 mm
│  │   • weekly guides    │  │
│  │   • immigration tracker│ │
│  │                      │  │
│  │   • notícias diárias │  │ ← PT bullets B1, 4 mm
│  │   • guias semanais   │  │
│  │   • imigração        │  │
│  │                      │  │
│  │ Scan ▶  ┌─────────┐  │  │ ← QR 35 mm bottom-right
│  │ Escaneia│   QR    │  │  │   small "Scan/Escaneia"
│  │         └─────────┘  │  │   + URL beside it
│  │   pastelka.news/welcome│ │
│  ╰──────────────────────╯  │
│ · · · BLEED · · · · · · · │
└────────────────────────────┘
```

Same brand-cream background. Same warm-amber accent. Headlines in a system
sans matching the welcome page (`system-ui, -apple-system, "Segoe UI"` —
operator picks a real font on Affinity side; brief recommends Inter or
Manrope at SemiBold/Bold).

## QR code

`qrcode` Python lib with the following parameters:

| Param | Value | Why |
|-------|-------|-----|
| `error_correction` | `H` (30%) | Survives rain stains, scratches |
| `box_size` | 10 (PNG) / 1 (SVG vector) | Module size derived per layout |
| `border` | 4 | Standard QR quiet-zone (4 modules) |
| `version` | None (auto) | Lib picks smallest version that fits URL |

URL: `https://pastelka.news/welcome/?utm_source=sticker&utm_campaign=2026-q2`
length ≈ 80 chars at error-correction H — auto-version selects v5 or v6 (37
or 41 modules per side). On a 35 mm QR that's 0.85-0.95 mm per module —
above the 1.2 mm rule-of-thumb for 50 cm scan distance.

If first physical print is unscannable from typical pavement distance,
shorten the URL to `pastelka.news/w/?s=lx` (single-letter folder) — that
brings the QR down to v3 (29 modules) and module size to 1.2 mm. The
shortener path is documented in `done.md` of the welcome-landing feature
(static redirect already lives at `/welcome/`, an extra `/w/` redirect is a
2-line follow-up). Default for v1: full URL, re-evaluate after first
print test.

Output: PNG 1024 px (300 DPI at 86 mm — covers both sticker + poster) and
SVG (vector — preferred for Affinity import).

## CMYK conversion approach

Two paths, in priority order:

### Path 1 — Inkscape CLI (preferred, if installed)

```bash
inkscape \
  --export-type=pdf \
  --export-pdf-version=1.5 \
  --export-text-to-path \
  --export-area-page \
  --export-filename=/path/out.pdf \
  /path/in.svg
```

Inkscape 1.2+ produces RGB PDF; for true CMYK we post-process via
`ghostscript` with the FOGRA39 ICC profile:

```bash
gs -dSAFER -dBATCH -dNOPAUSE \
   -sDEVICE=pdfwrite \
   -sProcessColorModel=DeviceCMYK \
   -sColorConversionStrategy=CMYK \
   -dPDFX=true \
   -sOutputICCProfile=/usr/share/color/icc/ISOcoated_v2_eci.icc \
   -sOutputFile=out_cmyk.pdf in.pdf
```

(FOGRA39 ICC is shipped with `icc-profiles-free` apt package as
`ISOcoated_v2_eci.icc`. If missing, the script falls back to converting via
Pillow.)

Operator install command:

```bash
sudo apt-get install -y inkscape ghostscript icc-profiles-free
```

### Path 2 — Pillow + reportlab fallback

If Inkscape isn't installed, `svg_to_cmyk_pdf.py`:

1. Rasterises SVG to PNG via `cairosvg` (preinstalled deps will be added if
   missing — script will print install command and exit non-zero).
2. Loads PNG with PIL, converts via `image.convert("CMYK")` (best-effort:
   uses sRGB → CMYK simple linear conversion; not gamut-mapped through ICC).
3. Embeds the CMYK image into a single-page PDF via reportlab at the right
   physical dimensions.

**Limitation documented:** PIL's `convert("CMYK")` is a naive sRGB→CMYK
without ICC gamut mapping. Acceptable for **proofing only**. The actual
print PDFs MUST be exported from Affinity Publisher with FOGRA39 ICC
attached. The fallback path exists to give the agent a sanity check that
the SVG layout renders correctly before the operator picks it up.

### Recommended path

**Operator runs Affinity Publisher for the final print PDFs.** The
`svg_to_cmyk_pdf.py` script is a CLI proof tool — useful in CI / agent
loops, not a substitute for Affinity export.

## Mascot iteration loop

Sequential, agent-driven, operator-in-the-loop via Telegram:

```
v1 — generate from prompt only (/v1/images/generations)
   ↓
   tg-send preview to operator
   ↓
operator replies "approve" / "regen" / "edit prompt: <delta>"
   ↓
v2+ — if approved → done; if regen → re-run /v1/images/edits with v(N-1)
       as reference and same prompt; if edit → update prompt file, run
       /v1/images/generations fresh.
```

`generate_mascot.py` accepts:

- `--prompt-file` — path to prompt text file
- `--output` — output PNG path
- `--reference` — optional, path to previous mascot for `/v1/images/edits`
  (used in v2+ when iterating on the same composition)
- `--size` — default `1024x1024`

The script doesn't bake in the loop — Phase 4a calls it once for v1, then
the operator signals approve/regen and Phase 4b re-runs the script with
appropriate flags for v2+.

API:
- v1 (no reference): `POST /v1/images/generations`, `model=gpt-image-1.5`,
  `size=1024x1024`, `quality=auto`.
- v2+ (with reference): `POST /v1/images/edits` with the previous PNG as
  the reference image, same prompt, same size.

Reads `OPENAI_API_KEY` from env or `~/workspace/.env` (matches the
`gatsby/scripts/gen-welcome-assets.mjs` pattern).

## Mascot prompt v1

Saved to `assets/print/prompts/mascot-v1.txt`. Concept brief:

- Small friendly bird-shaped mascot. "Pashtelka" / "pastelka" plays on the
  Portuguese pastel and the Ukrainian diminutive.
- Pastel colours: warm amber (`#d97706`), soft cream (`#fefcfa`), azulejo
  blue (`#7ba8c7`) accent.
- Cartoon + pixel-art hybrid — friendly round shapes, expressive eyes, a
  hint of pixel grid in the wing/feather detail.
- Mascot holding (or near) a pastel de nata. Lisbon-coded surroundings:
  faint azulejo tile wall pattern, distant 25 de Abril bridge silhouette,
  tiny yellow tram in the lower-right.
- Warm sunset palette aligned with the welcome page hero (already shipped).
- Square aspect, 1024×1024 minimum.
- Transparent or simple solid background — this image is the brand
  reference, will be cut out and re-placed.

## Affinity Publisher import procedure

Operator workflow (documented in `assets/print/README.md`):

1. Open Affinity Publisher → `File → New` → A5 (poster) or 81 × 81 mm
   (sticker).
2. `File → Place` → select `assets/print/sticker.svg` or
   `assets/print/poster_a5.svg`. The SVG comes in editable, all text/shapes
   live as vector layers.
3. Replace the placeholder mascot rectangle (named `MASCOT_PLACEHOLDER` in
   the SVG layer panel) with `gatsby/src/images/brand/pashtelka-mascot.png`
   via `File → Place`.
4. Replace the placeholder QR rectangle (`QR_PLACEHOLDER` layer) with the
   PNG/SVG output of `generate_qr.py` — SVG preferred for crispness.
5. Tweak typography if needed (font swap, kerning).
6. `File → Export → PDF/X-1a:2003`. Settings:
   - Colour space: CMYK
   - ICC profile: FOGRA39 (Coated FOGRA39, ISO 12647-2:2004)
   - Resolution: 300 DPI
   - Fonts: outlined (for print-shop reliability)
   - Bleed: 3 mm (already in the artboard)
7. Save the export preset as `pashtelka-print.afexport` and commit it with
   the next feature run (out of scope for v1 — Phase 4b).
8. Final PDFs land at `assets/print/sticker.pdf` and
   `assets/print/poster_a5.pdf`. Tracked by git LFS (Phase 4b).

## File deliverable list (this feature, total)

Phase 4a (this run):

- `scripts/print/generate_mascot.py`
- `scripts/print/generate_qr.py`
- `scripts/print/svg_to_cmyk_pdf.py`
- `assets/print/sticker.svg`
- `assets/print/poster_a5.svg`
- `assets/print/README.md`
- `assets/print/prompts/mascot-v1.txt`
- `gatsby/src/images/brand/pashtelka-mascot.png` (mascot v1 — draft)
- `requirements.txt` updated (`qrcode`, `cairosvg` optional fallback)

Phase 4b (next run, after operator approves the mascot):

- Final approved mascot at the same path (overwrite v1 if regen approved)
- `assets/print/affinity-print.afexport` (Affinity preset, exported once)
- `assets/print/sticker.pdf` (operator export, git LFS)
- `assets/print/poster_a5.pdf` (operator export, git LFS)
- `gatsby/src/pages/uk/welcome.js` and `…/pt/welcome.js` updated to import
  the brand mascot from `gatsby/src/images/brand/pashtelka-mascot.png` (the
  welcome page placeholder swap, called out in welcome-landing/done.md)
- `done.md`
- Move feature folder to `.aidocs/done/`

## Decisions

- **SVG-first authoring:** `.svg` is the canonical layout source. `.afpub`
  is operator output, optional, not committed unless the operator decides
  to.
- **Affinity Publisher** is the print-export tool. CLI tools provide the
  proofing path only.
- **Inkscape preferred over reportlab** for CMYK because it preserves
  vector text/paths through to PDF; reportlab pipeline rasterises which
  loses vector crispness on the QR.
- **Mascot at `gatsby/src/images/brand/pashtelka-mascot.png`** — single
  source of truth. Welcome page swap is a separate task in Phase 4b.
- **No PT TG channel link in v1 sticker copy** — the welcome-landing PT
  channel `@pashtelka_pt` doesn't exist yet. Sticker shows the URL
  `pastelka.news` only; the welcome page handles the language split.
- **Two-script vs one-script:** kept three scripts (`generate_mascot`,
  `generate_qr`, `svg_to_cmyk_pdf`) instead of one bundle so each is
  callable from the agent loop independently and re-runnable.

## Out of scope

- Final PDFs and `.afpub` source files (Phase 4b).
- Mascot v2+ iteration (Phase 4b — depends on operator feedback).
- Welcome-page swap to use the brand mascot (Phase 4b).
- Distribution, print-shop choice, sticker counts (operator domain).
- Per-sticker UTM token in `?start=` (analytics follow-up SDD).
