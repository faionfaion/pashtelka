# Pashtelka — Ukrainian News Media in Portugal

News portal for Ukrainian diaspora in Portugal. Site: pashtelka.faion.net, TG: @pashtelka_news.

## Structure

| Path | Purpose |
|------|---------|
| `pipeline/` | Publishing pipeline (Python, based on neromedia pattern) |
| `gatsby/` | Static site (Gatsby 5 + React) |
| `content/` | Markdown articles (Ukrainian) |
| `scripts/` | Utility scripts (send, translate, state) |
| `state/` | Runtime state (plans, posted history) |
| `prompts/` | Editorial prompts, author voice |
| `.product/` | Product docs (spec, constitution, roadmap) |
| `.agents/` | Reference docs (editorial guide, sources) |
| `.aidocs/` | SDD lifecycle docs |

## Quick Reference

- **Bot:** @nero_open_bot (shared with neromedia)
- **Channel:** @pashtelka_news (chat_id: TBD)
- **Author persona:** Oksana Lytvyn
- **Language:** Ukrainian (content), Portuguese (sources)
- **Deploy:** Gatsby build → rsync to faion-net server → nginx
- **Reference project:** ~/workspace/projects/neromedia-faion-net/

## Key Commands

```bash
# Run pipeline
python3 -m pipeline

# Deploy site
bash gatsby/deploy-gh.sh

# Send test post
python3 scripts/send_post.py --channel @pashtelka_news --text "test"
```

## Content Schedule

- 12 news articles/day (hourly 09:00-20:00)
- 1 evening digest (21:00)
- 2+ compiled analytical articles/day
- Hashtags: #Лісабон #Порту #Фару #Алгарве + topic tags

## Sources

Portuguese news (RTP, Publico, Observador, NaM, CM), municipal portals,
AIMA, IPMA API, Metro Lisboa API, E-REDES, EPAL, CP.

Details: `.agents/INDEX.md`
