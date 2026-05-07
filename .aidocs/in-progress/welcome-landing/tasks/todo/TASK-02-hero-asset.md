# TASK-02 — Hero placeholder via OpenAI gpt-image-1 + sharp variants

**Subject:** Generate a temporary mascot hero image via OpenAI gpt-image-1
and produce AVIF + WebP + PNG variants with `sharp`.

## Files touched

- `gatsby/scripts/gen-welcome-assets.mjs` (new)
- `gatsby/src/images/welcome/hero-placeholder.png` (new — raw)
- `gatsby/src/images/welcome/hero-placeholder.avif` (new — re-encoded)
- `gatsby/src/images/welcome/hero-placeholder.webp` (new — re-encoded)

## Approach

ESM Node script that:

1. Reads `OPENAI_API_KEY` from env or `~/workspace/.env`.
2. Calls `https://api.openai.com/v1/images/generations`,
   `model=gpt-image-1`, `size=1536x1024`, `quality=auto`, base64 response.
3. Writes raw PNG to disk, then uses `sharp` to:
   - resize to 940 px wide max,
   - emit AVIF at quality 50,
   - emit WebP at quality 70,
   - emit a smaller PNG fallback (final, replaces raw).
4. Sub-commands: `node scripts/gen-welcome-assets.mjs hero` (this task),
   `… og-uk` and `… og-pt` (TASK-03).

The hero prompt is the one documented in `design.md` (Lisbon-coded mascot,
azulejo + tram + bridge).

## Success criterion

- Three files exist under `src/images/welcome/`.
- AVIF file ≤ 80 KB (`stat -c%s …avif`).
- PNG width ≥ 940 px (`file …png` reports it).
- Script is idempotent (re-running overwrites cleanly).
- Script is committed alongside the assets.
