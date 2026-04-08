"""Stage 6: Generate TG — write the Telegram post teaser."""

from __future__ import annotations

import logging

from pipeline.config import AUTHOR_NAME, MAX_TG_CAPTION, MODEL_TG, SITE_BASE_URL
from pipeline.context import PipelineContext
from pipeline.sdk import structured_query

logger = logging.getLogger(__name__)

TG_POST_SCHEMA = {
    "type": "object",
    "properties": {
        "tg_post": {
            "type": "string",
            "description": "Telegram post text in Ukrainian with HTML formatting",
        },
    },
    "required": ["tg_post"],
}


def run(ctx: PipelineContext) -> None:
    article_url = f"{SITE_BASE_URL}/{ctx.slug}/"

    prompt = f"""\
<task>
Write a Telegram post teaser for this article.
</task>

<article>
Title: {ctx.title}
Type: {ctx.slot_type}
URL: {article_url}

{ctx.article_text[:2000]}
</article>

<rules>
1. Length: 400-{MAX_TG_CAPTION} characters (strict limit!)
2. Language: Ukrainian
3. Format: HTML (use <b>bold</b>, <i>italic</i> only)
4. Structure:
   - Hook line (grab attention)
   - 2-3 key facts from the article
   - Call to action or thought-provoking question
5. Include hashtags at the end: {ctx.hashtags}
6. Voice: Oksana's style — warm, friendly, light humor
7. Do NOT include the URL (it's added automatically as invisible link)
8. Do NOT use markdown — only HTML tags
9. Source attribution: mention the source name briefly
10. For utility alerts: lead with the actionable info (what, where, when)
</rules>

<sign_off>
End with: "Ваша Оксана з Лісабона 🇵🇹" (only for digest/material types)
For news: no sign-off needed, just hashtags
</sign_off>
"""

    result = structured_query(
        prompt=prompt,
        system_prompt=f"You are {AUTHOR_NAME}, writing a Telegram teaser post. Be concise and engaging.",
        schema=TG_POST_SCHEMA,
        model=MODEL_TG,
    )

    ctx.tg_post = result["tg_post"]

    # Trim if over limit
    if len(ctx.tg_post) > MAX_TG_CAPTION:
        logger.warning("TG post too long (%d chars), will be trimmed", len(ctx.tg_post))

    ctx.article_url = article_url
    logger.info("TG post: %d chars", len(ctx.tg_post))
