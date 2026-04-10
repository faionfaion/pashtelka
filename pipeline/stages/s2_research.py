"""Stage 2: Research — search for Portuguese news on the assigned topic."""

from __future__ import annotations

import logging

from pipeline.config import MODEL_RESEARCH
from pipeline.context import PipelineContext
from pipeline.prompts.builder import build_research_prompt
from pipeline.sdk import agent_query

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> None:
    headlines_text = _format_headlines(ctx.news_items[:20])
    focus_text = _focus_for_type(ctx.slot_type)

    system, prompt = build_research_prompt(ctx, headlines_text, focus_text)

    ctx.research_text = agent_query(
        prompt=prompt,
        system_prompt=system,
        model=MODEL_RESEARCH,
        allowed_tools=["WebSearch", "WebFetch", "Read", "Glob"],
        timeout=300,
    )

    logger.info("Research complete: %d chars", len(ctx.research_text))


def _format_headlines(items: list[dict]) -> str:
    lines = []
    for item in items:
        lines.append(f"- [{item['source']}] {item['title']}")
        if item.get("description"):
            lines.append(f"  {item['description'][:200]}")
        if item.get("link"):
            lines.append(f"  URL: {item['link']}")
    return "\n".join(lines) if lines else "(no RSS headlines available)"


def _focus_for_type(slot_type: str) -> str:
    focuses = {
        "news": "general Portuguese news most relevant to Ukrainian community",
        "material": "in-depth topic requiring compilation from multiple sources (3+ sources minimum)",
        "digest": "summary of all major news of the day",
        "weather": "weather forecast and any IPMA warnings for key cities",
        "utility": "service disruptions, outages, transport issues",
        "immigration": "AIMA updates, visa/permit changes, legal deadlines",
        "guide": "step-by-step practical information, official requirements, costs, deadlines",
    }
    return focuses.get(slot_type, focuses["news"])
