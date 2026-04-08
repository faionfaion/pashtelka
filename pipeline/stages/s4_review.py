"""Stage 4: Review — editorial review of the generated article."""

from __future__ import annotations

import logging

from pipeline.config import AUTHOR_NAME, MODEL_REVIEW
from pipeline.context import PipelineContext
from pipeline.sdk import structured_query

logger = logging.getLogger(__name__)

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "approved": {"type": "boolean"},
        "feedback": {"type": "string", "description": "Specific feedback for revision"},
        "score": {"type": "integer", "description": "Quality score 1-10"},
    },
    "required": ["approved", "feedback", "score"],
}


def run(ctx: PipelineContext) -> None:
    prompt = f"""\
<task>
Review this article for Pashtelka (Ukrainian news about Portugal).
</task>

<article>
Title: {ctx.title}
Type: {ctx.slot_type}
Author: {AUTHOR_NAME}

{ctx.article_text}
</article>

<sources>
{chr(10).join(f'- {name}: {url}' for name, url in zip(ctx.source_names, ctx.source_urls))}
</sources>

<checklist>
1. SOURCES: Every factual claim has a cited source? Source URLs are real?
2. ACCURACY: No fabricated facts or misleading claims?
3. VOICE: Matches Oksana's warm, friendly tone? No banned phrases?
4. LANGUAGE: Clean Ukrainian, no Russian words, no Surzhyk?
5. STRUCTURE: Short paragraphs? Inverted pyramid for news?
6. RELEVANCE: Relevant to Ukrainians in Portugal? Practical takeaway?
7. LENGTH: Within word count limits for {ctx.slot_type}?
8. TAGS/HASHTAGS: Appropriate city and topic tags?
9. LEGAL: No defamation, no unverified claims about specific people?
10. PORTUGUESE TERMS: Explained in Ukrainian on first use?
</checklist>

<scoring>
- 8-10: Approved (minor issues only)
- 5-7: Needs revision (specific improvements needed)
- 1-4: Major rewrite needed
</scoring>

If score >= 8, set approved=true. Otherwise, provide specific actionable feedback.
"""

    result = structured_query(
        prompt=prompt,
        system_prompt="You are a senior editor reviewing articles for a Ukrainian news outlet in Portugal. Be strict but fair.",
        schema=REVIEW_SCHEMA,
        model=MODEL_REVIEW,
    )

    ctx.review_approved = result.get("approved", False)
    ctx.review_feedback = result.get("feedback", "")
    score = result.get("score", 0)

    logger.info("Review: score=%d, approved=%s", score, ctx.review_approved)
    if ctx.review_feedback:
        logger.info("Feedback: %s", ctx.review_feedback[:200])
