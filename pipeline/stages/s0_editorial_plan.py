"""Stage 0: Editorial planning — create daily article plan.

Runs once per day (first generate run or explicit 'plan' mode).
Analyzes past articles to avoid repetition, considers RSS headlines,
and creates a diverse editorial plan for the day.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pipeline.config import (
    CONTENT_DIR, MODEL_GENERATE, STATE_DIR,
)
from pipeline.feeds import fetch_rss_headlines
from pipeline.sdk import structured_query

logger = logging.getLogger(__name__)

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "articles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Article topic/headline idea (Ukrainian)"},
                    "type": {"type": "string", "enum": ["news", "material", "utility", "immigration", "guide"],
                             "description": "Content type"},
                    "angle": {"type": "string", "description": "Specific angle/focus for this article (Ukrainian)"},
                    "sources_hint": {"type": "string", "description": "Where to research: specific portals, RSS, search queries (English)"},
                    "priority": {"type": "integer", "description": "1=must publish, 2=important, 3=nice to have"},
                },
                "required": ["topic", "type", "angle", "sources_hint", "priority"],
            },
            "description": "10-12 article ideas for today, ordered by priority",
        },
    },
    "required": ["articles"],
}


def run() -> dict:
    """Create editorial plan for today. Returns the plan dict."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")

    # Check if plan already exists for today
    plan_file = STATE_DIR / "plans" / f"{today_str}.json"
    if plan_file.exists():
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
        logger.info("Editorial plan already exists for %s (%d articles)", today_str, len(plan.get("articles", [])))
        return plan

    # Gather context
    recent_summaries = _load_recent_articles(days=30)
    rss_headlines = _format_rss()
    today_articles = _load_today_articles(today_str)

    prompt = f"""\
<task>
Create an editorial plan for today ({today_str}, {now.strftime('%A')}) for Паштелька News — a Ukrainian news outlet about Portugal.
Target audience: Ukrainian diaspora in Portugal (Lisbon, Porto, Faro, Algarve).
</task>

<recent_articles_last_30_days>
{recent_summaries}
</recent_articles_last_30_days>

<already_written_today>
{today_articles if today_articles else "(none yet)"}
</already_written_today>

<current_rss_headlines>
{rss_headlines}
</current_rss_headlines>

<editorial_guidelines>
PLAN 10-12 articles for today. Mix of types:
- 6-8 news: breaking/current Portuguese news relevant to Ukrainians
- 1-2 material: in-depth compiled articles from multiple sources (immigration, housing, healthcare, taxes, etc.)
- 1-2 utility/guide: practical info (transport disruptions, weather warnings, document deadlines, etc.)

RULES:
1. DO NOT repeat topics from the last 30 days (see recent articles above)
2. DO NOT repeat topics already written today
3. Prioritize: breaking news > utility alerts > immigration updates > economy > society > culture
4. Each article must have a SPECIFIC angle, not just a general topic
5. Material articles need compilation from 3+ sources — specify what to search for
6. Cover geographic diversity: not just Lisbon, also Porto, Faro, Algarve when relevant
7. Include at least 1 article directly useful for daily life (transport, weather, prices, deadlines)
8. Include at least 1 immigration/AIMA/SEF topic if there's news
9. Day of week matters: Monday = week outlook, Friday = weekend plans, etc.
10. FOLLOW-UPS: If a story from the past 30 days has NEW DEVELOPMENTS, include it as a follow-up. Mark these with "(продовження)" in the topic. The article will reference our previous coverage.
</editorial_guidelines>
"""

    system = """\
You are the editor-in-chief of Паштелька News. You plan diverse, relevant content for Ukrainian readers in Portugal.
Think like a local Ukrainian who needs practical info about life in Portugal.
Never repeat topics. Always bring fresh angles even on recurring themes (housing, immigration, weather).
"""

    plan = structured_query(
        prompt=prompt,
        system_prompt=system,
        schema=PLAN_SCHEMA,
        model=MODEL_GENERATE,
    )

    # Save plan
    plan_dir = STATE_DIR / "plans"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan["date"] = today_str
    plan["created_at"] = now.isoformat()
    plan_file.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("Editorial plan created: %d articles for %s", len(plan.get("articles", [])), today_str)
    return plan


def get_next_topic(plan: dict, written_slugs: set[str]) -> dict | None:
    """Get the next unwritten topic from the plan."""
    written_file = STATE_DIR / "plans" / f"{plan.get('date', 'unknown')}_written.json"
    written_topics: list[str] = []
    if written_file.exists():
        written_topics = json.loads(written_file.read_text(encoding="utf-8"))

    for article in plan.get("articles", []):
        topic = article["topic"]
        if topic not in written_topics:
            # Mark as taken
            written_topics.append(topic)
            written_file.parent.mkdir(parents=True, exist_ok=True)
            written_file.write_text(json.dumps(written_topics, ensure_ascii=False), encoding="utf-8")
            return article

    return None


def _load_recent_articles(days: int = 30) -> str:
    """Load summaries of articles from the last N days, using stored summaries."""
    if not CONTENT_DIR.exists():
        return "(no articles yet)"

    # Load stored summaries
    summaries_file = STATE_DIR / "summaries.json"
    stored: dict = {}
    if summaries_file.exists():
        try:
            stored = json.loads(summaries_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            stored = {}

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    lines = []

    for md in sorted(CONTENT_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        text = md.read_text(encoding="utf-8")
        title = ""
        date = ""
        article_type = ""

        for line in text.split("\n"):
            if line.startswith("title:"):
                title = line.split('"')[1] if '"' in line else line.split(": ", 1)[1]
            elif line.startswith("date:"):
                date = line.split('"')[1] if '"' in line else line.split(": ", 1)[1]
            elif line.startswith("type:"):
                article_type = line.split('"')[1] if '"' in line else line.split(": ", 1)[1]

        if date and date < cutoff:
            continue

        slug = md.stem
        summary = stored.get(slug, {}).get("summary", "")
        if not summary:
            # Fallback: extract first 200 chars of body
            body_lines = text.split("---", 2)
            if len(body_lines) > 2:
                body = body_lines[2].strip().replace("\n", " ")[:200]
                summary = body + "..."

        lines.append(f"[{date}] ({article_type}) {title}\n  Summary: {summary}\n  Slug: {slug}")

        if len(lines) >= 80:
            break

    return "\n".join(lines) if lines else "(no recent articles)"


def _load_today_articles(today_str: str) -> str:
    """Load titles of articles already written today."""
    if not CONTENT_DIR.exists():
        return ""

    today_articles = []
    for md in CONTENT_DIR.glob("*.md"):
        text = md.read_text(encoding="utf-8")
        if f'date: "{today_str}"' in text:
            for line in text.split("\n"):
                if line.startswith("title:"):
                    title = line.split('"')[1] if '"' in line else line.split(": ", 1)[1]
                    today_articles.append(f"- {title}")
                    break

    return "\n".join(today_articles)


def _format_rss() -> str:
    """Fetch and format current RSS headlines."""
    items = fetch_rss_headlines()
    lines = []
    for item in items[:30]:
        lines.append(f"- [{item['source']}] {item['title']}")
    return "\n".join(lines) if lines else "(no RSS available)"
