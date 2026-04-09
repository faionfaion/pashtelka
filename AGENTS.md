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
| `generate` | `0 7-19 * * *` | Editorial plan → research → write → review → deploy to site |
| `publish` | `5 9,12,15,18 * * *` | Pick best article → TG caption → send photo+caption |
| `digest` | `5 20 * * *` | Compile day's articles → evening digest to TG |
| `plan` | Auto / manual | Create daily editorial plan (10-12 topics) |

## Key Commands

```bash
python3 -m pipeline generate -v   # Generate one article
python3 -m pipeline publish -v    # Publish best to TG
python3 -m pipeline digest -v     # Evening digest
python3 -m pipeline plan -v       # Show editorial plan
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
