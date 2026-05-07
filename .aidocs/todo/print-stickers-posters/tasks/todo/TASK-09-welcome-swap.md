# TASK-09 — Welcome-landing import swap (Phase 4b)

**Phase:** 4b
**Subject:** Swap the welcome-landing hero placeholder for the now-canonical
brand mascot. Per `welcome-landing/done.md` "Mascot placeholder swap"
section.

## Files touched

- `gatsby/scripts/gen-welcome-assets.mjs` — add `--source` flag to skip
  OpenAI and re-encode from a local file (or new sub-command `from-brand`)
- `gatsby/src/images/welcome/hero-placeholder.{png,webp,avif}` —
  re-emitted from the brand mascot
- `gatsby/src/pages/uk/welcome.js`, `gatsby/src/pages/pt/welcome.js` — if
  needed, update import paths (likely no change — the variants stay at the
  same path, just regenerated)

## Approach

1. Edit `gen-welcome-assets.mjs`: add `--source <path>` flag. When set, skip
   the OpenAI call and use the local PNG as the input for the sharp resize
   chain.
2. Run:
   ```bash
   cd gatsby
   node scripts/gen-welcome-assets.mjs hero --source ../gatsby/src/images/brand/pashtelka-mascot.png
   ```
3. Verify the AVIF/WebP/PNG variants are regenerated and pass the existing
   welcome-landing test plan (≤80 KB AVIF, ≥940 px PNG width).
4. `npm run build` — must exit 0.
5. Visually open `/uk/welcome/` and `/pt/welcome/` in a browser; confirm
   the new mascot loads.

## Success criterion

- `gen-welcome-assets.mjs` accepts `--source` flag.
- Three welcome hero variants re-emitted from brand mascot.
- AVIF still ≤ 80 KB, PNG width ≥ 940.
- `npm run build` exits 0.
