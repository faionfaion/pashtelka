# Pashtelka — Ukrainian News Media in Portugal

News portal for Ukrainian diaspora in Portugal. Site: pastelka.news, TG: @pashtelka_news.

## Structure

| Path | Purpose |
|------|---------|
| `pipeline/` | Publishing pipeline (Python, 3 modes: generate/publish/digest) |
| `pipeline/stages/` | Pipeline stages (s0-s11) |
| `gatsby/` | Static site (Gatsby 5 + React) |
| `content/` | Markdown articles (Ukrainian) |
| `scripts/` | Cron runner, regen, republish utilities |
| `state/` | Runtime state (plans, teasers, posted, logs) |
| `.aidocs/` | SDD docs (constitution, spec, roadmap, memory) |
| `.product/` | Legacy product docs (superseded by .aidocs) |

## Pipeline Modes

| Mode | Cron | What |
|------|------|------|
| `generate` | `17 1 * * *` | Night batch (01:17 UTC): editorial plan → 1 material + 1 guide + 10 news → 1 deploy |
| `digest` | `0 20 * * *` | 20:00 UTC = 21:00 Lisbon (WEST). Single daily TG post: 10 news + 2-word glossary + premium image |
| `plan` | Manual | Show/create daily editorial plan |

**Digest-only model (2026-04-24):** per-slot publishes removed. TG gets one high-quality post per day at 21:00 Lisbon. Material and guide live on the site only, surfaced via "Читайте також" blocks at the bottom of news articles.

## Key Commands

```bash
python3 -m pipeline generate -v       # Batch generate all articles for the day
python3 -m pipeline publish -v        # Mechanical TG publish (no LLM)
python3 -m pipeline digest -v         # Evening digest
python3 -m pipeline plan -v           # Show editorial plan
python3 -m pipeline generate --dry-run  # Test without deploy
```

## Quick Reference

- **Bot:** @nero_open_bot (shared with neromedia)
- **Channel:** @pashtelka_news (chat_id: -1003726391778)
- **Domain:** pastelka.news (Cloudflare DNS → faion-net nginx)
- **Deploy:** git push → SSH faion@46.225.58.119:22022 → gatsby build → rsync
- **LLM:** All stages use Claude Opus via CLI
- **Images:** OpenAI gpt-image-1, comic style, JPEG

## Sources

RSS: RTP, Publico, CM Jornal. Web search per topic.
APIs: IPMA (weather), Metro Lisboa (transport).

Details: `.aidocs/INDEX.md`
