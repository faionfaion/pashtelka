# Mistakes and Solutions

## SameFileError in deploy
**Problem:** image_gen saves to IMAGES_DIR, deploy tried to copy to same path
**Fix:** Added `if ctx.image_path.resolve() != dest.resolve()` check

## SSH denied / fail2ban
**Problem:** Multiple failed SSH attempts triggered fail2ban on faion-net
**Fix:** Generate new ed25519 key, add to server, unban IP from macbook

## Cloudflare Pages conflict
**Problem:** Old Pages custom domain intercepted traffic for pashtelka.faion.net
**Fix:** Remove Pages custom domain via Cloudflare API, use A record to server

## Nginx 404
**Problem:** nginx on port 80 but Cloudflare Full SSL expects 443
**Fix:** Changed to `listen 443 ssl http2` with snakeoil cert

## OG images not showing in TG
**Problem:** PNG files 3.5MB too large for TG crawler
**Fix:** Convert all to JPEG via Pillow (~280KB, 92% reduction)

## GitHub push rejected (secret detection)
**Problem:** Hardcoded OpenAI API key in code
**Fix:** Load from environment variable only, empty fallback

## Domain typo: pashtelka vs pastelka
**Problem:** User registered pastelka.news (no 'h') while code had pashtelka
**Fix:** Mass replacement across 31 files

## Vocabulary translations too free
**Problem:** LLM translated "lista de espera" as "черга" instead of "список очікування"
**Fix:** Updated prompts to require literal dictionary translations, added examples
