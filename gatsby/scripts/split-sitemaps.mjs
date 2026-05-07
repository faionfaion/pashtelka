#!/usr/bin/env node
// Post-build sitemap splitter (pt-translation-b1).
//
// gatsby-plugin-sitemap emits a single public/sitemap-0.xml plus an
// index public/sitemap-index.xml. This script partitions the URLs by
// locale prefix and writes:
//   public/sitemap-uk.xml    — URLs under /uk/ + locale-neutral pages
//   public/sitemap-pt.xml    — URLs under /pt/ + locale-neutral pages
//   public/sitemap.xml       — index referencing both locale sitemaps
//
// Locale-neutral pages (root /, /tag/<tag>/, /welcome/) appear in BOTH
// locale sitemaps so search engines find them from either entry point.
//
// Idempotent: safe to re-run on a built tree. Exits 0 on missing input
// (the sitemap plugin failed earlier in the build) so this never blocks
// a partial build from completing.
//
// Run via npm postbuild hook in gatsby/package.json.

import { readFile, writeFile, access } from "node:fs/promises";
import { constants as FS } from "node:fs";
import path from "node:path";

const PUBLIC_DIR = path.resolve(process.cwd(), "public");
const INPUT = path.join(PUBLIC_DIR, "sitemap-0.xml");

const SITE_URL = "https://pastelka.news";

const NS = `xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"` +
  ` xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"` +
  ` xmlns:xhtml="http://www.w3.org/1999/xhtml"` +
  ` xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"` +
  ` xmlns:video="http://www.google.com/schemas/sitemap-video/1.1"`;

async function main() {
  try {
    await access(INPUT, FS.R_OK);
  } catch {
    console.warn(`split-sitemaps: ${INPUT} not found — skipping (build incomplete?)`);
    return 0;
  }

  const xml = await readFile(INPUT, "utf-8");
  const urlBlocks = [...xml.matchAll(/<url>[\s\S]*?<\/url>/g)].map((m) => m[0]);

  if (urlBlocks.length === 0) {
    console.warn("split-sitemaps: no <url> blocks found in sitemap-0.xml");
    return 0;
  }

  const ukUrls = [];
  const ptUrls = [];
  const sharedUrls = [];

  for (const block of urlBlocks) {
    const locMatch = block.match(/<loc>([^<]+)<\/loc>/);
    if (!locMatch) continue;
    const loc = locMatch[1];
    if (loc.includes("/uk/")) ukUrls.push(block);
    else if (loc.includes("/pt/")) ptUrls.push(block);
    else sharedUrls.push(block);
  }

  // Locale-neutral URLs appear in both sitemaps so neither is dead.
  const ukAll = [...sharedUrls, ...ukUrls];
  const ptAll = [...sharedUrls, ...ptUrls];

  const wrap = (blocks) =>
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset ${NS}>${blocks.join("")}</urlset>\n`;

  await writeFile(path.join(PUBLIC_DIR, "sitemap-uk.xml"), wrap(ukAll), "utf-8");
  await writeFile(path.join(PUBLIC_DIR, "sitemap-pt.xml"), wrap(ptAll), "utf-8");

  const indexXml =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    `  <sitemap><loc>${SITE_URL}/sitemap-uk.xml</loc></sitemap>\n` +
    `  <sitemap><loc>${SITE_URL}/sitemap-pt.xml</loc></sitemap>\n` +
    `</sitemapindex>\n`;
  await writeFile(path.join(PUBLIC_DIR, "sitemap.xml"), indexXml, "utf-8");

  console.log(
    `split-sitemaps: wrote sitemap-uk.xml (${ukAll.length} urls), ` +
    `sitemap-pt.xml (${ptAll.length} urls), ` +
    `sitemap.xml (index of 2)`,
  );
  return 0;
}

main().then((rc) => process.exit(rc || 0)).catch((e) => {
  console.error("split-sitemaps: fatal:", e);
  process.exit(1);
});
