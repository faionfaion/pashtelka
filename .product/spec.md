# Pashtelka Product Specification

## Problem Statement

56,000+ Ukrainians live in Portugal with no dedicated Ukrainian-language news source.
They rely on Portuguese media (language barrier), general Ukrainian media (no Portugal focus),
or informal community channels (unreliable, unstructured).

## Target Audience

### Primary: Ukrainian residents in Portugal
- Age: 25-45 (working age, highest digital engagement)
- Locations: Lisbon (22%), Greater Lisbon (15%), Porto (8%), Algarve (7%), rest scattered
- Needs: local news, immigration updates, utility alerts, community info
- Language: Ukrainian (primary), basic Portuguese (many still learning)
- Devices: smartphone-first (80%+ TG usage on mobile)

### Secondary: Ukrainians considering moving to Portugal
- Need: practical guides, legal info, community insights

## Product Definition

### Telegram Channel (@pashtelka_news)
Primary distribution. 12+ posts/day covering:
- Breaking Portuguese news relevant to Ukrainian community
- Immigration/AIMA updates
- Utility alerts (water, electricity, transport)
- Municipal announcements
- Tax/legal deadlines
- Community events
- Evening daily digest

### Website (pashtelka.faion.net)
Full articles with extended content, images, source links.
Telegram posts link to website for full reads.

## Content Types

| Type | Count/Day | Length | Description |
|------|-----------|--------|-------------|
| `news` | 8-10 | 400-600w | Breaking/daily news from Portuguese sources |
| `utility` | 1-2 | 200-400w | Service alerts, outages, disruptions |
| `immigration` | 1 | 500-800w | AIMA/legal updates, deadline reminders |
| `digest` | 1 | 600-1000w | Evening summary of day's news |
| `material` | 2 | 800-1500w | Compiled analytical articles on topics |
| `guide` | 1/week | 1000-2000w | Practical guides (tax filing, healthcare, etc.) |

## Author Persona: Oksana Lytvyn

**Full name:** Оксана Литвин (Oksana Lytvyn)
**Bio:** Ukrainian journalist, 34, living in Lisbon since 2018. Former reporter at regional
Ukrainian outlet. Moved to Portugal, fell in love with the country. Knows both the expat
and local communities well. Speaks Portuguese fluently.

**Voice characteristics:**
- Warm, friendly, approachable — like a knowledgeable friend
- Light humor, occasional wordplay (UA/PT mix)
- Empathetic — understands the challenges of life abroad
- Never condescending or alarmist
- Uses casual but grammatically correct Ukrainian
- Occasionally drops Portuguese words/phrases with Ukrainian explanation
- Signs off posts with characteristic phrases

**Writing style:**
- Short paragraphs (2-3 sentences max)
- Active voice, present tense for news
- Starts with the most important info (inverted pyramid for news)
- Adds personal touch: "I checked this myself" / "My neighbor told me"
- Uses Ukrainian equivalents for Portuguese terms with original in brackets
- Emoji usage: minimal, tasteful (no walls of emoji)

**Catchphrases:**
- "Ваша Оксана з Лісабона" (Your Oksana from Lisbon) — sign-off
- "Що нового в наших пастелах" (What's new in our pastels) — morning greeting
- "Бережіть себе, пастелкові" (Take care, pastelkovians) — evening sign-off

## Hashtag Taxonomy

### City Tags
- #Лісабон — Lisbon
- #Порту — Porto
- #Фару — Faro
- #Алгарве — Algarve region
- #ВеликийЛісабон — Greater Lisbon (Cascais, Sintra, Amadora, Oeiras)
- #Кашкайш — Cascais
- #Сінтра — Sintra
- #Албуфейра — Albufeira
- #Коїмбра — Coimbra
- #Брага — Braga

### Topic Tags
- #Новини — General news
- #Імміграція — Immigration/AIMA
- #Податки — Taxes
- #Транспорт — Transport
- #Погода — Weather
- #Комуналка — Utilities (water, electricity)
- #Здоровя — Healthcare
- #Освіта — Education
- #Робота — Employment
- #Житло — Housing
- #Безпека — Safety/security
- #Культура — Culture/events
- #Спорт — Sports
- #Діаспора — Ukrainian community
- #Дайджест — Daily digest
- #Гайд — Practical guide
- #Матеріал — In-depth compiled article

## Publishing Schedule

### Daily Schedule (Lisbon time, UTC+0/+1)

| Time | Slot | Content Type |
|------|------|-------------|
| 08:00 | Morning greeting | Brief weather + top story preview |
| 09:00 | News 1 | Breaking/morning news |
| 10:00 | News 2 | News or utility alert |
| 11:00 | News 3 | News |
| 12:00 | Material 1 | Compiled article on trending topic |
| 13:00 | News 4 | News |
| 14:00 | News 5 | News or immigration update |
| 15:00 | News 6 | News |
| 16:00 | Material 2 | Compiled article |
| 17:00 | News 7 | News |
| 18:00 | News 8 | News |
| 19:00 | News 9 | News or utility |
| 20:00 | News 10 | Last news of the day |
| 21:00 | Digest | Evening digest of all day's news |

### Weekly Specials
- Monday: Immigration/AIMA weekly update
- Wednesday: Practical guide (rotating topics)
- Friday: Week in review (extended digest)
- Saturday: Community events for the weekend

## Success Metrics

| Metric | Target (3 months) | Target (6 months) |
|--------|-------------------|-------------------|
| TG subscribers | 500 | 2,000 |
| Daily TG views | 1,000 | 5,000 |
| Site daily visits | 100 | 500 |
| Articles/day | 12 | 15 |
| Source diversity | 5+ sources/day | 10+ sources/day |

## Sources Priority

### Tier 1 (Daily monitoring, RSS/API)
- RTP Noticias (8 category RSS feeds, free, public broadcaster)
- Noticias ao Minuto (breaking news, RSS)
- IPMA API (weather, warnings — JSON, no auth)
- Metro Lisboa API (disruptions — JSON, no auth)

### Tier 2 (Regular monitoring)
- Publico (RSS, metered paywall — use free articles)
- Observador (RSS, freemium)
- Correio da Manha (RSS, free)
- Jornal de Noticias (Porto-focused)

### Tier 3 (Topic-specific)
- AIMA (aima.gov.pt — immigration updates)
- Portal das Financas (tax deadlines)
- CM Lisboa, CM Porto, CM Faro (municipal portals)
- E-REDES (electricity outages)
- EPAL (water — Lisbon)
- CP (train disruptions)
- Sul Informacao (Algarve news)

### Tier 4 (English sources for cross-reference)
- The Portugal News
- Portugal Resident
- Algarve Daily News
