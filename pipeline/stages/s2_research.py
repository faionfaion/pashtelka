"""Stage 2: Research — search for Portuguese news on the selected topic."""

from __future__ import annotations

import json
import logging

from pipeline.config import MODEL_RESEARCH
from pipeline.context import PipelineContext
from pipeline.sdk import agent_query

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a research assistant for Pashtelka, a Ukrainian news outlet covering Portugal.
Your task is to find current Portuguese news relevant to Ukrainians living in Portugal.

Focus areas:
- Breaking Portuguese news (politics, economy, society)
- Immigration/AIMA updates
- Utility alerts (water, electricity, transport disruptions)
- Municipal announcements (Lisbon, Porto, Faro)
- Weather warnings
- Tax/legal deadlines
- Employment and housing market
- Community events

Search in Portuguese. Return detailed findings with source URLs.
Always include the original Portuguese source URL for every fact.
"""


def run(ctx: PipelineContext) -> None:
    # Build research prompt from RSS headlines and slot type
    headlines_text = _format_headlines(ctx.news_items[:20])

    prompt = f"""\
<task>
Research Portuguese news for a {ctx.slot_type} article.
Current slot: {ctx.slot_hour}:00 Lisbon time.
</task>

<rss_headlines>
{headlines_text}
</rss_headlines>

<instructions>
1. Review the RSS headlines above
2. Search the web for the most newsworthy topics for Ukrainians in Portugal TODAY
3. For {ctx.slot_type} type, focus on: {_focus_for_type(ctx.slot_type)}
4. Find 3-5 relevant stories with full details
5. For each story provide: title, summary (3-5 sentences), source URL, relevance to Ukrainian community
6. If there are utility alerts (water/electricity outages, transport disruptions), prioritize those

Return your findings as a structured research brief.
</instructions>

<existing_articles>
Do NOT cover topics already published today: {', '.join(ctx.posted_slugs[-10:])}
</existing_articles>
"""

    ctx.research_text = agent_query(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        model=MODEL_RESEARCH,
        allowed_tools=["WebSearch", "WebFetch"],
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
        "material": "in-depth topic requiring compilation from multiple sources",
        "digest": "summary of all major news of the day",
        "weather": "weather forecast and any IPMA warnings for key cities",
        "utility": "service disruptions, outages, transport issues",
        "immigration": "AIMA updates, visa/permit changes, legal deadlines",
    }
    return focuses.get(slot_type, focuses["news"])
