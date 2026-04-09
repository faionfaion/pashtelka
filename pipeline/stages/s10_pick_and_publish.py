"""Stage 10: Pick best unpublished article and publish to TG.

Used in 'publish' mode (9, 12, 15, 18).
Reads today's generated articles, picks one not yet posted to TG,
generates a caption, and sends photo+caption.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from pipeline.config import (
    CONTENT_DIR, IMAGES_DIR, MODEL_TG, SITE_BASE_URL,
    SOUND_ON_END, SOUND_ON_START, STATE_DIR,
    TG_BOT_TOKEN, TG_CHANNEL_ID,
)
from pipeline.prompts.builder import build_pick_publish_prompt
from pipeline.schemas import load_schema
from pipeline.sdk import structured_query
from pipeline.telegram import add_reaction, send_photo

logger = logging.getLogger(__name__)


def run() -> dict | None:
    """Pick best unpublished article, generate TG caption, publish. Returns info dict or None."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")

    # Load today's TG publish state
    tg_state_file = STATE_DIR / "tg_published" / f"{today_str}.json"
    tg_published: dict = {}
    if tg_state_file.exists():
        tg_published = json.loads(tg_state_file.read_text(encoding="utf-8"))

    already_posted_slugs = set(tg_published.values()) if isinstance(next(iter(tg_published.values()), None), str) else {v.get("slug", "") for v in tg_published.values()} if tg_published else set()

    # Find today's articles not yet posted to TG
    candidates = _find_candidates(today_str, already_posted_slugs)
    if not candidates:
        # Fallback: any article not yet TG-published
        candidates = _find_all_candidates(already_posted_slugs)

    if not candidates:
        logger.info("No unpublished articles available for TG")
        return None

    # Pick the first candidate (newest unposted)
    slug, title, article_text = candidates[0]
    article_url = f"{SITE_BASE_URL}/{slug}/"

    # Generate TG caption
    caption = _generate_caption(title, article_text, article_url)

    # Find image
    image_path = _find_image(slug)
    if not image_path:
        logger.warning("No image for %s, skipping TG publish", slug)
        return None

    # Determine silent mode
    lisbon_hour = now.hour
    silent = not (SOUND_ON_START <= lisbon_hour < SOUND_ON_END)

    # Publish
    msg_id = send_photo(
        chat_id=TG_CHANNEL_ID,
        image_path=image_path,
        caption=caption,
        bot_token=TG_BOT_TOKEN,
        silent=silent,
    )

    if msg_id:
        add_reaction(TG_CHANNEL_ID, msg_id, "\U0001f525", TG_BOT_TOKEN)
        _mark_tg_published(today_str, now.hour, slug, msg_id)
        logger.info("TG published: %s -> msg %d", slug, msg_id)
        return {"slug": slug, "msg_id": msg_id, "url": article_url}

    logger.error("Failed to publish %s to TG", slug)
    return None


def _find_candidates(today_str: str, exclude: set[str]) -> list[tuple[str, str, str]]:
    """Find today's articles not yet posted to TG."""
    candidates = []
    for md in sorted(CONTENT_DIR.glob("*.md"), reverse=True):
        slug = md.stem
        if slug in exclude:
            continue
        text = md.read_text(encoding="utf-8")
        # Check if article is from today
        if f'date: "{today_str}"' in text:
            title = _extract_title(text)
            body = _extract_body(text)
            candidates.append((slug, title, body))
    return candidates


def _find_all_candidates(exclude: set[str]) -> list[tuple[str, str, str]]:
    """Fallback: find any articles not yet TG-published."""
    candidates = []
    for md in sorted(CONTENT_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        slug = md.stem
        if slug in exclude:
            continue
        text = md.read_text(encoding="utf-8")
        title = _extract_title(text)
        body = _extract_body(text)
        candidates.append((slug, title, body))
        if len(candidates) >= 5:
            break
    return candidates


def _extract_title(text: str) -> str:
    for line in text.split("\n"):
        if line.startswith("title:"):
            return line.split('"')[1] if '"' in line else line.split(": ", 1)[1]
    return ""


def _extract_body(text: str) -> str:
    lines = text.split("\n")
    in_fm = False
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if in_fm:
                body_start = i + 1
                break
            in_fm = True
    return "\n".join(lines[body_start:])[:2000]


def _find_image(slug: str) -> str | None:
    for ext in (".jpg", ".jpeg", ".png"):
        p = IMAGES_DIR / f"{slug}{ext}"
        if p.exists():
            return str(p)
    return None


def _generate_caption(title: str, article_text: str, article_url: str) -> str:
    system, prompt = build_pick_publish_prompt(title, article_text)

    result = structured_query(
        prompt=prompt,
        system_prompt=system,
        schema=load_schema("tg_post"),
        model=MODEL_TG,
    )

    hook = result["hook"]
    body = result["body"]
    vocab = result.get("vocab", [])

    vocab_lines = [f"{v['pt']} — <tg-spoiler>{v['uk']}</tg-spoiler>" for v in vocab[:5]]
    vocab_block = "\n".join(vocab_lines)

    parts = [
        f"<b>{hook}</b>",
        "",
        body,
        "",
        f'<a href="{article_url}">Дізнатись більше \u2192</a>',
        "",
        "\U0001f4d6 Словничок:",
        vocab_block,
        "",
        '<a href="https://t.me/pashtelka_news">\U0001f1f5\U0001f1f9 Паштелька News</a>',
    ]

    return "\n".join(parts)


def _mark_tg_published(today_str: str, hour: int, slug: str, msg_id: int) -> None:
    tg_dir = STATE_DIR / "tg_published"
    tg_dir.mkdir(parents=True, exist_ok=True)
    state_file = tg_dir / f"{today_str}.json"

    data: dict = {}
    if state_file.exists():
        data = json.loads(state_file.read_text(encoding="utf-8"))

    data[str(hour)] = {"slug": slug, "msg_id": msg_id}
    state_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
