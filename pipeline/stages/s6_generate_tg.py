"""Stage 6: Generate TG — write Telegram photo caption."""

from __future__ import annotations

import logging

from pipeline.config import MAX_TG_CAPTION, MODEL_TG, SITE_BASE_URL
from pipeline.context import PipelineContext
from pipeline.sdk import structured_query

logger = logging.getLogger(__name__)

TG_POST_SCHEMA = {
    "type": "object",
    "properties": {
        "hook": {
            "type": "string",
            "description": "Bold hook/headline — 1 sentence, grab attention (Ukrainian)",
        },
        "body": {
            "type": "string",
            "description": "2-3 sentences: key facts, practical info. Accent words in <b>bold</b>. Ukrainian, HTML only.",
        },
        "vocab": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pt": {"type": "string", "description": "Portuguese term"},
                    "uk": {"type": "string", "description": "Ukrainian translation"},
                },
                "required": ["pt", "uk"],
            },
            "description": "3-5 Portuguese vocabulary words from the article with Ukrainian translation",
        },
    },
    "required": ["hook", "body", "vocab"],
}


def run(ctx: PipelineContext) -> None:
    article_url = f"{SITE_BASE_URL}/{ctx.slug}/"

    prompt = f"""\
<task>
Write a Telegram photo caption for this article. Also extract Portuguese vocabulary.
</task>

<article>
Title: {ctx.title}
Type: {ctx.slot_type}

{ctx.article_text[:2000]}
</article>

<rules>
HOOK: one punchy sentence, Ukrainian. Will be displayed in bold.
BODY: 2-3 sentences with key facts. Use <b>bold</b> for accent words (numbers, names, dates, important terms). Keep it useful and practical. No hashtags. No sign-offs.
VOCAB: 3-5 Portuguese terms from the article topic. Pick words people encounter in daily life in Portugal. Portuguese word first, Ukrainian translation second.
</rules>
"""

    result = structured_query(
        prompt=prompt,
        system_prompt="You write Telegram captions for a Ukrainian news channel about Portugal. Concise, useful, bold accents on key words.",
        schema=TG_POST_SCHEMA,
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
