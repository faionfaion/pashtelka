# Key Decisions

## 2026-04-09: Removed author persona
Removed "Oksana Lytvyn" from everywhere. Content now published as "Паштелька News".
**Why:** User decision — no fictional persona for AI-generated content.

## 2026-04-09: Domain pastelka.news (no 'h')
User registered pastelka.news instead of pashtelka.news.
**Why:** Shorter, cleaner domain. "Паштелька" in Ukrainian, "Pastelka" in URL.

## 2026-04-09: Photo+caption instead of Instant View
Switched from text message with IV to sendPhoto with HTML caption.
**Why:** More visual, works reliably, shows image directly in feed.

## 2026-04-09: 3-mode pipeline architecture
Split monolithic pipeline into generate/publish/digest modes.
**Why:** Site gets 13 articles/day, TG only gets 4 best + 1 digest. No TG spam.

## 2026-04-09: Editorial planning with 30-day context
Added s0_editorial_plan that reads last 30 days of articles before planning.
**Why:** Prevents topic repetition, ensures diversity, enables follow-up articles.

## 2026-04-09: No hashtags in TG posts
Removed all hashtags from TG posts.
**Why:** User feedback — hashtags not used by readers, just noise.
