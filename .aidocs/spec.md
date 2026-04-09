# Pashtelka Product Specification

## Problem Statement

56,000+ Ukrainians live in Portugal with no dedicated Ukrainian-language news source.
They rely on Portuguese media (language barrier), general Ukrainian media (no Portugal focus),
or informal community channels (unreliable, unstructured).

## Target Audience

### Primary: Ukrainian residents in Portugal
- Age: 25-45 (working age, highest digital engagement)
- Locations: Lisbon (22%), Greater Lisbon (15%), Porto (8%), Algarve (7%)
- Needs: local news, immigration updates, utility alerts, community info
- Language: Ukrainian (primary), basic Portuguese (many still learning)
- Devices: smartphone-first (80%+ TG usage on mobile)

### Secondary: Ukrainians considering moving to Portugal

## Distribution

### Telegram Channel (@pashtelka_news)
Primary distribution. 5 posts/day:
- 4 articles at 9:00, 12:00, 15:00, 18:00 (best from site)
- 1 evening digest at 20:00 (5-10 links to day's articles)

### Website (pastelka.news)
Full articles published continuously (up to 13/day, hourly 7-19).
TG posts link to website for full reads.

## TG Post Format

```
<b>{hook headline}</b>

{2-3 sentences with <b>accent words</b>}

<a href="url">Дізнатись більше →</a>

📖 Словничок:
termo — <tg-spoiler>переклад</tg-spoiler>
...

🇵🇹 Паштелька News (link to channel)
```

Sent as photo + HTML caption (sendPhoto API).

## Content Types

| Type | Per Day | Words | Description |
|------|---------|-------|-------------|
| `news` | 6-8 | 300-600 | Breaking/daily Portuguese news |
| `material` | 1-2 | 600-1500 | Compiled from 3+ sources |
| `utility` | 0-2 | 150-400 | Service alerts, disruptions |
| `immigration` | 0-1 | 400-800 | AIMA/legal updates |
| `guide` | 0-1 | 800-2000 | Practical guides |
| `digest` | 1 | — | Evening TG digest (links only) |

## Editorial Pipeline

1. **Plan** (daily, auto): LLM creates 10-12 topics with context of last 30 days
2. **Generate** (hourly 7-19): research → write → review → deploy to site
3. **Publish** (4x/day): pick best unpublished → TG caption → send
4. **Digest** (20:00): compile day's best → TG digest

## Vocabulary Section

Each TG post includes 3-5 Portuguese terms with Ukrainian translations:
- Literal dictionary translations only (not paraphrases)
- Portuguese term first, Ukrainian under spoiler tag
- Words relevant to article topic and daily life in Portugal

## Sources

### Tier 1 (RSS, daily)
- RTP Noticias (public broadcaster, 8 category feeds)
- Publico, CM Jornal (RSS)

### Tier 2 (Web search per topic)
- Observador, JN, NaM
- Municipal portals (CM Lisboa, CM Porto, CM Faro)

### Tier 3 (Specialized)
- AIMA (immigration), Portal das Financas (tax)
- IPMA API (weather), Metro Lisboa API (transport)
- E-REDES (electricity), EPAL (water), CP (trains)

## Success Metrics

| Metric | 3 months | 6 months |
|--------|----------|----------|
| TG subscribers | 500 | 2,000 |
| Daily TG views | 1,000 | 5,000 |
| Site daily visits | 100 | 500 |
| Articles/day | 8-12 | 10-15 |
