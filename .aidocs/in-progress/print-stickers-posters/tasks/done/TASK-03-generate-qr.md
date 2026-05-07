# TASK-03 — QR code generator script

**Phase:** 4a
**Subject:** `scripts/print/generate_qr.py` — wraps the `qrcode` Python lib
to emit both PNG and SVG outputs at error-correction H, suitable for the
sticker (35 mm) and poster (35 mm) layouts.

## Files touched

- `scripts/print/generate_qr.py` (new, executable)
- `requirements.txt` (+= `qrcode[pil]>=7.4`)

## Approach

CLI flags:

- `--url` (required) — payload URL
- `--output` (required) — output prefix; script writes `<prefix>.png` and
  `<prefix>.svg`
- `--size` (default 1024) — PNG width in pixels
- `--border` (default 4) — quiet-zone modules

Internals:

```python
import qrcode
from qrcode.image.svg import SvgPathImage
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                   border=args.border)
qr.add_data(args.url)
qr.make(fit=True)

# PNG
img = qr.make_image(fill_color="black", back_color="white")
img = img.resize((args.size, args.size))   # PIL nearest-neighbour
img.save(prefix + ".png")

# SVG (vector, preferred for Affinity)
svg = qr.make_image(image_factory=SvgPathImage)
svg.save(prefix + ".svg")
```

Shebang `#!/usr/bin/env python3`, chmod +x.

## Success criterion

- `python3 scripts/print/generate_qr.py --url https://pastelka.news/welcome/ --output /tmp/qr-test --size 1024` produces:
  - `/tmp/qr-test.png` > 1 KB
  - `/tmp/qr-test.svg` > 100 B
- Decoding the PNG with `pyzbar` (if installed) or just inspecting size
  confirms it's a valid scannable QR.
- `qrcode[pil]>=7.4` line added to `requirements.txt`.

## Execution Report

### Status: COMPLETED

### What Was Done
- Wrote `scripts/print/generate_qr.py` (~110 lines): `qrcode` lib at
  error-correction `H`, border 4. Writes both `<prefix>.png` (raster, PIL
  nearest-neighbour resize to keep modules sharp) and `<prefix>.svg`
  (vector via `qrcode.image.svg.SvgPathImage` — preferred for Affinity).
- Added `qrcode[pil]>=7.4` to `requirements.txt`.
- Installed locally with `pip install --user --break-system-packages
  'qrcode[pil]>=7.4'` (PEP 668 environment).

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `scripts/print/generate_qr.py` | new (chmod +x) |
| pashtelka-faion-net | `requirements.txt` | += `qrcode[pil]>=7.4` |

### Tests
- `python3 scripts/print/generate_qr.py --url "https://pastelka.news/welcome/?utm_source=sticker&utm_campaign=2026-q2" --output /tmp/qr-test --size 1024` →
  - PNG 6.4 KB, 1024×1024 RGB — PASS (>1 KB).
  - SVG 18.4 KB, vector path — PASS.
  - QR version=8, 49×49 modules (full URL is 70 chars).

### Issues
- Module-size math: full UTM URL fits at v8 (49 modules + 8 border = 57).
  At 35 mm sticker scale that's 0.614 mm/module — **below** the 1.2 mm
  rule-of-thumb for 50 cm scan distance.
- Mitigation already noted in design.md / spec.md AC5: shorten URL to
  `https://pastelka.news/w/?s=lx` (29 chars → v4 → 33 modules → 0.854
  mm/module). Still below 1.2 mm but closer; phone cameras at <30 cm
  scan it fine. Re-evaluate after first physical print test.
- Decision deferred to Phase 4b: pick short-URL form before the print
  shop send.

