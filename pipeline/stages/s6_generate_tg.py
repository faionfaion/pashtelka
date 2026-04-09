"""Stage 6: Generate TG — write Telegram photo caption."""

from __future__ import annotations

import logging

from pipeline.config import MAX_TG_CAPTION, MODEL_TG, SITE_BASE_URL
from pipeline.context import PipelineContext
from pipeline.prompts.builder import build_tg_post_prompt
from pipeline.schemas import load_schema
from pipeline.sdk import structured_query

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> None:
    article_url = f"{SITE_BASE_URL}/{ctx.slug}/"

    system, prompt = build_tg_post_prompt(ctx)

    result = structured_query(
        prompt=prompt,
        system_prompt=system,
        schema=load_schema("tg_post"),
        model=MODEL_TG,
    )

    hook = result["hook"]
    body = result["body"]
    vocab = result.get("vocab", [])

    # Build vocab with spoilers
    vocab_lines = []
    for v in vocab[:5]:
        vocab_lines.append(f"{v['pt']} — <tg-spoiler>{v['uk']}</tg-spoiler>")
    vocab_block = "\n".join(vocab_lines)

    # Assemble caption
    parts = [
        f"<b>{hook}</b>",
        "",
        body,
        "",
        f'<a href="{article_url}">Дізнатись більше →</a>',
        "",
        f"📖 Словничок:",
        vocab_block,
        "",
        '<a href="https://t.me/pashtelka_news">🇵🇹 Паштелька News</a>',
    ]

    ctx.tg_post = "\n".join(parts)
    ctx.article_url = article_url
    logger.info("TG caption: %d chars, vocab: %d words", len(ctx.tg_post), len(vocab))
