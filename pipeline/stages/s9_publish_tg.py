"""Stage 9: Publish TG — send the teaser to @pashtelka_news."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from pipeline.config import (
    MAX_TG_CAPTION, SITE_BASE_URL, SOUND_ON_END, SOUND_ON_START,
    STATE_DIR, TG_BOT_TOKEN, TG_BUTTON_LABEL, TG_CHANNEL_ID,
)
from pipeline.context import PipelineContext
from pipeline.telegram import send_text, add_reaction

logger = logging.getLogger(__name__)


class PublishError(Exception):
    """Site not OK, refusing to publish."""


def run(ctx: PipelineContext) -> None:
    if not ctx.site_ok:
        raise PublishError("Site verification failed — refusing to publish to Telegram")

    article_url = f"{SITE_BASE_URL}/{ctx.slug}/"

    # Determine silent mode
    now = datetime.now(timezone.utc)
    lisbon_hour = now.hour  # Close enough for UTC+0/+1
    silent = not (SOUND_ON_START <= lisbon_hour < SOUND_ON_END)

    # Trim TG post if needed
    tg_text = ctx.tg_post
    if len(tg_text) > MAX_TG_CAPTION:
        # Trim to last complete sentence before limit
        tg_text = tg_text[:MAX_TG_CAPTION]
        last_period = tg_text.rfind(".")
        if last_period > MAX_TG_CAPTION * 0.7:
            tg_text = tg_text[:last_period + 1]

    # Send to Telegram
    msg_id = send_text(
        chat_id=TG_CHANNEL_ID,
        caption=tg_text,
        preview_url=article_url,
        silent=silent,
        button_url=article_url,
        button_text=TG_BUTTON_LABEL,
        bot_token=TG_BOT_TOKEN,
    )

    if msg_id:
        add_reaction(TG_CHANNEL_ID, msg_id, "🔥", TG_BOT_TOKEN)
        ctx.msg_id = msg_id
        logger.info("Published to @pashtelka_news: msg_id=%d (silent=%s)", msg_id, silent)

        # Save to posted state
        _mark_posted(ctx, msg_id)
    else:
        logger.error("Failed to publish to Telegram")


def _mark_posted(ctx: PipelineContext, msg_id: int) -> None:
    """Mark the slot as posted in today's state file."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    posted_dir = STATE_DIR / "posted"
    posted_dir.mkdir(parents=True, exist_ok=True)
    state_file = posted_dir / f"{today_str}.json"

    posted: dict = {}
    if state_file.exists():
        posted = json.loads(state_file.read_text(encoding="utf-8"))

    posted[str(ctx.slot_hour)] = {
        "slug": ctx.slug,
        "msg_id": msg_id,
        "type": ctx.slot_type,
        "title": ctx.title,
    }

    state_file.write_text(
        json.dumps(posted, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
