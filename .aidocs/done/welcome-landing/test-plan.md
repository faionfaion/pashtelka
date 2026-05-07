# Test Plan: Bilingual Welcome Landing

**Implements:** spec.md (AC1..AC8), design.md
**Status:** todo

Each AC has at least one verification command + expected result. The plan is
written so a human (or a future agent) can re-run every step from a clean
checkout.

## Pre-flight

```bash
cd ~/workspace/projects/pashtelka-faion-net/gatsby
npm run clean
npm run build
```

Build must finish without error. `public/` will contain
`uk/welcome/index.html`, `pt/welcome/index.html`, `welcome/index.html`,
plus the hero variants under `static/...` and OG images under `og/...`.

After build, serve locally:

```bash
cd ~/workspace/projects/pashtelka-faion-net/gatsby
npx gatsby serve --port 9000 &
SERVE_PID=$!
sleep 3
```

(Tear down with `kill $SERVE_PID` at the end.)

## AC1 — Two locale routes

```bash
curl -sI http://localhost:9000/uk/welcome/ | head -1   # expect: HTTP/1.1 200 OK
curl -sI http://localhost:9000/pt/welcome/ | head -1   # expect: HTTP/1.1 200 OK
curl -s  http://localhost:9000/uk/welcome/ | grep -c 'lang="uk"'   # expect: ≥1
curl -s  http://localhost:9000/pt/welcome/ | grep -c 'lang="pt"'   # expect: ≥1
curl -s  http://localhost:9000/uk/welcome/ | grep -E 'href="/pt/welcome/"' | head -1  # expect: lang switcher present
curl -s  http://localhost:9000/pt/welcome/ | grep -E 'href="/uk/welcome/"' | head -1  # expect: lang switcher present
```

## AC2 — Content blocks

```bash
# UA page must contain hero copy, three bullets, two CTAs, footer trust line
curl -s http://localhost:9000/uk/welcome/ > /tmp/uk.html
grep -c "Новини Португалії українською"     /tmp/uk.html   # ≥1 (hero)
grep -c "t.me/pashtelka_news"                /tmp/uk.html   # ≥1 (TG CTA)
grep -cE 'href="/"'                          /tmp/uk.html   # ≥1 (secondary CTA)
grep -c "Editorial since 2026"               /tmp/uk.html   # ≥1 (trust line)

# PT page B1 copy + @pastelka_pt CTA
curl -s http://localhost:9000/pt/welcome/ > /tmp/pt.html
grep -c "t.me/pastelka_pt"                   /tmp/pt.html   # ≥1
grep -cE "Notícias de Portugal em ucraniano" /tmp/pt.html   # ≥1
```

## AC3 — Mobile-first design + perf budget

### Page weight

```bash
# Above-the-fold: HTML + critical CSS (inline) + JS chunk(s) + hero (AVIF preferred)
cd ~/workspace/projects/pashtelka-faion-net/gatsby/public

UK_HTML_BYTES=$(stat -c%s uk/welcome/index.html)
UK_HERO_BYTES=$(ls -la static/*hero-placeholder*.avif 2>/dev/null | awk '{print $5}' | head -1)
# Sum the gatsby commons + page chunks listed in the HTML
UK_JS_BYTES=$(curl -s http://localhost:9000/uk/welcome/ | grep -oE 'src="/[^"]+\.js"' | sed 's|src="||;s|"||' | xargs -I{} stat -c%s "public{}" 2>/dev/null | paste -sd+ | bc)
echo "UK total: $((UK_HTML_BYTES + UK_HERO_BYTES + UK_JS_BYTES)) bytes (target ≤ 250000)"
```

Expected: total ≤ 250 000 bytes.

Same for `pt/welcome/`.

### Mobile viewport screenshot

Manual procedure — Chromium DevTools mobile emulation:

```bash
# Open in Chromium with 360x640 mobile preset
chromium --headless --disable-gpu \
  --window-size=360,640 \
  --screenshot=/tmp/welcome-uk-mobile.png \
  http://localhost:9000/uk/welcome/

chromium --headless --disable-gpu \
  --window-size=360,640 \
  --screenshot=/tmp/welcome-pt-mobile.png \
  http://localhost:9000/pt/welcome/
```

Visual check: hero readable, primary CTA above the fold, no horizontal
scroll. Save both screenshots into the task report.

### Lighthouse

Lighthouse is not preinstalled on this box. Operator runs:

```bash
npx --yes lighthouse \
  http://localhost:9000/uk/welcome/ \
  --form-factor=mobile \
  --throttling.cpuSlowdownMultiplier=4 \
  --quiet \
  --only-categories=performance \
  --chrome-flags="--headless --no-sandbox" \
  --output=json --output-path=/tmp/lh-uk.json
jq '.categories.performance.score' /tmp/lh-uk.json   # expect: ≥ 0.90

npx --yes lighthouse \
  http://localhost:9000/pt/welcome/ \
  --form-factor=mobile \
  --throttling.cpuSlowdownMultiplier=4 \
  --quiet \
  --only-categories=performance \
  --chrome-flags="--headless --no-sandbox" \
  --output=json --output-path=/tmp/lh-pt.json
jq '.categories.performance.score' /tmp/lh-pt.json   # expect: ≥ 0.90
```

If `npx lighthouse` fails to install in the sandbox, document the exact
command for the operator to run on a workstation.

## AC4 — Open Graph & sharing

