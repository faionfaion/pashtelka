# Pashtelka Constitution

## Product Identity

**Pashtelka** (Пастелка) — Ukrainian-language news media for Ukrainians living in Portugal.
Name evokes warmth (pastel colors, Portuguese pastel de nata) and accessibility.

- **Site:** pashtelka.faion.net
- **Telegram:** @pashtelka_news
- **Bot:** @nero_open_bot (shared infrastructure)
- **Language:** Ukrainian (all content), Portuguese (source references)
- **Target audience:** 56,000+ Ukrainians in Portugal

## Tech Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Site | Gatsby 5 + React | Static site, same as neromedia |
| Content | Markdown + frontmatter | Single language (UA), no translation needed |
| Pipeline | Python 3.11+ | Synchronous, based on neromedia pattern |
| LLM | Claude (via claude CLI) | All stages use Opus |
| Images | gpt-image-1.5 | Comic-style illustrations |
| TG posting | @nero_open_bot | Telegram Bot API via Python |
| Deploy | GitHub → faion-net server | Gatsby build + nginx |
| Weather API | IPMA open API | JSON, no auth required |
| Transport | Metro Lisboa API | JSON, no auth |
| Hosting | faion-net (46.225.58.119) | Shared with other faion projects |

## Architecture Decisions

### ADR-001: Single Language (Ukrainian Only)
No translation pipeline needed. All content generated directly in Ukrainian.
Unlike neromedia (8 languages), pashtelka serves one linguistic community.

### ADR-002: One Author Persona
Single consistent voice (Oksana Lytvyn) instead of multiple characters.
Builds trust and recognition. Simpler editorial pipeline.

### ADR-003: Source-First Journalism
Every article MUST cite Portuguese sources. We compile and translate/adapt,
never fabricate. Source URLs always included in article frontmatter and body.

### ADR-004: Practical Utility Focus
Beyond news, the outlet provides actionable utility information:
water/electricity outages, transport disruptions, immigration updates,
tax deadlines. This is the unique value proposition vs generic news.

### ADR-005: Comic-Style Illustrations
All article images are comic-style illustrations, not stock photos.
Creates consistent visual brand, avoids copyright issues with news photos.

### ADR-006: Reuse Neromedia Infrastructure
Pipeline architecture, Gatsby setup, deploy scripts, bot infrastructure
all based on neromedia patterns. Reduces development effort.

### ADR-007: City-Based Hashtag System
Every article tagged with relevant city hashtags (#Lisbon #Porto #Faro etc.)
Allows readers to filter by their location. Topic hashtags for content type.

## Content Standards

- Sources always cited with URL
- No fabrication or speculation presented as fact
- Utility info (outages, disruptions) verified before publishing
- Tone: warm, friendly, light humor — never alarmist
- No political advocacy — neutral reporting with context
- Immigration/legal info includes disclaimer: "consult a lawyer for your case"

## Quality Gates

1. Every article must have at least 1 source URL
2. Utility alerts must be verified against official source
3. No article published without editorial review stage
4. Site deploy verified before TG posting
5. All hashtags must be from approved taxonomy
