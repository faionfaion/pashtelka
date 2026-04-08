# Pashtelka Roadmap

## Phase 1: Foundation (Current)
**Goal:** Working pipeline + site + first publications

- [x] Market research (Ukrainian diaspora, Portuguese news sources)
- [x] Product spec (content types, schedule, author persona)
- [x] Constitution (tech decisions, architecture)
- [ ] Project structure (pipeline, gatsby, scripts)
- [ ] Author voice prompts (Oksana Lytvyn persona)
- [ ] Source ingestion setup (RSS feeds, IPMA API)
- [ ] Basic pipeline: collect → research → generate → deploy → publish
- [ ] Gatsby site with minimal theme
- [ ] First test articles (5-10 manual pipeline runs)
- [ ] TG channel setup (bio, avatar, pinned intro post)

## Phase 2: Automation
**Goal:** Fully automated daily publishing

- [ ] Cron-based pipeline execution (14 slots/day)
- [ ] RSS feed monitoring for breaking news
- [ ] IPMA weather integration (morning weather brief)
- [ ] Metro/transport disruption alerts (automated)
- [ ] Evening digest auto-generation from day's articles
- [ ] State management (dedup, posted tracking, slot planning)
- [ ] Image generation pipeline (comic-style illustrations)

## Phase 3: Quality & Growth
**Goal:** Consistent quality, growing audience

- [ ] Editorial review loop (generate → review → revise)
- [ ] Guardian-style health monitoring
- [ ] SEO optimization (meta, structured data, sitemap)
- [ ] Cross-promotion (Ukrainian community groups)
- [ ] Analytics integration
- [ ] Reader engagement features (reactions, comments concept)

## Phase 4: Expansion
**Goal:** Full-featured media outlet

- [ ] Weekly practical guides
- [ ] Immigration law tracker (AIMA changes monitoring)
- [ ] Tax calendar with automated reminders
- [ ] Community events aggregation
- [ ] City-specific digest channels (optional: Lisbon, Porto sub-channels)
- [ ] Podcast (Ukrainian, weekly news review)

## Dependencies

```
Phase 1 → Phase 2 → Phase 3 → Phase 4
                ↘ Phase 3 (partially parallel)
```

## Risks

| Risk | Mitigation |
|------|-----------|
| Source RSS feeds break | Multiple sources per topic, fallback to web scraping |
| Content quality inconsistent | Editorial review loop, voice prompt refinement |
| Low initial engagement | Cross-promote in Ukrainian community groups, utility value |
| Legal issues with source content | Always compile/rewrite, never copy verbatim, cite sources |
| Pipeline cost (LLM API) | Single language (no translation), optimize prompts |
