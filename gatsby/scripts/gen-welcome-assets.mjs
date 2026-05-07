#!/usr/bin/env node
/**
 * gen-welcome-assets.mjs — one-shot generator for welcome-landing assets.
 *
 *   node scripts/gen-welcome-assets.mjs hero      # placeholder mascot hero
 *   node scripts/gen-welcome-assets.mjs og-uk     # 1200x630 UA card
 *   node scripts/gen-welcome-assets.mjs og-pt     # 1200x630 PT card
 *   node scripts/gen-welcome-assets.mjs all       # all three
 *
 * Reads OPENAI_API_KEY from env or ~/workspace/.env. Idempotent — re-running
 * overwrites. Calls OpenAI gpt-image-1 (size 1536x1024, quality auto), then
 * post-processes via the bundled sharp module (transitive dep of
 * gatsby-plugin-sharp).
 *
 * Hero output: gatsby/src/images/welcome/hero-placeholder.{png,webp,avif}
 * OG output:   gatsby/static/og/welcome-{uk,pt}.png
 *
 * Designed to be re-run when the canonical mascot replaces the placeholder
 * (just point the script at a different prompt).
 */

import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const GATSBY_ROOT = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(GATSBY_ROOT, "..");

// Load sharp from the gatsby/node_modules tree.
const { default: sharp } = await import(
  path.join(GATSBY_ROOT, "node_modules", "sharp", "lib", "index.js")
);

// ---- API key loader ------------------------------------------------------
function loadOpenAIKey() {
  if (process.env.OPENAI_API_KEY) return process.env.OPENAI_API_KEY;
  const envFile = path.join(os.homedir(), "workspace", ".env");
  if (fs.existsSync(envFile)) {
    const lines = fs.readFileSync(envFile, "utf8").split("\n");
    for (const line of lines) {
      if (line.startsWith("OPENAI_API_KEY=")) {
        return line.slice("OPENAI_API_KEY=".length).trim();
      }
    }
  }
  return "";
}

const OPENAI_KEY = loadOpenAIKey();
if (!OPENAI_KEY) {
  console.error("FATAL: no OPENAI_API_KEY in env or ~/workspace/.env");
  process.exit(2);
}

// ---- Prompts -------------------------------------------------------------
const PROMPTS = {
  hero: `Friendly cartoon bird mascot, soft pastel colors with warm amber and
cream accents, clean flat illustration, large expressive eyes. The mascot is
centered. Background: sunny Lisbon street with a faint azulejo tile pattern
wall, yellow tram tracks, distant silhouette of the 25 de Abril bridge across
the Tagus. Daytime, soft golden light. Friendly, welcoming, mobile-first
composition with plenty of negative space on the right. Style: modern flat
vector illustration, light texture, no photorealism, NO TEXT in the image.`,

  "og-uk": `Banner-style horizontal illustration, very wide aspect (1.9:1).
Friendly pastel bird mascot on the left third, gentle Lisbon street scene
with azulejo tile + yellow tram + distant 25 de Abril bridge silhouette. Big
clean Cyrillic Ukrainian text in the lower-left third: "Новини Португалії
українською". Warm amber + cream + soft blue palette, modern flat
illustration, no photorealism. Text MUST be perfectly legible at small
thumbnail size — large bold cyrillic letters with high contrast.`,

  "og-pt": `Banner-style horizontal illustration, very wide aspect (1.9:1).
Friendly pastel bird mascot on the left third, gentle Lisbon street scene
with azulejo tile + yellow tram + distant 25 de Abril bridge silhouette. Big
clean Latin-alphabet Portuguese text in the lower-left third: "Notícias de
Portugal em ucraniano". Warm amber + cream + soft blue palette, modern flat
illustration, no photorealism. Text MUST be perfectly legible at small
thumbnail size — large bold letters with high contrast.`,
};

