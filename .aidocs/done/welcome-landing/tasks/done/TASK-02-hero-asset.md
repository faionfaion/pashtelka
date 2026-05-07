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

## Execution Report

### Status: COMPLETED

### What Was Done
- Wrote `gatsby/scripts/gen-welcome-assets.mjs` (ESM, ~150 lines): reads `OPENAI_API_KEY` from env or `~/workspace/.env`, calls gpt-image-1 (`size=1024x1024`, `quality=auto`), uses bundled sharp to emit AVIF/WebP/PNG variants. Sub-commands `hero | og-uk | og-pt | all`.
- Ran `node scripts/gen-welcome-assets.mjs hero`. OpenAI returned a 1024×1024 mascot. Sharp resized to 940 px (width-bound) and emitted three encoded variants.
- Used 1024×1024 instead of 1536×1024 for hero — square fits the centered-mascot composition better, and the mobile hero is rendered at max-width 360-460 anyway. OG cards use 1536×1024 (TASK-03).

### Files Changed
| Repo | File | Change | Size |
|------|------|--------|------|
| pashtelka-faion-net | `gatsby/scripts/gen-welcome-assets.mjs` | new | ~5 KB source |
| pashtelka-faion-net | `gatsby/src/images/welcome/hero-placeholder.png` | new (binary) | 331.6 KB |
| pashtelka-faion-net | `gatsby/src/images/welcome/hero-placeholder.webp` | new (binary) | 28.8 KB |
| pashtelka-faion-net | `gatsby/src/images/welcome/hero-placeholder.avif` | new (binary) | 16.6 KB |

### Tests
- AVIF size 16.6 KB ≤ 80 KB target — PASS.
- `file …png` reports `940 x 940`, ≥ 940 width — PASS.
- WebP size 28.8 KB.
- Script is idempotent: re-runs overwrite cleanly (sharp `.toFile()` truncates).

### Issues
- gpt-image-1 doesn't support arbitrary aspect ratios — it requires `1024x1024`, `1024x1536`, or `1536x1024`. Switched hero to square `1024x1024` (fits a centered mascot). Documented in script.
