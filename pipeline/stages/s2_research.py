"""Stage 2: Research — search for Portuguese news on the assigned topic."""

from __future__ import annotations

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
Find at least 3 different sources for material/guide articles.
"""


def run(ctx: PipelineContext) -> None:
    headlines_text = _format_headlines(ctx.news_items[:20])

    # Use editorial plan topic if available
    topic_section = ""
    if ctx.editorial_plan:
        topic = ctx.editorial_plan
        topic_section = f"""
<assigned_topic>
Topic: {topic.get('topic', '')}
Type: {topic.get('type', 'news')}
Angle: {topic.get('angle', '')}
Research hints: {topic.get('sources_hint', '')}
</assigned_topic>
"""

    prompt = f"""\
<task>
Research Portuguese news for a {ctx.slot_type} article.
</task>

{topic_section}

<rss_headlines>
{headlines_text}
</rss_headlines>

<instructions>
1. {"Focus on the assigned topic above." if topic_section else "Review the RSS headlines and find the most newsworthy topic for Ukrainians in Portugal TODAY."}
2. Search the web for detailed information. Use Portuguese search queries.
3. For {ctx.slot_type} type, focus on: {_focus_for_type(ctx.slot_type)}
4. Find 3-5 relevant sources with full details
5. For each source: title, key facts (3-5 sentences), source URL
6. If there are utility alerts (water/electricity outages, transport disruptions), note them
7. For material/guide articles: find at least 3 different sources to compile from

Return your findings as a structured research brief.
</instructions>

<existing_articles>
Do NOT cover topics already published: {', '.join(ctx.posted_slugs[-20:])}
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
        "material": "in-depth topic requiring compilation from multiple sources (3+ sources minimum)",
        "digest": "summary of all major news of the day",
        "weather": "weather forecast and any IPMA warnings for key cities",
        "utility": "service disruptions, outages, transport issues",
        "immigration": "AIMA updates, visa/permit changes, legal deadlines",
        "guide": "step-by-step practical information, official requirements, costs, deadlines",
    }
    return focuses.get(slot_type, focuses["news"])