// ---- OpenAI image call ---------------------------------------------------
async function generateImage(prompt, size = "1536x1024") {
  console.log(`→ OpenAI gpt-image-1 (size=${size}, prompt ~${prompt.length} chars)…`);
  const resp = await fetch("https://api.openai.com/v1/images/generations", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENAI_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "gpt-image-1",
      prompt,
      n: 1,
      size,
      quality: "auto",
    }),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`OpenAI HTTP ${resp.status}: ${text.slice(0, 400)}`);
  }
  const data = await resp.json();
  const item = data.data?.[0];
  if (!item) throw new Error("OpenAI returned no images");
  if (item.b64_json) {
    return Buffer.from(item.b64_json, "base64");
  }
  if (item.url) {
    const img = await fetch(item.url);
    if (!img.ok) throw new Error(`Image fetch HTTP ${img.status}`);
    return Buffer.from(await img.arrayBuffer());
  }
  throw new Error("OpenAI response had neither b64_json nor url");
}

// ---- Pipelines -----------------------------------------------------------
async function buildHero() {
  const outDir = path.join(GATSBY_ROOT, "src", "images", "welcome");
  fs.mkdirSync(outDir, { recursive: true });

  const raw = await generateImage(PROMPTS.hero, "1024x1024");
  // Resize to 940 wide (above-the-fold target) and emit three formats.
  const base = sharp(raw).resize({ width: 940, withoutEnlargement: true });

  await base.clone().png({ compressionLevel: 9, quality: 80 })
    .toFile(path.join(outDir, "hero-placeholder.png"));
  await base.clone().webp({ quality: 70 })
    .toFile(path.join(outDir, "hero-placeholder.webp"));
  await base.clone().avif({ quality: 50 })
    .toFile(path.join(outDir, "hero-placeholder.avif"));

  for (const ext of ["png", "webp", "avif"]) {
    const f = path.join(outDir, `hero-placeholder.${ext}`);
    const sz = fs.statSync(f).size;
    console.log(`  ${path.relative(REPO_ROOT, f)}: ${(sz / 1024).toFixed(1)} KB`);
  }
}

async function buildOg(locale) {
  const outDir = path.join(GATSBY_ROOT, "static", "og");
  fs.mkdirSync(outDir, { recursive: true });

  const raw = await generateImage(PROMPTS[`og-${locale}`], "1536x1024");
  // Resize to height 630 keeping aspect, then center-crop to exactly 1200x630.
  const meta = await sharp(raw).metadata();
  // Resize so the shorter dimension becomes ≥ target while preserving aspect,
  // then extract a 1200x630 region centered.
  const targetW = 1200;
  const targetH = 630;
  // Fit cover: ensures the output covers the full 1200x630 area.
  const out = sharp(raw)
    .resize({ width: targetW, height: targetH, fit: "cover", position: "center" })
    .png({ compressionLevel: 9, quality: 85 });
  const outPath = path.join(outDir, `welcome-${locale}.png`);
  await out.toFile(outPath);
  const sz = fs.statSync(outPath).size;
  console.log(`  ${path.relative(REPO_ROOT, outPath)}: ${(sz / 1024).toFixed(1)} KB (input ${meta.width}×${meta.height})`);
}

// ---- Main ----------------------------------------------------------------
const cmd = process.argv[2] || "all";
const wanted =
  cmd === "all"
    ? ["hero", "og-uk", "og-pt"]
    : cmd === "hero"
    ? ["hero"]
    : cmd === "og-uk"
    ? ["og-uk"]
    : cmd === "og-pt"
    ? ["og-pt"]
    : null;

if (!wanted) {
  console.error(`Unknown sub-command: ${cmd}. Use: hero | og-uk | og-pt | all`);
  process.exit(1);
}

for (const w of wanted) {
  console.log(`\n=== ${w} ===`);
  if (w === "hero") await buildHero();
  if (w === "og-uk") await buildOg("uk");
  if (w === "og-pt") await buildOg("pt");
}

console.log("\nDone.");
