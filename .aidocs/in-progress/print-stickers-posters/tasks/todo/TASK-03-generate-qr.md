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