```bash
# OG meta tags present
curl -s http://localhost:9000/uk/welcome/ | grep -E 'property="og:(title|description|image|type|url)"' | wc -l   # expect: ≥5
curl -s http://localhost:9000/uk/welcome/ | grep -E 'name="twitter:card"' | grep summary_large_image            # expect: 1 hit

# OG image is reachable and is 1200x630 PNG
curl -sI http://localhost:9000/og/welcome-uk.png | head -1   # HTTP 200
file ../public/og/welcome-uk.png                              # PNG image data, 1200 x 630
file ../public/og/welcome-pt.png                              # PNG image data, 1200 x 630
```

Telegram preview validation (manual, on production after deploy — out of
scope for code-ready milestone but documented):

```bash
# Once deployed, open in TG: send the URL to @WebpageBot or yourself, watch the preview
# Or use the public OG inspector:
echo "Open: https://www.opengraph.xyz/url/https%3A%2F%2Fpastelka.news%2Fuk%2Fwelcome%2F"
echo "Open: https://www.opengraph.xyz/url/https%3A%2F%2Fpastelka.news%2Fpt%2Fwelcome%2F"
```

## AC5 — UTM-ready

```bash
# Page renders cleanly with utm params (no query-string-induced 404 / no JS error)
curl -s 'http://localhost:9000/uk/welcome/?utm_source=sticker_lisboa&utm_campaign=2026-q2' | grep -c 't.me/pashtelka_news'  # ≥1

# Lang-switcher preserves utm — verified by client-side handler. Smoke check:
# the rendered link starts as plain "/pt/welcome/" but the onClick adds search.
# Test in headless browser:
chromium --headless --disable-gpu --dump-dom \
  'http://localhost:9000/uk/welcome/?utm_source=sticker_lisboa' \
  | grep 'href="/pt/welcome/"'   # link is in the DOM
```

UTM is captured by Plausible automatically (Plausible parses `utm_*` from the
URL on every event). No extra wiring needed.

## AC6 — No tracking pixels beyond Plausible

```bash
# Confirm no Google Analytics, no Meta Pixel, no Hotjar, no Segment
for url in /uk/welcome/ /pt/welcome/; do
  HTML=$(curl -s "http://localhost:9000$url")
  echo "$HTML" | grep -iE 'google-analytics|googletagmanager|gtag|fbq|connect.facebook|hotjar|segment.com' \
    && echo "FAIL: tracker found on $url" \
    || echo "OK: $url clean"
done

# Plausible IS present
curl -s http://localhost:9000/uk/welcome/ | grep 'plausible.io/js/script' | wc -l   # expect: 1
curl -s http://localhost:9000/uk/welcome/ | grep 'plausible-event-name=welcome_tg_click' | wc -l   # expect: ≥1
curl -s http://localhost:9000/uk/welcome/ | grep 'plausible-event-name=welcome_site_click' | wc -l # expect: ≥1
```

`welcome_view` is fired in a `useEffect`; verified by inspecting the source:

```bash
grep -rn 'welcome_view' src/pages/uk/welcome.js src/pages/pt/welcome.js
```

## AC7 — Build & deploy

```bash
cd ~/workspace/projects/pashtelka-faion-net/gatsby
npm run clean && npm run build   # exits 0
test -f public/uk/welcome/index.html
test -f public/pt/welcome/index.html
test -f public/welcome/index.html
test -f public/og/welcome-uk.png
test -f public/og/welcome-pt.png
```

`deploy-gh.sh` runs untouched — no changes to deploy infra in this feature.

## AC8 — Anti-link-rot (`/welcome/` redirect)

```bash
# Static HTML page exists, contains language detection script + meta-refresh fallback
curl -s http://localhost:9000/welcome/ > /tmp/welcome.html
grep -c 'navigator.languages' /tmp/welcome.html   # ≥1
grep -c 'meta http-equiv="refresh"' /tmp/welcome.html   # ≥1
grep -c '/uk/welcome/' /tmp/welcome.html   # ≥1
grep -c '/pt/welcome/' /tmp/welcome.html   # ≥1

# UTM passthrough (visual: dump DOM after redirect with PT lang)
chromium --headless --disable-gpu --dump-dom \
  --lang=pt-PT \
  'http://localhost:9000/welcome/?utm_source=sticker_lisboa' 2>/dev/null \
  | tee /tmp/welcome-redirected.html >/dev/null
# After redirect, the rendered page should be /pt/welcome/ — chromium logs final URL.
```

404 alert wiring is out of scope for this feature — site-wide 404 alerts are
the pipeline's job (`scripts/`). If the operator wants explicit 404 → TG
alerting on `/uk/welcome/` and `/pt/welcome/` it's a follow-up SDD task.

## Final verification matrix

| AC | Command(s) | Pass criterion |
|----|-----------|----------------|
| AC1 | `curl -sI` × 2 + `lang="..."` grep | both 200 + lang attrs match |
| AC2 | `grep -c` per content block | each ≥1 |
| AC3 | `du -b` total | ≤ 250 000 bytes |
| AC3 (LH) | `npx lighthouse --form-factor=mobile` | perf score ≥ 0.90 |
| AC4 | OG meta tag count + `file` on PNG | ≥5 tags + 1200×630 PNG |
| AC5 | curl with `?utm_*` | renders, TG link present |
| AC6 | grep for trackers | no GA/Meta hits, Plausible present |
| AC7 | `npm run build` | exit 0, all 5 files present |
| AC8 | `curl /welcome/` content | redirect logic present |
