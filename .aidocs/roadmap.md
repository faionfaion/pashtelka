# Pashtelka Roadmap

## Phase 1: Foundation — DONE
- [x] Market research (Ukrainian diaspora, Portuguese news sources)
- [x] Product spec, constitution, editorial guidelines
- [x] Pipeline: collect → research → generate → review → deploy → publish
- [x] Gatsby site with warm amber/dark theme
- [x] Comic-style image generation (gpt-image-1)
- [x] TG channel setup (avatar, bio, initial posts)
- [x] Domain: pastelka.news (Cloudflare DNS + nginx on faion-net)
- [x] SSH deploy pipeline (git push → SSH → gatsby build → rsync)
- [x] 26 initial articles published

## Phase 2: Editorial Automation — DONE
- [x] 3-mode pipeline: generate / publish / digest
- [x] Editorial planning (daily plan with 30-day context)
- [x] Cron schedule: generate (7-19), publish (9,12,15,18), digest (20:00)
- [x] TG format: photo + caption with vocab spoilers
- [x] Cross-referencing (follow-up articles link to previous coverage)
- [x] State tracking: plans, tg_published, posted, teasers
- [x] Vocabulary section with literal translations

## Phase 3: Quality & Growth — IN PROGRESS
- [ ] OpenAI API key in cron environment (image generation)
- [ ] Guardian-style health monitoring (pipeline failures, site uptime)
- [ ] SEO optimization (sitemap, structured data, meta)
- [ ] Cross-promotion in Ukrainian community groups
- [ ] Analytics integration (Plausible or similar)
- [ ] TG channel growth tactics (pinned intro post, community seeding)
- [ ] Content quality tracking (review scores over time)

## Phase 4: Expansion
- [ ] Weekly practical guides (immigration, taxes, healthcare)
- [ ] Immigration law tracker (AIMA changes monitoring)
- [ ] Tax calendar with automated reminders
- [ ] Community events aggregation
- [ ] Weather alerts (IPMA API integration for morning brief)
- [ ] Transport disruption alerts (Metro, CP APIs)
- [ ] Reader engagement (reactions tracking, topic voting)

## Phase 5: Scale
- [ ] City-specific content targeting
- [ ] Podcast (weekly news review in Ukrainian)
- [ ] Newsletter (weekly email digest)
- [ ] Advertising/sponsorship model
- [ ] Community contributions (reader tips pipeline)

## Risks

| Risk | Mitigation |
|------|-----------|
| RSS feeds break | Multiple sources, web search fallback |
| Content quality drift | Editorial review loop, voice prompt refinement |
| Low initial engagement | Utility value (alerts, guides), community seeding |
| Legal issues | Compile/rewrite only, always cite sources |
| Pipeline cost | Single language, editorial plan prevents waste |
| OpenAI key expiry | Monitor, alert on image gen failures |
