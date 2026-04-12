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
    pt_paragraph = result.get("pt_paragraph", "")
    vocab = result.get("vocab", [])

    # Bold vocab words in pt_paragraph
    pt_bold = pt_paragraph
    for v in vocab:
        import re
        word = v["pt"]
        pt_bold = re.sub(
            rf'\b({re.escape(word)})\b',
            r'<b>\1</b>',
            pt_bold,
            flags=re.IGNORECASE,
        )

    # Build vocab with bold PT + spoiler UA
    vocab_lines = []
    for v in vocab[:5]:
        vocab_lines.append(f"<b>{v['pt']}</b> — <tg-spoiler>{v['uk']}</tg-spoiler>")
    vocab_block = "\n".join(vocab_lines)

    # Assemble caption
    parts = [
        f"<b>{hook}</b>",
        "",
        body,
        "",
        f'<a href="{article_url}">Дізнатись більше →</a>',
        "",
        "🇵🇹 Português fácil:",
        f"<i>{pt_bold}</i>",
        "",
        "📖 Словничок:",
        vocab_block,
        "",
        '<a href="https://t.me/pashtelka_news">🇵🇹 Паштелька News</a>',
    ]

    ctx.tg_post = "\n".join(parts)
    ctx.article_url = article_url
    logger.info("TG caption: %d chars, vocab: %d words, pt: %d chars",
                len(ctx.tg_post), len(vocab), len(pt_paragraph))
