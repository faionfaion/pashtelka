"""Stage 11: Evening digest — single daily TG post with 10 news + glossary + premium image.

Used in 'digest' mode (21:00 Lisbon = 20:00 UTC, April/WEST).

- Collects today's news articles (type=news only) from CONTENT_DIR
- Generates structured digest via LLM: intro, 10 items, 2 glossary words, image prompt
- Generates a premium cityscape image via gpt-image-1 quality=high
- Sends single TG post (photo + caption); splits if caption exceeds 1024 chars
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from pipeline.config import (
    CONTENT_DIR, DIGEST_IMAGE_QUALITY, MODEL_TG, SITE_BASE_URL,
    SOUND_ON_END, SOUND_ON_START, SPONSOR_LINE,
    TG_BOT_TOKEN, TG_CHANNEL_ID,
)
from pipeline.image_gen import generate_image
from pipeline.prompts.builder import build_digest_prompt
from pipeline.schemas import load_schema
from pipeline.sdk import structured_query
from pipeline.telegram import add_reaction, send_photo, send_text

logger = logging.getLogger(__name__)

TG_CAPTION_LIMIT = 4096  # Extended caption limit (Telegram Premium / bot upgrade)
MIN_NEWS_FOR_DIGEST = 5  # absolute floor; below this, skip digest

WEEKDAYS_UK = [
    "Понеділок", "Вівторок", "Середа", "Четвер",
    "П'ятниця", "Субота", "Неділя",
]


def run() -> dict | None:
    """Generate and publish evening digest to TG. Returns info dict or None."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    weekday_uk = WEEKDAYS_UK[now.weekday()]

    articles = _collect_today_news(today_str)
    if len(articles) < MIN_NEWS_FOR_DIGEST:
        logger.info("Only %d news articles today, skipping digest (min=%d)",
                    len(articles), MIN_NEWS_FOR_DIGEST)
        return None

    logger.info("Building digest for %d news articles", len(articles))

    result = _generate_digest(articles, today_str, weekday_uk)
    intro = result["intro"]
    items = result["items"]
    glossary = result["glossary"]
    image_prompt = result["image_prompt"]

    digest_slug = f"digest-{today_str}"
    image_path = generate_image(
        prompt=image_prompt,
        slug=digest_slug,
        comic_mode=True,
        quality=DIGEST_IMAGE_QUALITY,
    )

    if not image_path:
        logger.error("Digest image generation failed — aborting digest")
        return None

    caption = _build_caption(intro, items, glossary)

    # WEST (April) is UTC+1; silent window 08:00-22:00 Lisbon
    lisbon_hour = (now.hour + 1) % 24
    silent = not (SOUND_ON_START <= lisbon_hour < SOUND_ON_END)

    msg_id = _send_digest(str(image_path), caption, silent)

    if msg_id:
        add_reaction(TG_CHANNEL_ID, msg_id, "\U0001f525", TG_BOT_TOKEN)
        logger.info(
            "Digest published: msg %d (%d news, glossary: %s)",
            msg_id, len(items),
            ", ".join(f"{g['pt']}→{g['ua']}" for g in glossary),
        )
        return {
            "type": "digest",
            "msg_id": msg_id,
            "article_count": len(items),
            "glossary": glossary,
            "image_path": str(image_path),
        }

    logger.error("Failed to publish digest")
    return None


def _collect_today_news(today_str: str) -> list[dict]:
    """Return list of {slug, title, body} for today's type=news articles only."""
    news = []
    for md in sorted(CONTENT_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        text = md.read_text(encoding="utf-8")
        if f'date: "{today_str}"' not in text:
            continue

        article_type = _fm_value(text, "type")
        if article_type and article_type != "news":
            continue

        title = _fm_value(text, "title")
        slug = md.stem
        body = _strip_frontmatter(text)[:400]
        news.append({"slug": slug, "title": title, "body": body})
    return news


def _fm_value(text: str, key: str) -> str:
    """Extract a single YAML frontmatter field. Returns '' if not found."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith(f"{key}:"):
            val = line.split(":", 1)[1].strip()
            if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
                val = val[1:-1]
            return val
    return ""


def _strip_frontmatter(text: str) -> str:
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                return "\n".join(lines[i + 1:])
    return text


def _generate_digest(articles: list[dict], today_str: str, weekday_uk: str) -> dict:
    articles_text = "\n\n".join(
        f"slug: {a['slug']}\ntitle: {a['title']}\npreview: {a['body'][:200]}"
        for a in articles
    )
    system, prompt = build_digest_prompt(articles_text, today_str, weekday_uk)
    return structured_query(
        prompt=prompt,
        system_prompt=system,
        schema=load_schema("digest"),
        model=MODEL_TG,
    )


def _build_caption(intro: str, items: list[dict], glossary: list[dict]) -> str:
    parts = [
        "<b>\U0001f4f0 Дайджест дня</b>",
        "",
        intro,
        "",
    ]
    for item in items:
        emoji = item.get("emoji", "\u2022")
        title = item["title"]
        hook = item.get("hook", "")
        slug = item["slug"]
        url = f"{SITE_BASE_URL}/{slug}/"
        parts.append(f'{emoji} <a href="{url}"><b>{title}</b></a>')
        if hook:
            parts.append(hook)
        parts.append("")

    if SPONSOR_LINE:
        parts.append(f"\U0001f4ac {SPONSOR_LINE}")
        parts.append("")

    parts.append("\U0001f4d6 <b>Словничок:</b>")
    for g in glossary:
        parts.append(f"{g['pt']} — {g['ua']}")
    parts.append("")

    parts.append('\U0001f1f5\U0001f1f9 <a href="https://t.me/pashtelka_news">Паштелька News</a>')

    return "\n".join(parts)


def _send_digest(image_path: str, caption: str, silent: bool) -> int | None:
    """Send photo + caption. Splits into photo + reply-text if caption > 1024 chars."""
    if len(caption) <= TG_CAPTION_LIMIT:
        return send_photo(
            chat_id=TG_CHANNEL_ID,
            image_path=image_path,
            caption=caption,
            bot_token=TG_BOT_TOKEN,
            silent=silent,
        )

    split_marker = "\U0001f4d6 <b>Словничок:</b>"
    idx = caption.find(split_marker)
    if idx == -1:
        idx = TG_CAPTION_LIMIT - 50

    head = caption[:idx].rstrip()
    tail = caption[idx:].lstrip()

    msg_id = send_photo(
        chat_id=TG_CHANNEL_ID,
        image_path=image_path,
        caption=head[:TG_CAPTION_LIMIT],
        bot_token=TG_BOT_TOKEN,
        silent=silent,
    )
    if not msg_id:
        return None

    send_text(
        chat_id=TG_CHANNEL_ID,
        caption=tail,
        silent=silent,
        bot_token=TG_BOT_TOKEN,
    )
    return msg_id
