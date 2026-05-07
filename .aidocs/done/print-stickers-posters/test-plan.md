# Test Plan: Print Stickers + Posters

**Implements:** spec.md (AC1..AC8), design.md
**Status:** todo

Each AC is verified with one or more commands runnable from a clean checkout.
Where a CLI tool is missing on the agent box (Inkscape, ghostscript), the
plan documents the install step and the manual operator path.

## Pre-flight

```bash
cd ~/workspace/projects/pashtelka-faion-net
python3 -c "import qrcode; print('qrcode', qrcode.__version__)"   # ≥ 7.4
python3 -c "import PIL; print('Pillow', PIL.__version__)"         # ≥ 11
which inkscape ghostscript                                         # optional
test -f ~/workspace/.env && grep -c '^OPENAI_API_KEY=' ~/workspace/.env  # ≥1
```

If `qrcode` is missing: `pip install --user qrcode[pil]`.

## AC1 — Sticker spec (SVG roundtrip + CMYK PDF)

```bash
# Layout SVG exists, has all four placeholders
test -f assets/print/sticker.svg
grep -c '{{MASCOT_PATH}}'   assets/print/sticker.svg   # expect: ≥1
grep -c '{{QR_PATH}}'        assets/print/sticker.svg   # expect: ≥1
grep -c '{{HEADLINE_UA}}'    assets/print/sticker.svg   # expect: ≥1
grep -c '{{HEADLINE_PT}}'    assets/print/sticker.svg   # expect: ≥1
grep -c 'width="81mm"'       assets/print/sticker.svg   # expect: 1 (artboard incl. bleed)
grep -c 'height="81mm"'      assets/print/sticker.svg   # expect: 1

# CMYK PDF roundtrip — Inkscape path
python3 scripts/print/svg_to_cmyk_pdf.py \
  --in assets/print/sticker.svg \
  --out /tmp/sticker-test.pdf

test -f /tmp/sticker-test.pdf
file /tmp/sticker-test.pdf | grep -c 'PDF'   # expect: 1

# If Inkscape missing the script must exit non-zero with a clear install hint
which inkscape || python3 scripts/print/svg_to_cmyk_pdf.py --in assets/print/sticker.svg --out /tmp/foo.pdf 2>&1 | grep -ci 'apt-get install inkscape'
```

The actual PDF/X-1a:2003 export with FOGRA39 ICC happens in **Affinity
Publisher** (operator). The CLI path produces a CMYK proofing PDF only.

## AC2 — Poster spec (A5 portrait)

```bash
test -f assets/print/poster_a5.svg
grep -c 'width="154mm"'      assets/print/poster_a5.svg   # 1 (A5 + bleed)
grep -c 'height="216mm"'     assets/print/poster_a5.svg   # 1
grep -c '{{MASCOT_PATH}}'    assets/print/poster_a5.svg   # ≥1
grep -c '{{QR_PATH}}'        assets/print/poster_a5.svg   # ≥1
grep -c 'Новини Португалії'  assets/print/poster_a5.svg   # ≥1 (UA headline)
grep -c 'Notícias de Portugal' assets/print/poster_a5.svg # ≥1 (PT headline)

# CMYK PDF roundtrip
python3 scripts/print/svg_to_cmyk_pdf.py \
  --in assets/print/poster_a5.svg \
  --out /tmp/poster-test.pdf
file /tmp/poster-test.pdf | grep -c 'PDF'   # 1
```

## AC3 — Image generation flow (mascot iteration)

```bash
# Script exists and is executable
test -x scripts/print/generate_mascot.py

# Help text documents the iteration model
python3 scripts/print/generate_mascot.py --help | grep -c 'reference'   # ≥1

# v1 generation (no reference) — already done in Phase 4a
test -f gatsby/src/images/brand/pashtelka-mascot.png
SIZE=$(stat -c%s gatsby/src/images/brand/pashtelka-mascot.png)
test "$SIZE" -gt 50000   # > 50 KB (sanity: real image, not a stub)

# Prompt file is committed for reproducibility
test -f assets/print/prompts/mascot-v1.txt
wc -w assets/print/prompts/mascot-v1.txt   # 200-300 words
```

Phase 4b verification (operator-driven):

- `python3 scripts/print/generate_mascot.py --prompt-file assets/print/prompts/mascot-v2.txt --reference gatsby/src/images/brand/pashtelka-mascot.png --output gatsby/src/images/brand/pashtelka-mascot.png`
- After each iteration, `~/workspace/scripts/tg-send.sh --photo …` ships the
  preview to the operator. Operator replies in chat:
  - "approve" → loop ends, next task starts
  - "regen" → run again with same prompt (different seed)
  - "edit prompt: …" → write `mascot-v(N+1).txt` and re-run

## AC4 — Mascot definition

```bash
# Final mascot lives at the canonical brand path
test -f gatsby/src/images/brand/pashtelka-mascot.png

# Image dimensions ≥ 1024x1024
file gatsby/src/images/brand/pashtelka-mascot.png | grep -E '102[4-9] x 102[4-9]|[1-9][0-9]{3,} x [1-9][0-9]{3,}'

# Used by welcome-landing AND print assets
grep -rln 'pashtelka-mascot' gatsby/src/pages/   # Phase 4b — must show ≥1 hit
grep -c 'pashtelka-mascot'   assets/print/sticker.svg     # ≥1 (referenced in default placeholder filename comment)
```

## AC5 — QR code quality

