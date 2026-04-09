# Pashtelka Constitution

## Product Identity

**Паштелька News** — Ukrainian-language news media for Ukrainians in Portugal.

- **Site:** https://pastelka.news
- **Telegram:** @pashtelka_news
- **Bot:** @nero_open_bot (shared with neromedia)
- **Language:** Ukrainian (content), Portuguese (sources)
- **Target audience:** 56,000+ Ukrainians in Portugal

## Tech Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Site | Gatsby 5 + React | SSG, deployed to faion-net nginx |
| Content | Markdown + frontmatter | Single language (UA) |
| Pipeline | Python 3.11+ | Synchronous, 3 modes: generate/publish/digest |
| LLM | Claude Opus via CLI | All stages (research, generate, review, TG, editorial plan) |
| Images | OpenAI gpt-image-1 | Comic-style JPEG illustrations |
| TG posting | Bot API (sendPhoto) | Photo + HTML caption format |
| Deploy | git push → SSH → gatsby build → rsync | faion-net server |
| DNS | Cloudflare | pastelka.news zone |
| Hosting | faion-net (46.225.58.119:22022) | Shared nginx, SSL via Cloudflare |

## Architecture

### Pipeline Modes

| Mode | Schedule | Purpose |
|------|----------|---------|
| `plan` | Auto (first generate of day) | Editorial plan: 10-12 topics based on RSS + last 30 days context |
| `generate` | Cron `0 7-19 * * *` | Take next topic from plan → research → write → review → deploy to site |
| `publish` | Cron `5 9,12,15,18 * * *` | Pick best unpublished article → generate TG caption → send photo+caption |
| `digest` | Cron `5 20 * * *` | Compile day's articles → evening digest post to TG |

### Pipeline Stages (generate mode)

```
s0_editorial_plan → s1_collect → s2_research → s3_generate → s4_review → s5_revise → s7_deploy → s8_verify
```

### State Files

| Path | Purpose |
|------|---------|
| `state/plans/{date}.json` | Daily editorial plan |
| `state/plans/{date}_written.json` | Topics already taken from plan |
| `state/tg_published/{date}.json` | Articles published to TG today |
| `state/posted/{date}.json` | Slot-based post tracking |
| `state/teasers/{slug}.json` | TG captions per article |
| `state/runs/{timestamp}.json` | Pipeline run reports |
| `state/logs/` | Pipeline and cron logs |

## Architecture Decisions

### ADR-001: Single Language (Ukrainian Only)
No translation pipeline. All content generated directly in Ukrainian.
Unlike neromedia (multi-language), pashtelka serves one community.

### ADR-002: No Author Persona
Content published as "Паштелька News" editorial team. No personal name or persona.
Avoids trust issues with AI-generated content attributed to a fictional person.

### ADR-003: Source-First Journalism
Every article MUST cite Portuguese sources with URLs.
We compile and translate/adapt, never fabricate.

### ADR-004: Editorial Planning
Daily editorial plan created by LLM with context of last 30 days of articles.
Prevents topic repetition, ensures diversity, follows news continuity.

### ADR-005: Comic-Style Illustrations
All images are gpt-image-1 comic-style illustrations.
Consistent visual brand, avoids copyright issues with news photos.
Portuguese visual elements: azulejo tiles, yellow tram, sardines, pastel de nata.

### ADR-006: Separate Site and TG Publishing
Articles deploy to site continuously (hourly). TG posts only 4x/day + digest.
Avoids TG channel spam while keeping site fresh.

### ADR-007: Cross-Reference Continuity
When a story has new developments, articles reference previous coverage.
Builds narrative continuity for regular readers.

### ADR-008: Vocabulary Section in TG Posts
Each TG post includes 3-5 Portuguese words with literal Ukrainian translations.
Educational value for diaspora learning Portuguese. Translations under spoiler tags.

## Content Standards

- Sources always cited with URL
- No fabrication or speculation as fact
- Tone: warm, friendly, light humor — never alarmist
- No political advocacy — neutral reporting with context
- Immigration/legal info includes disclaimer
- Vocabulary translations must be literal dictionary equivalents

## Quality Gates

1. Every article reviewed by LLM reviewer (min 1 revision cycle)
2. Site deploy verified (HTTP 200 + title check) before TG posting
3. Editorial plan checked against last 30 days to avoid repetition
4. TG captions use photo+caption format with vocab section
