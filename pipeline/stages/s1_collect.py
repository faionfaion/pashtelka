"""Stage 1: Collect context — determine slot, check posted articles, gather RSS."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from pipeline.config import (
    CONTENT_DIR, RSS_FEEDS, SLOTS, SLOT_TYPES, STATE_DIR,
)
from pipeline.context import PipelineContext
from pipeline.feeds import fetch_rss_headlines

logger = logging.getLogger(__name__)


class AllPostedError(Exception):
    """All slots for today are already posted."""


def run(ctx: PipelineContext) -> None:
    now = datetime.now(timezone.utc)
    current_hour = now.hour

    # Load posted state for today
    today_str = now.strftime("%Y-%m-%d")
    state_file = STATE_DIR / "posted" / f"{today_str}.json"
    posted: dict = {}
    if state_file.exists():
        posted = json.loads(state_file.read_text(encoding="utf-8"))

    # Find next unposted slot
    available = [h for h in SLOTS if str(h) not in posted and h <= current_hour + 1]
    if not available:
        # Check if any future slots exist
        future = [h for h in SLOTS if str(h) not in posted]
        if not future:
            raise AllPostedError("All slots posted for today")
        # Pick first available future slot
        ctx.slot_hour = future[0]
    else:
        ctx.slot_hour = available[0]

    ctx.slot_type = SLOT_TYPES.get(ctx.slot_hour, "news")

    # Load existing slugs to prevent duplicates
    if CONTENT_DIR.exists():
        ctx.posted_slugs = [
            p.stem for p in CONTENT_DIR.glob("*.md")
        ]

    # Fetch RSS headlines for research stage
    ctx.news_items = fetch_rss_headlines()

    logger.info(
        "Slot: %02d:00 (%s) | RSS items: %d | Existing articles: %d",
        ctx.slot_hour, ctx.slot_type, len(ctx.news_items), len(ctx.posted_slugs),
    )
