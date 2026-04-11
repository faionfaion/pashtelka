"""Stage 4: Review — editorial review of the generated article."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from pipeline.config import AUTHOR_NAME, CONTENT_DIR, MODEL_REVIEW
from pipeline.context import PipelineContext
from pipeline.prompts.builder import build_review_prompt
from pipeline.schemas import load_schema
from pipeline.sdk import structured_query

logger = logging.getLogger(__name__)


def _load_recent_titles(days: int = 3) -> str:
    """Load titles+types of articles from the last N days for dedup check."""
    if not CONTENT_DIR.exists():
        return ""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    lines = []
    for md in sorted(CONTENT_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        text = md.read_text(encoding="utf-8")
        title, date, article_type = "", "", ""
        for line in text.split("\n"):
            if line.startswith("title:"):
                title = line.split('"')[1] if '"' in line else line.split(": ", 1)[1]
            elif line.startswith("date:"):
                date = line.split('"')[1] if '"' in line else line.split(": ", 1)[1]
            elif line.startswith("type:"):
                article_type = line.split('"')[1] if '"' in line else line.split(": ", 1)[1]
        if date and date >= cutoff:
            lines.append(f"[{date}] ({article_type}) {title}")
        if len(lines) >= 40:
            break
    return "\n".join(lines)


def run(ctx: PipelineContext) -> None:
    recent_titles = _load_recent_titles(days=3)
    system, prompt = build_review_prompt(ctx, AUTHOR_NAME, recent_titles=recent_titles)

    result = structured_query(
        prompt=prompt,
        system_prompt=system,
        schema=load_schema("review"),
        model=MODEL_REVIEW,
    )

    ctx.review_approved = result.get("approved", False)
    ctx.review_feedback = result.get("feedback", "")
    score = result.get("score", 0)

    logger.info("Review: score=%d, approved=%s", score, ctx.review_approved)
    if ctx.review_feedback:
        logger.info("Feedback: %s", ctx.review_feedback[:200])
