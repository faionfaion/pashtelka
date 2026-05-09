"""Stage 11: Evening digest — single daily TG post with 10 news + glossary + premium image.

Used in 'digest' mode (21:00 Lisbon = 20:00 UTC, April/WEST).

- Collects today's news articles (type=news only) from CONTENT_DIR
- Generates structured digest via LLM: intro, 10 items, 2 glossary words, image prompt
- Generates a premium cityscape image via gpt-image-1 quality=high
- Sends UA digest to TG_CHANNEL_ID
- pt-translation-b1: when TG_CHANNEL_PT_ID is set, translates the UA digest
  (intro + items) into B1 PT and sends the same image with PT caption to
  TG_CHANNEL_PT_ID. PT digest skips the glossary block. PT failures are
  logged but never fail the run — UA send always wins.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from pipeline.config import (
    CONTENT_DIR, DIGEST_IMAGE_QUALITY, SITE_BASE_URL,
    SOUND_ON_END, SOUND_ON_START, SPONSOR_LINE, STATE_DIR,
    TG_BOT_TOKEN, TG_CHANNEL_ID, TG_CHANNEL_PT_ID,
    TG_CHANNEL_PT_USERNAME, TG_CHANNEL_USERNAME,
)
from pipeline.image_gen import generate_image
from pipeline.llm import dispatch_structured, dispatch_translate
from pipeline.prompts.builder import (
    build_digest_prompt, build_translate_digest_pt_prompt,
)
from pipeline.schemas import load_schema
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

    marker = STATE_DIR / "tg_published" / f"digest-{today_str}.json"
    if marker.exists():
        logger.info("Digest for %s already published (%s); skipping", today_str, marker.name)
        return None

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

    caption_ua = _build_caption(intro, items, glossary, lang="uk")

    # WEST (April) is UTC+1; silent window 08:00-22:00 Lisbon
    lisbon_hour = (now.hour + 1) % 24
    silent = not (SOUND_ON_START <= lisbon_hour < SOUND_ON_END)

    # UA-side send: existing channel.
    msg_id_ua = _send_digest(str(image_path), caption_ua, silent, TG_CHANNEL_ID)
    if not msg_id_ua:
        logger.error("Failed to publish UA digest")
        return None
    add_reaction(TG_CHANNEL_ID, msg_id_ua, "\U0001f525", TG_BOT_TOKEN)
    logger.info(
        "UA digest published: msg %d (%d news, glossary: %s)",
        msg_id_ua, len(items),
        ", ".join(f"{g['pt']}->{g['ua']}" for g in glossary),
    )

    # PT-side send: only when the operator has wired the chat_id.
    msg_id_pt = None
    if TG_CHANNEL_PT_ID:
        try:
            result_pt = _translate_digest_to_pt(result)
            caption_pt = _build_caption(
                result_pt["intro"], result_pt["items"], glossary=[],
                lang="pt",
            )
            msg_id_pt = _send_digest(str(image_path), caption_pt, silent, TG_CHANNEL_PT_ID)
            if msg_id_pt:
                add_reaction(TG_CHANNEL_PT_ID, msg_id_pt, "\U0001f525", TG_BOT_TOKEN)
                logger.info(
                    "PT digest published: msg %d (%d news)",
                    msg_id_pt, len(result_pt["items"]),
                )
            else:
                logger.error("Failed to publish PT digest (UA already sent)")
        except Exception:
            logger.exception("PT digest failed (UA already sent)")
    else:
        logger.warning(
            "TG_CHANNEL_PT_ID not set; skipping PT digest. Operator: create "
            "@%s, add @nero_open_bot as admin, then export TG_CHANNEL_PT_ID.",
            TG_CHANNEL_PT_USERNAME,
        )

    info = {
        "type": "digest",
        "msg_id": msg_id_ua,
        "msg_id_pt": msg_id_pt,
        "article_count": len(items),
        "glossary": glossary,
        "image_path": str(image_path),
    }
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        json.dumps({**info, "published_at": now.isoformat()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return info


def _collect_today_news(today_str: str) -> list[dict]:
    """Return list of {slug, title, body} for today's type=news articles only.

    Articles live as `content/<slug>/uk.md` (per-locale layout introduced by
    pt-translation-b1). Slug is the parent directory name.
    """
    news = []
    for md in sorted(CONTENT_DIR.glob("*/uk.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        text = md.read_text(encoding="utf-8")
        if f'date: "{today_str}"' not in text:
            continue

        article_type = _fm_value(text, "type")
        if article_type and article_type != "news":
            continue

        title = _fm_value(text, "title")
        slug = md.parent.name
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
    return dispatch_structured(
        prompt=prompt,
        system=system,
        schema=load_schema("digest"),
        stage="digest",
    )


def _build_caption(intro: str, items: list[dict], glossary: list[dict],
                    *, lang: str = "uk") -> str:
    """Build the TG caption for either UA or PT digest.

    PT digests skip the glossary block (PT readers don't need PT->UA word
    cards). URL prefix is /uk/<slug>/ for UA digest, /pt/<slug>/ for PT.
    """
    if lang == "pt":
        title_line = "<b>\U0001f4f0 Resumo do dia</b>"
        url_prefix = "pt"
        footer = (
            f'\U0001f1fa\U0001f1e6 <a href="https://t.me/{TG_CHANNEL_PT_USERNAME}">'
            "Pastelka News</a>"
        )
        glossary_label = None
    else:
        title_line = "<b>\U0001f4f0 Дайджест дня</b>"
        url_prefix = "uk"
        footer = (
            f'\U0001f1fa\U0001f1e6 <a href="https://t.me/{TG_CHANNEL_USERNAME}">'
            "Паштелька News</a>"
        )
        glossary_label = "\U0001f4d6 <b>Словничок:</b>"

    parts = [title_line, "", intro, ""]
    for item in items:
        emoji = item.get("emoji", "•")
        title = item["title"]
        hook = item.get("hook", "")
        slug = item["slug"]
        url = f"{SITE_BASE_URL}/{url_prefix}/{slug}/"
        parts.append(f'{emoji} <a href="{url}"><b>{title}</b></a>')
        if hook:
            parts.append(hook)
        parts.append("")

    if SPONSOR_LINE:
        parts.append(f"\U0001f4ac {SPONSOR_LINE}")
        parts.append("")

    if glossary and glossary_label:
        parts.append(glossary_label)
        for g in glossary:
            parts.append(f"{g['pt']} — {g['ua']}")
        parts.append("")

    parts.append(footer)
    return "\n".join(parts)


def _send_digest(image_path: str, caption: str, silent: bool,
                  chat_id: str = TG_CHANNEL_ID) -> int | None:
    """Send photo + caption to chat_id. Splits into photo + reply-text if caption > limit."""
    if len(caption) <= TG_CAPTION_LIMIT:
        return send_photo(
            chat_id=chat_id,
            image_path=image_path,
            caption=caption,
            bot_token=TG_BOT_TOKEN,
            silent=silent,
        )

    # Split marker: UA glossary heading. PT digests skip the glossary so a
    # PT caption that needs splitting will fall through to the char-index
    # split — fine because PT captions are shorter than UA + glossary.
    split_marker = "\U0001f4d6 <b>Словничок:</b>"
    idx = caption.find(split_marker)
    if idx == -1:
        idx = TG_CAPTION_LIMIT - 50

    head = caption[:idx].rstrip()
    tail = caption[idx:].lstrip()

    msg_id = send_photo(
        chat_id=chat_id,
        image_path=image_path,
        caption=head[:TG_CAPTION_LIMIT],
        bot_token=TG_BOT_TOKEN,
        silent=silent,
    )
    if not msg_id:
        return None

    send_text(
        chat_id=chat_id,
        caption=tail,
        silent=silent,
        bot_token=TG_BOT_TOKEN,
    )
    return msg_id


def _translate_digest_to_pt(digest_ua: dict) -> dict:
    """Translate the UA digest (intro + 10 items) into B1 Portuguese.

    Returns dict with `intro` and `items` (each item: emoji, title, hook,
    slug). Glossary is dropped — PT readers don't need PT->UA card.
    Image is reused, so image_prompt is not translated.
    """
    system, prompt = build_translate_digest_pt_prompt(digest_ua)
    schema = load_schema("digest_pt")
    return dispatch_translate(prompt, system=system, schema=schema, lang="pt")
