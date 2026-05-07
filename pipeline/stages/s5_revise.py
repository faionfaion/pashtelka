"""Stage 5: Revise — apply editorial feedback to the article."""

from __future__ import annotations

import logging

from pipeline.config import AUTHOR_NAME
from pipeline.context import PipelineContext
from pipeline.llm import dispatch_structured
from pipeline.prompts.builder import build_revise_prompt
from pipeline.schemas import load_schema

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> None:
    system, prompt = build_revise_prompt(ctx, AUTHOR_NAME)

    result = dispatch_structured(
        prompt=prompt,
        system=system,
        schema=load_schema("revision"),
        stage="revise",
    )

    ctx.article_text = result["article"]
    if result.get("title"):
        ctx.title = result["title"]
    if result.get("description"):
        ctx.description = result["description"]

    logger.info("Revised article: %d words", len(ctx.article_text.split()))
