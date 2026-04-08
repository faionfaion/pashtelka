"""Stage 5: Revise — apply editorial feedback to the article."""

from __future__ import annotations

import logging

from pipeline.config import AUTHOR_NAME, MODEL_GENERATE
from pipeline.context import PipelineContext
from pipeline.sdk import structured_query

logger = logging.getLogger(__name__)

REVISION_SCHEMA = {
    "type": "object",
    "properties": {
        "article": {"type": "string", "description": "Revised article text in Ukrainian"},
        "title": {"type": "string", "description": "Revised title (if needed)"},
        "description": {"type": "string", "description": "Revised meta description"},
    },
    "required": ["article"],
}


def run(ctx: PipelineContext) -> None:
    prompt = f"""\
<task>
Revise this article based on editorial feedback.
</task>

<current_article>
Title: {ctx.title}
Type: {ctx.slot_type}

{ctx.article_text}
</current_article>

<feedback>
{ctx.review_feedback}
</feedback>

<instructions>
- Apply ALL feedback points
- Maintain Oksana Lytvyn's voice (warm, friendly, light humor)
- Keep all source citations
- Do NOT add new information not in the original research
- Return the complete revised article
</instructions>
"""

    result = structured_query(
        prompt=prompt,
        system_prompt=f"You are {AUTHOR_NAME}, revising your article based on editor feedback.",
        schema=REVISION_SCHEMA,
        model=MODEL_GENERATE,
    )

    ctx.article_text = result["article"]
    if result.get("title"):
        ctx.title = result["title"]
    if result.get("description"):
        ctx.description = result["description"]

    logger.info("Revised article: %d words", len(ctx.article_text.split()))
