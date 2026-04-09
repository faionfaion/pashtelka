"""Stage 6: Generate TG — write the Telegram post teaser."""

from __future__ import annotations

import logging

from pipeline.config import MAX_TG_CAPTION, MODEL_TG, SITE_BASE_URL
from pipeline.context import PipelineContext
from pipeline.sdk import structured_query

logger = logging.getLogger(__name__)

TG_POST_SCHEMA = {
    "type": "object",
    "properties": {
        "tg_post": {
            "type": "string",
            "description": "Telegram post body in Ukrainian with HTML formatting (NO hashtags, NO sign-off)",
        },
        "vocab": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "uk": {"type": "string", "description": "Ukrainian word/phrase"},
                    "pt": {"type": "string", "description": "Portuguese word/phrase"},
                },
                "required": ["uk", "pt"],
            },
            "description": "3-5 key vocabulary pairs from the article (Ukrainian - Portuguese)",
        },
    },
    "required": ["tg_post", "vocab"],
}


def run(ctx: PipelineContext) -> None:
    article_url = f"{SITE_BASE_URL}/{ctx.slug}/"

    prompt = f"""\
<task>
Write a Telegram post teaser for this article. Also extract key vocabulary.
</task>

<article>
Title: {ctx.title}
Type: {ctx.slot_type}
URL: {article_url}

{ctx.article_text[:2000]}
</article>

<rules>
1. Length: 300-600 characters for tg_post (strict!)
2. Language: Ukrainian
3. Format: HTML (use <b>bold</b>, <i>italic</i> only)
4. Structure:
   - Hook line (grab attention)
   - 2-3 key facts from the article
   - Optional: thought-provoking question or practical takeaway
5. NO hashtags — do not include any hashtags
6. NO sign-off — no "Ваша Оксана" or similar
7. Do NOT include the URL (it's added automatically)
8. Do NOT use markdown — only HTML tags
9. Tone: informative, warm, light — like a friend sharing news
10. For utility alerts: lead with the actionable info (what, where, when)
</rules>

<vocab_rules>
Extract 3-5 Portuguese terms that appear in the article or are relevant to the topic.
Format: Ukrainian word/phrase paired with Portuguese equivalent.
Pick practical words that readers might encounter in daily life in Portugal.
Examples:
  - Громадянство - cidadania
  - Податок - imposto
  - Дозвіл на проживання - autorização de residência
</vocab_rules>
"""

    result = structured_query(
        prompt=prompt,
        system_prompt="You write Telegram teasers for a Ukrainian news channel about Portugal. Concise, engaging, no hashtags, no sign-offs.",
        schema=TG_POST_SCHEMA,
        model=MODEL_TG,
    )

    # Build final TG post: teaser + footer + vocab
    teaser = result["tg_post"]
    vocab = result.get("vocab", [])

    # Build vocab block
    vocab_lines = []
    for v in vocab[:5]:
        vocab_lines.append(f"🇺🇦 {v['uk']} — 🇵🇹 {v['pt']}")
    vocab_block = "\n".join(vocab_lines)

    # Assemble final post
    parts = [teaser]
    if vocab_block:
        parts.append(f"\n📖 <b>Словничок:</b>\n{vocab_block}")
    parts.append("\n🇵🇹 Паштелька News")

    ctx.tg_post = "\n".join(parts)

    # Trim if over limit
    if len(ctx.tg_post) > MAX_TG_CAPTION:
        logger.warning("TG post too long (%d chars), will be trimmed", len(ctx.tg_post))

    ctx.article_url = article_url
    logger.info("TG post: %d chars, vocab: %d words", len(ctx.tg_post), len(vocab))
