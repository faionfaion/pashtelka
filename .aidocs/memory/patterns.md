# Learned Patterns

## TG Post Format
- Photo + caption (sendPhoto) works better than text + preview (sendMessage)
- NBSP invisible link trick works for OG preview but photo+caption is preferred
- Vocab spoilers: `term — <tg-spoiler>translation</tg-spoiler>`
- Max caption ~1024 chars for photo messages

## Image Generation
- gpt-image-1 comic style: JPEG, max 1200px wide, quality=85 → ~280KB
- PNG from API is 3-4MB → always convert to JPEG
- Style prefix: "Portuguese azulejo tiles, yellow tram, sardines, pastel de nata"
- No text in images, no real people

## Deploy
- faion-net server: SSH port 22022, user faion, key id_ed25519
- Must `git checkout -- . && git clean -fd` before pull (build artifacts conflict)
- nginx serves /var/www/pashtelka.faion.net/, SSL via Cloudflare proxy

## Vocabulary Translations
- Must be literal dictionary translations, not paraphrases
- "lista de espera" = "список очікування" (NOT "черга")
- No explanations in parentheses — just word and translation
