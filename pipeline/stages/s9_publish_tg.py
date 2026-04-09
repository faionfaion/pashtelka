"""Stage 9: Publish TG — send photo+caption to @pashtelka_news."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from pipeline.config import (
    IMAGES_DIR, SITE_BASE_URL, SOUND_ON_END, SOUND_ON_START,
    STATE_DIR, TG_BOT_TOKEN, TG_CHANNEL_ID,
)
from pipeline.context import PipelineContext
from pipeline.telegram import send_photo, add_reaction

logger = logging.getLogger(__name__)


class PublishError(Exception):
    """Site not OK, refusing to publish."""


def run(ctx: PipelineContext) -> None:
    if not ctx.site_ok:
        raise PublishError("Site verification failed — refusing to publish to Telegram")

    # Determine silent mode
    now = datetime.now(timezone.utc)
    lisbon_hour = now.hour
    silent = not (SOUND_ON_START <= lisbon_hour < SOUND_ON_END)

    # Find image file
    image_path = None
    for ext in [".jpg", ".png"]:
        candidate = IMAGES_DIR / f"{ctx.slug}{ext}"
        if candidate.exists():
            image_path = str(candidate)
            break

    if not image_path and ctx.image_path and ctx.image_path.exists():
        image_path = str(ctx.image_path)

    if not image_path:
        logger.warning("No image found for %s, skipping TG publish", ctx.slug)
        return

    # Send photo + caption
    msg_id = send_photo(
        chat_id=TG_CHANNEL_ID,
        image_path=image_path,
        caption=ctx.tg_post,
        bot_token=TG_BOT_TOKEN,
        silent=silent,
    )

    if msg_id:
        add_reaction(TG_CHANNEL_ID, msg_id, "🔥", TG_BOT_TOKEN)
        ctx.msg_id = msg_id
        logger.info("Published photo to @pashtelka_news: msg_id=%d", msg_id)
        _mark_posted(ctx, msg_id)
    else:
        logger.error("Failed to publish to Telegram")


def _mark_posted(ctx: PipelineContext, msg_id: int) -> None:
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
