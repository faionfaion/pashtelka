"""Stage 3: Generate — write the article in Ukrainian from research."""

from __future__ import annotations

import logging

from pipeline.config import (
    CONTENT_DIR, CONTENT_TYPES, MODEL_GENERATE, SITE_BASE_URL,
)
from pipeline.context import PipelineContext
from pipeline.sdk import structured_query

logger = logging.getLogger(__name__)

GENERATION_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Article title in Ukrainian"},
        "slug": {"type": "string", "description": "URL slug (latin, lowercase, hyphens)"},
        "article": {"type": "string", "description": "Article BODY in Ukrainian markdown. NO title, NO metadata, NO 'Title:' prefix — just paragraphs starting with the hook sentence."},
        "description": {"type": "string", "description": "Meta description in Ukrainian (150-160 chars)"},
        "tags": {"type": "array", "items": {"type": "string"}, "description": "Topic tags in Ukrainian"},
        "hashtags": {"type": "string", "description": "Hashtags for TG post (city + topic)"},
        "source_urls": {"type": "array", "items": {"type": "string"}, "description": "Source URLs"},
        "source_names": {"type": "array", "items": {"type": "string"}, "description": "Source names"},
        "city_tags": {"type": "array", "items": {"type": "string"}, "description": "Relevant city names"},
        "image_prompt": {"type": "string", "description": "Comic-style illustration prompt in English"},
    },
    "required": ["title", "slug", "article", "description", "tags", "hashtags",
                  "source_urls", "source_names", "image_prompt"],
}

VOICE_GUIDE = """\
You write for Паштелька News — a Ukrainian news outlet about Portugal.

Voice characteristics:
- Warm, friendly, approachable — like a knowledgeable friend
- Light humor where appropriate (never forced)
- Mix Portuguese terms with Ukrainian explanation: "Junta de Freguesia (місцева рада)"
- Short paragraphs (2-3 sentences max)
- Active voice, present tense for news
- Inverted pyramid for news (most important first)
- Never alarmist, never condescending
- Use casual but grammatically correct Ukrainian
- NO Russian words, NO Surzhyk
- Occasional warmth: reference to Portuguese culture, pastel de nata, local quirks

BANNED phrases:
- "Як повідомляють джерела" (which sources?)
- "Експерти стверджують" (which experts?)
- "Як відомо", "Не секрет, що", "Варто зазначити", "Цікаво, що"
- "Залишається тільки чекати"

Every article MUST cite sources with URLs. Never fabricate facts.
No author name or sign-off — articles are by the editorial team.
"""


def run(ctx: PipelineContext) -> None:
    type_cfg = CONTENT_TYPES.get(ctx.slot_type, CONTENT_TYPES["news"])

    # Editorial plan context
    editorial_section = ""
    if ctx.editorial_plan:
        ep = ctx.editorial_plan
        editorial_section = f"""
<editorial_assignment>
Topic: {ep.get('topic', '')}
Angle: {ep.get('angle', '')}
Type: {ep.get('type', ctx.slot_type)}
</editorial_assignment>
"""

    prompt = f"""\
<task>
Write a {ctx.slot_type} article in Ukrainian based on the research below.
{f"Follow the editorial assignment closely." if editorial_section else ""}
</task>

{editorial_section}

<research>
{ctx.research_text}
</research>

<requirements>
- Content type: {ctx.slot_type}
- Word count: {type_cfg['min_words']}-{type_cfg['max_words']} words
- Language: Ukrainian
- MUST include source URLs for every factual claim
- Slug: latin lowercase with hyphens, descriptive, SEO-friendly
- Tags: Ukrainian topic tags relevant to the article
- Hashtags: combine city hashtags (#Лісабон, #Порту, etc.) with topic hashtags (#Новини, #Імміграція, etc.)
- Image prompt: describe a comic-style illustration for this article (in English, for DALL-E)
  - Style: colorful comic book illustration, clean lines, warm palette
  - Include relevant Portuguese visual elements (tiles, sardines, tram, etc.)
  - NO text in the image
  - NO real people or politicians
- If this topic CONTINUES or UPDATES a story we already covered, reference the previous article:
  - Mention it in the text: "Як ми писали раніше (посилання)" or "Нагадаємо, що..."
  - Use the URL format: {SITE_BASE_URL}/{{previous-slug}}/
  - This builds narrative continuity for readers
</requirements>

<existing_articles>
Our published articles (use for cross-references if topic overlaps):
{_format_existing_articles(ctx.posted_slugs[-30:])}
</existing_articles>

<existing_slugs>
Avoid these slugs (already used): {', '.join(ctx.posted_slugs[-20:])}
</existing_slugs>
"""

    system = f"""\
{VOICE_GUIDE}

You are writing for pashtelka.faion.net — a news outlet for Ukrainians in Portugal.
Target audience: Ukrainian residents in Portugal (Lisbon, Porto, Faro, Algarve).

CRITICAL: The "article" field must contain ONLY the markdown body text.
Do NOT include "Title:", "Type:", "Tags:" or any metadata — those go in separate JSON fields.
Start the article directly with the first paragraph (the hook).
"""

    result = structured_query(
        prompt=prompt,
        system_prompt=system,
        schema=GENERATION_SCHEMA,
        model=MODEL_GENERATE,
    )

    ctx.title = result["title"]
    ctx.slug = result["slug"]
    ctx.article_text = result["article"]
    ctx.description = result.get("description", "")
    ctx.tags = result.get("tags", [])
    ctx.hashtags = result.get("hashtags", "")
    ctx.source_urls = result.get("source_urls", [])
    ctx.source_names = result.get("source_names", [])
    ctx.city_tags = result.get("city_tags", [])
    ctx.image_prompt = result.get("image_prompt", "")

    logger.info(
        "Generated: '%s' (slug=%s, %d words, %d sources)",
        ctx.title, ctx.slug,
        len(ctx.article_text.split()),
        len(ctx.source_urls),
    )


def _format_existing_articles(slugs: list[str]) -> str:
    """Format existing articles with titles for cross-reference context."""
    lines = []
    for slug in slugs:
        md = CONTENT_DIR / f"{slug}.md"
        if not md.exists():
            continue
        text = md.read_text(encoding="utf-8")
        title = ""
        for line in text.split("\n"):
            if line.startswith("title:"):
                title = line.split('"')[1] if '"' in line else line.split(": ", 1)[1]
                break
        if title:
            lines.append(f"- {slug}: {title} ({SITE_BASE_URL}/{slug}/)")
    return "\n".join(lines) if lines else "(no existing articles)"
