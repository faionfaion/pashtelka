#!/usr/bin/env python3
"""svg_to_cmyk_pdf.py — convert an SVG layout to a CMYK proofing PDF.

This script is a CLI **proofing** path. The final print PDFs come from
Affinity Publisher with PDF/X-1a:2003 + FOGRA39 ICC. See
`assets/print/README.md` for the operator-side flow.

Two paths in priority order:

1. **Inkscape CLI** (preferred): `inkscape --export-type=pdf …`. If
   `ghostscript` and the FOGRA39 ICC profile are also available, post-
   process the PDF through `gs` to swap the colour space to CMYK with the
   ICC profile attached.

2. **Pillow + reportlab fallback**: rasterise SVG via `cairosvg` →
   PIL.Image.convert("CMYK") (naive sRGB→CMYK, no ICC gamut mapping) →
   embed in a single-page PDF via reportlab at the SVG's physical size.
   This is a **proofing** path only — the colour mapping is best-effort.

If neither toolchain is available, exits with a clear install hint.

Operator install (Debian/Ubuntu):

    sudo apt-get install -y inkscape ghostscript icc-profiles-free

Or pip-only fallback:

    pip install --user --break-system-packages cairosvg reportlab
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_ICC = "/usr/share/color/icc/ISOcoated_v2_eci.icc"


def parse_svg_dimensions(svg_path: Path) -> tuple[float, float]:
    """Return (width_mm, height_mm) parsed from the SVG root.

    Supports `width="81mm"` and `height="216mm"` style attributes (which is
    what our layout SVGs ship with). Falls back to viewBox if width/height
    are unitless. Raises if neither is parseable.
    """
    text = svg_path.read_text()
    # Look at the first <svg ...> tag only.
    m = re.search(r"<svg[^>]+>", text, flags=re.IGNORECASE)
    if not m:
        raise ValueError(f"no <svg> root in {svg_path}")
    head = m.group(0)
    w = re.search(r'\bwidth="([\d.]+)mm"', head)
    h = re.search(r'\bheight="([\d.]+)mm"', head)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    # Fallback: viewBox in user units (assumes 1 unit = 1 mm in our layouts).
    vb = re.search(r'\bviewBox="\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)"', head)
    if vb:
        return float(vb.group(1)), float(vb.group(2))
    raise ValueError(f"cannot parse width/height from {svg_path}")


def have(tool: str) -> str | None:
    return shutil.which(tool)


def inkscape_path(in_svg: Path, out_pdf: Path) -> bool:
    """Try Inkscape. Return True on success, False if Inkscape isn't there."""
    inkscape = have("inkscape")
    if not inkscape:
        return False
    cmd = [
        inkscape,
        "--export-type=pdf",
        "--export-pdf-version=1.5",
        "--export-text-to-path",
        "--export-area-page",
        f"--export-filename={out_pdf}",
        str(in_svg),
    ]
    print(f"  → {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    return True


def cmyk_via_ghostscript(
    in_pdf: Path, out_pdf: Path, icc: Path
) -> bool:
    """Best-effort CMYK + ICC conversion via ghostscript. Skips if missing."""
    gs = have("gs") or have("ghostscript")
    if not gs:
        print("  ! ghostscript not installed — leaving PDF in RGB.")
        print("    apt-get install -y ghostscript icc-profiles-free")
        if in_pdf != out_pdf:
            out_pdf.write_bytes(in_pdf.read_bytes())
        return False
    if not icc.exists():
        print(f"  ! ICC profile not found: {icc}")
        print("    apt-get install -y icc-profiles-free  # ships ISOcoated_v2_eci.icc")
        if in_pdf != out_pdf:
            out_pdf.write_bytes(in_pdf.read_bytes())
        return False
    cmd = [
        gs,
        "-dSAFER",
        "-dBATCH",
        "-dNOPAUSE",
        "-sDEVICE=pdfwrite",
        "-sProcessColorModel=DeviceCMYK",
        "-sColorConversionStrategy=CMYK",
        "-dPDFX=true",
        f"-sOutputICCProfile={icc}",
        f"-sOutputFile={out_pdf}",
        str(in_pdf),
    ]
    print(f"  → {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    return True


def fallback_path(in_svg: Path, out_pdf: Path) -> bool:
    """cairosvg → PIL CMYK → reportlab single-page PDF. Proofing only."""
    try:
        import cairosvg  # noqa: F401
    except ImportError:
        return False
    try:
        from PIL import Image  # noqa: F401
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
    except ImportError:
        sys.stderr.write(
            "FATAL: reportlab + Pillow required for the cairosvg fallback.\n"
            "  pip install --user --break-system-packages reportlab pillow\n"
        )
        return False

    import cairosvg
    from PIL import Image
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    width_mm, height_mm = parse_svg_dimensions(in_svg)
    print(f"  SVG size: {width_mm}×{height_mm} mm")

    sys.stderr.write(
        "WARN: using cairosvg+PIL+reportlab fallback. PIL.convert('CMYK') "
        "is a naive sRGB→CMYK without ICC gamut mapping — this PDF is "
        "PROOFING ONLY. Final print PDFs MUST come from Affinity Publisher "
        "with FOGRA39 ICC.\n"
    )

    # Rasterise at 300 DPI.
    dpi = 300
    px_w = int(round(width_mm / 25.4 * dpi))
    px_h = int(round(height_mm / 25.4 * dpi))
    print(f"  rasterising at {dpi} DPI → {px_w}×{px_h} px")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        cairosvg.svg2png(
            url=str(in_svg),
            write_to=tmp.name,
            output_width=px_w,
            output_height=px_h,
        )
        png_tmp = Path(tmp.name)

    img = Image.open(png_tmp).convert("CMYK")
    cmyk_tmp = png_tmp.with_suffix(".cmyk.jpg")
    img.save(cmyk_tmp, format="JPEG", quality=95)

    c = canvas.Canvas(
        str(out_pdf), pagesize=(width_mm * mm, height_mm * mm)
    )
    c.drawImage(
        str(cmyk_tmp), 0, 0, width=width_mm * mm, height=height_mm * mm
    )
    c.showPage()
    c.save()

    png_tmp.unlink(missing_ok=True)
    cmyk_tmp.unlink(missing_ok=True)
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Convert SVG → CMYK PDF (proofing path; final PDFs from Affinity)"
    )
    p.add_argument("--in", dest="in_svg", required=True, help="Input SVG")
    p.add_argument("--out", dest="out_pdf", required=True, help="Output PDF")
    p.add_argument(
        "--icc",
        default=DEFAULT_ICC,
        help=f"ICC profile path (default {DEFAULT_ICC} — FOGRA39)",
    )
    args = p.parse_args(argv)

    in_svg = Path(args.in_svg)
    out_pdf = Path(args.out_pdf)
    icc = Path(args.icc)

    if not in_svg.exists():
        sys.stderr.write(f"FATAL: input not found: {in_svg}\n")
        return 2
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    print(f"Converting {in_svg} → {out_pdf}")

    # Path 1: Inkscape (preferred).
    if have("inkscape"):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as t:
            tmp_pdf = Path(t.name)
        try:
            inkscape_path(in_svg, tmp_pdf)
            cmyk_via_ghostscript(tmp_pdf, out_pdf, icc)
        finally:
            tmp_pdf.unlink(missing_ok=True)
        print(f"OK  wrote {out_pdf} ({out_pdf.stat().st_size / 1024:.1f} KB)")
        return 0

    # Path 2: cairosvg fallback.
    if fallback_path(in_svg, out_pdf):
        print(f"OK  wrote {out_pdf} ({out_pdf.stat().st_size / 1024:.1f} KB)")
        return 0

    # Neither path available — fail with documented install hint.
    sys.stderr.write(
        "FATAL: SVG rasteriser missing.\n"
        "Install Inkscape (preferred):\n"
        "  sudo apt-get install -y inkscape ghostscript icc-profiles-free\n"
        "Or the pip fallback:\n"
        "  pip install --user --break-system-packages cairosvg reportlab\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
