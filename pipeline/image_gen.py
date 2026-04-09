"""Image generation: comic-style illustrations via OpenAI gpt-image-1."""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

import requests

from pipeline.config import IMAGES_DIR

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get(
    "OPENAI_API_KEY",
    "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",
)

STYLE_PREFIX = (
    "Colorful comic book illustration style, clean bold lines, warm pastel color palette "
    "inspired by Portuguese azulejo tiles. No text, no speech bubbles, no watermarks. "
    "Include subtle Portuguese visual elements (yellow tram, sardines, pastel de nata, "
    "azulejo patterns, Tagus river). "
)


def generate_image(prompt: str, slug: str) -> Path | None:
    """Generate a comic-style illustration and save to images dir.

    Args:
        prompt: Image description (in English).
        slug: Article slug for filename.

    Returns:
        Path to saved image, or None on failure.
    """
    if not OPENAI_API_KEY:
        logger.warning("No OPENAI_API_KEY — skipping image generation")
        return None

    full_prompt = f"{STYLE_PREFIX}{prompt}"

    try:
        resp = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-image-1",
                "prompt": full_prompt,
                "n": 1,
                "size": "1536x1024",  # landscape for article headers
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()

        # gpt-image-1 returns base64
        image_data = data["data"][0]
        if "b64_json" in image_data:
            img_bytes = base64.b64decode(image_data["b64_json"])
        elif "url" in image_data:
            img_resp = requests.get(image_data["url"], timeout=60)
            img_resp.raise_for_status()
            img_bytes = img_resp.content
        else:
            logger.error("No image data in response")
            return None

        IMAGES_DIR.mkdir(parents=True, exist_ok=True)

        # Convert to JPEG for smaller file size (TG needs < 5MB for previews)
        out_path = IMAGES_DIR / f"{slug}.jpg"
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(img_bytes))
            img = img.convert("RGB")
            # Resize if too large (max 1200px wide for web)
            if img.width > 1200:
                ratio = 1200 / img.width
                img = img.resize((1200, int(img.height * ratio)), Image.LANCZOS)
            img.save(out_path, "JPEG", quality=85, optimize=True)
        except ImportError:
            # Fallback: save as PNG if Pillow not installed
            out_path = IMAGES_DIR / f"{slug}.png"
            out_path.write_bytes(img_bytes)

        logger.info("Image saved: %s (%d KB)", out_path, out_path.stat().st_size // 1024)
        return out_path

    except requests.exceptions.HTTPError as e:
        logger.error("OpenAI API error: %s — %s", e.response.status_code,
                     e.response.text[:300] if e.response else "")
        return None
    except Exception:
        logger.error("Image generation failed", exc_info=True)
        return None