```bash
# Script exists
test -x scripts/print/generate_qr.py

# Generate the canonical sticker QR
python3 scripts/print/generate_qr.py \
  --url "https://pastelka.news/welcome/?utm_source=sticker&utm_campaign=2026-q2" \
  --output /tmp/qr-test \
  --size 1024

test -f /tmp/qr-test.png
test -f /tmp/qr-test.svg

# PNG sanity
SIZE=$(stat -c%s /tmp/qr-test.png)
test "$SIZE" -gt 1000   # > 1 KB

# Decode the QR back to the URL — proves it's a valid scannable QR
python3 - <<'EOF'
from PIL import Image
import sys
try:
    from pyzbar.pyzbar import decode
    decoded = decode(Image.open("/tmp/qr-test.png"))
    assert decoded, "no QR detected"
    url = decoded[0].data.decode()
    assert "pastelka.news/welcome/" in url, f"unexpected URL: {url}"
    print("OK:", url)
except ImportError:
    # pyzbar optional — fallback to file size + presence check
    print("pyzbar not installed; size check only:", __import__('os').stat("/tmp/qr-test.png").st_size)
EOF

# Module-size math at 35 mm sticker scale (informational)
python3 - <<'EOF'
import qrcode
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=4)
qr.add_data("https://pastelka.news/welcome/?utm_source=sticker&utm_campaign=2026-q2")
qr.make(fit=True)
modules = qr.modules_count + 8  # incl. quiet zone
mm_per_module = 35.0 / modules
print(f"version={qr.version}, modules={qr.modules_count}, total_with_border={modules}, mm/module={mm_per_module:.3f}")
assert mm_per_module >= 0.85, "QR module too small for 50cm scan distance — shorten URL"
EOF
```

## AC6 — File deliverables

Phase 4a:

```bash
test -f scripts/print/generate_mascot.py
test -f scripts/print/generate_qr.py
test -f scripts/print/svg_to_cmyk_pdf.py
test -f assets/print/sticker.svg
test -f assets/print/poster_a5.svg
test -f assets/print/README.md
test -f assets/print/prompts/mascot-v1.txt
test -f gatsby/src/images/brand/pashtelka-mascot.png
grep -c 'qrcode' requirements.txt   # ≥1
```

Phase 4b:

```bash
test -f assets/print/sticker.pdf       # operator-exported, git LFS
test -f assets/print/poster_a5.pdf     # operator-exported, git LFS
```

## AC7 — Print test loop

Out of scope for code-ready milestone. Documented in `assets/print/README.md`:

- 50 stickers + 20 posters in one Lisbon district (Arroios or Anjos).
- Track UTM-tagged scans in Plausible for 14 days.
- If unique-scan → TG-sub conversion > 2%: scale up. Else: revisit creative.

Verification command (post-distribution):

```bash
# Plausible dashboard check (manual, post-deploy):
echo "Open: https://plausible.io/pastelka.news"
echo "Filter: utm_source=sticker"
echo "Compare: welcome_view vs welcome_tg_click events"
```

## AC8 — Authoring tool (Affinity)

```bash
# Phase 4a — operator-readable handoff doc exists
test -f assets/print/README.md
grep -c 'Affinity Publisher' assets/print/README.md   # ≥1
grep -c 'PDF/X-1a:2003'      assets/print/README.md   # ≥1
grep -c 'FOGRA39'            assets/print/README.md   # ≥1
grep -c '300 DPI'            assets/print/README.md   # ≥1

# Phase 4b — Affinity export preset committed
test -f assets/print/affinity-print.afexport
```

The PDFs themselves come from the operator's Affinity export (Phase 4b).

## Layout safe-zone check (post-export, manual)

After the operator exports the PDFs from Affinity:

```bash
# pdfinfo to confirm dimensions
pdfinfo assets/print/sticker.pdf | grep -E 'Page size'      # 81 x 81 mm (or 229.6x229.6 pt)
pdfinfo assets/print/poster_a5.pdf | grep -E 'Page size'    # 154 x 216 mm

# Visual safe-zone overlay (manual) — open the PDF in Affinity, toggle
# rulers, confirm no critical text or QR module crosses the 5 mm safe-zone
# boundary.
```

## OG-card style alignment with Wave 2 brand

Compare the new mascot to the welcome-landing hero already shipped:

```bash
# Both mascot files exist; visually compare in TG (operator)
test -f gatsby/src/images/welcome/hero-placeholder.png       # Wave 2 placeholder
test -f gatsby/src/images/brand/pashtelka-mascot.png         # this feature

# After approval, both should show the same canonical mascot.
# Phase 4b updates welcome page imports to point at the brand asset.
```

## Final verification matrix

| AC | Phase | Command(s) | Pass criterion |
|----|-------|-----------|----------------|
| AC1 | 4b | `pdfinfo` + `file` on sticker.pdf | 81×81 mm CMYK PDF/X-1a |
| AC1 (proof) | 4a | `svg_to_cmyk_pdf.py` on sticker.svg | proof PDF generates |
| AC2 | 4b | `pdfinfo` on poster_a5.pdf | 154×216 mm CMYK PDF/X-1a |
| AC3 | 4a | `generate_mascot.py` runs, PNG > 50 KB | true |
| AC4 | 4a | `gatsby/src/images/brand/pashtelka-mascot.png` exists | true |
| AC5 | 4a | `generate_qr.py` + decode roundtrip + module-size math | URL decodes, mm/module ≥ 0.85 |
| AC6 | 4a | `test -f` on each deliverable | all present |
| AC6 | 4b | `test -f` on sticker.pdf + poster_a5.pdf | both present |
| AC7 | post | Plausible UTM filter, 14d window | conversion ≥ 2% |
| AC8 | 4a | grep on README.md for keywords | Affinity, PDF/X-1a, FOGRA39, 300 DPI present |
