# welcome-landing — done

Shipped (master, 7 tasks, single-repo, 8 commits):

- Two locale routes — `/uk/welcome/` (UA) and `/pt/welcome/` (PT B1) — with hero + 3 bullets + Telegram CTA + secondary CTA + trust footer + Plausible (`welcome_view`, `welcome_tg_click`, `welcome_site_click`) + OG/Twitter cards. PT TG handle is `@pastelka_pt` (channel will be created separately by the operator before the Lisbon launch).
- `/welcome/` static redirect (1.3 KB, 3 layers: navigator.languages → meta-refresh → visible UA/PT links). UTM search params passthrough on redirect.
- Hero placeholder + OG cards generated via OpenAI gpt-image-1 + sharp (one-shot script `gatsby/scripts/gen-welcome-assets.mjs`, idempotent). Hero: 940×940 AVIF/WebP/PNG. OG cards: exactly 1200×630 PNG.
- Above-the-fold weight uncompressed: UK 249 420 B / PT 248 977 B — both within the 250 KB budget. Real-world over gzip will be ~75-90 KB.

## Rollback

`git revert eaf6d67d^..0add73e4` (the welcome-landing range, 8 commits). All changes are additive — no edits to `pipeline/`, `gatsby-node.js`, or `gatsby-config.js`. Reverting removes the three URLs and the assets cleanly.

## Mascot placeholder swap

The hero image at `gatsby/src/images/welcome/hero-placeholder.{png,webp,avif}` is a **placeholder** generated today. The canonical pashtelka mascot is being designed in the separate feature `print-stickers-posters`, slated for `gatsby/src/images/brand/pashtelka-mascot.png`. To swap:

1. Drop the canonical PNG (≥940 px wide) into `gatsby/src/images/brand/pashtelka-mascot.png`.
2. Edit the `gen-welcome-assets.mjs` script to read that file instead of calling OpenAI (or add a `--source` flag) and re-emit the AVIF/WebP/PNG variants under `gatsby/src/images/welcome/`.
3. Update the import paths in `gatsby/src/pages/uk/welcome.js` and `gatsby/src/pages/pt/welcome.js` to point at the new variants.
4. Re-run `npm run build` and visually verify both routes.

## Operator items before / after deploy

- **Plausible:** add `pastelka.news` to your Plausible workspace if not already present. Until then, `welcome_view` / `welcome_tg_click` / `welcome_site_click` events 404 silently — no breakage.
- **PT TG channel:** create `@pastelka_pt` before printing PT-locale stickers. The CTA link is hard-coded to that handle; if the channel doesn't exist at scan time the CTA shows TG's "Channel not found" message.
- **Lighthouse mobile perf:** could not run in the build sandbox (no Chrome binary). Operator runs from a workstation:

```bash
cd ~/workspace/projects/pashtelka-faion-net/gatsby
npx --yes gatsby serve --port 9000 &
sleep 4
npx --yes lighthouse http://localhost:9000/uk/welcome/ \
  --form-factor=mobile --throttling.cpuSlowdownMultiplier=4 --quiet \
  --only-categories=performance --output=json --output-path=/tmp/lh-uk.json
jq '.categories.performance.score' /tmp/lh-uk.json   # expect ≥ 0.90
```

(Same for `/pt/welcome/`.)

- **Telegram preview validation:** after `deploy-gh.sh`, send `https://pastelka.news/uk/welcome/` and `…/pt/welcome/` to a TG chat and confirm the OG card thumbnail renders. Or use `https://www.opengraph.xyz/url/<urlencoded>`.

## Out of scope (open follow-ups)

- Replace placeholder mascot with canonical brand mascot → `print-stickers-posters`.
- 404 → Telegram alert wiring → existing pipeline notification SDD.
- Per-sticker UTM token in TG `?start=` → analytics follow-up.
