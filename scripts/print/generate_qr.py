#!/usr/bin/env python3
"""generate_qr.py — emit a QR code as PNG + SVG for sticker / poster use.

Wraps the `qrcode` Python lib at error-correction level H (30%) so the QR
survives partial occlusion (rain stains, scratches). PNG is a raster
suitable for ImageMagick or PIL pipelines; SVG is the preferred input for
Affinity Publisher because it stays crisp at any resolution.

Usage:
    python3 scripts/print/generate_qr.py \\
        --url "https://pastelka.news/welcome/?utm_source=sticker" \\
        --output /tmp/qr-sticker \\
        --size 1024

Writes <output>.png and <output>.svg side by side. Idempotent — re-runs
overwrite cleanly.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _build_qr(url: str, border: int):
    import qrcode

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr


def write_png(qr, path: Path, size_px: int) -> None:
    """Render the QR matrix to a square PNG of `size_px` width via PIL.

    qrcode.make_image gives us a 1-bit matrix; we resize with nearest-
    neighbour to keep the modules sharp at the target raster size.
    """
    img = qr.make_image(fill_color="black", back_color="white")
    pil = img.convert("RGB")
    from PIL import Image

    pil = pil.resize((size_px, size_px), Image.NEAREST)
    pil.save(path, format="PNG", optimize=True)


def write_svg(qr, path: Path) -> None:
    """Render the QR as a vector SVG path image (preferred for Affinity)."""
    from qrcode.image.svg import SvgPathImage

    svg = qr.make_image(image_factory=SvgPathImage)
    # qrcode SvgPathImage exposes .save(stream); use a binary stream so the
    # output is byte-identical across runs.
    with open(path, "wb") as fh:
        svg.save(fh)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--url", required=True, help="Payload URL")
    p.add_argument(
        "--output",
        required=True,
        help="Output path prefix (writes <prefix>.png and <prefix>.svg)",
    )
    p.add_argument(
        "--size",
        type=int,
        default=1024,
        help="PNG width in pixels (default 1024)",
    )
    p.add_argument(
        "--border",
        type=int,
        default=4,
        help="QR quiet-zone in modules (default 4 — standard)",
    )
    args = p.parse_args(argv)

    try:
        import qrcode  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "FATAL: `qrcode` not installed.\n"
            "  pip install --user 'qrcode[pil]>=7.4'\n"
            "or with system override:\n"
            "  pip install --user --break-system-packages 'qrcode[pil]>=7.4'\n"
        )
        return 2

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    png_path = out.with_suffix(".png")
    svg_path = out.with_suffix(".svg")

    qr = _build_qr(args.url, args.border)

    write_png(qr, png_path, args.size)
    write_svg(qr, svg_path)

    png_size = png_path.stat().st_size
    svg_size = svg_path.stat().st_size
    modules = qr.modules_count
    total_with_border = modules + args.border * 2
    print(
        f"OK  url={args.url!r}\n"
        f"    version={qr.version} modules={modules}x{modules} "
        f"(with border: {total_with_border}x{total_with_border})\n"
        f"    {png_path}: {png_size / 1024:.1f} KB\n"
        f"    {svg_path}: {svg_size / 1024:.1f} KB"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
