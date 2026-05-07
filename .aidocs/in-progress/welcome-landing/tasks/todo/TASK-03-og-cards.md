# TASK-03 — OG cards (UA + PT) at exactly 1200×630

**Subject:** Generate the two Open Graph share cards via the same OpenAI
flow + `sharp` crop.

## Files touched

- `gatsby/static/og/welcome-uk.png` (new)
- `gatsby/static/og/welcome-pt.png` (new)
- `gatsby/scripts/gen-welcome-assets.mjs` (extended with `og-uk` / `og-pt`
  sub-commands)

## Approach

Extend the script from TASK-02. Two prompts (`design.md`), each producing
1536×1024 → cropped to **exactly** 1200×630 with `sharp.extract` after
resizing the long edge. Save as PNG (Telegram preview prefers PNG over
WebP; size budget ≤ 250 KB per card).

UA prompt: Cyrillic overlay "Новини Португалії українською".
PT prompt: Latin overlay "Notícias de Portugal em ucraniano — para a
comunidade".

Note: gpt-image-1 is not reliable for in-image text; if the rendered text
is illegible, fall back to a `sharp.composite` overlay step (text rendered
as SVG → composited as PNG layer). Document the chosen path in the
execution report.

## Success criterion

- Both PNGs exist under `gatsby/static/og/`.
- `file welcome-uk.png` reports `1200 x 630`. Same for PT.
- Each file ≤ 250 KB.
- Image is brand-coloured (warm amber + pastel) and visually matches the
  hero placeholder direction.
