const path = require("path");

// pt-translation-b1: Map frontmatter `lang` (UA legacy is "ua") to URL
// prefix ("uk" or "pt").
const LANG_TO_PREFIX = { ua: "uk", uk: "uk", pt: "pt" };

exports.createPages = async ({ graphql, actions }) => {
  const { createPage } = actions;

  const result = await graphql(`
    {
      allMarkdownRemark(sort: { frontmatter: { date: DESC } }) {
        nodes {
          frontmatter {
            slug
            title
            date
            type
            tags
            author
            description
            source_urls
            source_names
            lang
          }
          html
          wordCount {
            words
          }
          fileAbsolutePath
        }
      }
    }
  `);

  if (result.errors) {
    throw result.errors;
  }

  const articles = result.data.allMarkdownRemark.nodes;

  // Group by slug, then by language. Legacy fall-back: missing lang is "ua".
  const bySlug = {};
  for (const node of articles) {
    const slug = node.frontmatter.slug;
    const fmLang = (node.frontmatter.lang || "ua").toLowerCase();
    if (!bySlug[slug]) bySlug[slug] = {};
    bySlug[slug][fmLang] = node;
  }

  // For prev/next pagination per locale, build flat ordered lists.
  const ukOrdered = articles
    .filter((n) => (n.frontmatter.lang || "ua").toLowerCase() === "ua" ||
                   (n.frontmatter.lang || "ua").toLowerCase() === "uk")
    .sort((a, b) => (a.frontmatter.date < b.frontmatter.date ? 1 : -1));
  const ptOrdered = articles
    .filter((n) => (n.frontmatter.lang || "").toLowerCase() === "pt")
    .sort((a, b) => (a.frontmatter.date < b.frontmatter.date ? 1 : -1));

  function neighbours(ordered, slug) {
    const idx = ordered.findIndex((n) => n.frontmatter.slug === slug);
    if (idx === -1) return { prev: null, next: null };
    const prev = idx < ordered.length - 1 ? ordered[idx + 1] : null;
    const next = idx > 0 ? ordered[idx - 1] : null;
    return {
      prev: prev ? { slug: prev.frontmatter.slug, title: prev.frontmatter.title } : null,
      next: next ? { slug: next.frontmatter.slug, title: next.frontmatter.title } : null,
    };
  }

  // Create per-locale article pages.
  for (const slug of Object.keys(bySlug)) {
    const variants = bySlug[slug];

    // UA page (legacy fm lang="ua", new fm lang could be "uk")
    const uaNode = variants.ua || variants.uk;
    if (uaNode) {
      const uaLang = (uaNode.frontmatter.lang || "ua").toLowerCase();
      const { prev, next } = neighbours(ukOrdered, slug);
      createPage({
        path: `/uk/${slug}/`,
        component: path.resolve("./src/templates/article.js"),
        context: {
          slug,
          lang: "uk",
          frontmatterLang: uaLang,         // "ua" or "uk"; query needs the actual fm value
          otherLocaleAvailable: !!variants.pt,
          prev,
          next,
        },
      });
    }

    // PT page
    if (variants.pt) {
      const { prev, next } = neighbours(ptOrdered, slug);
      createPage({
        path: `/pt/${slug}/`,
        component: path.resolve("./src/templates/article.js"),
        context: {
          slug,
          lang: "pt",
          frontmatterLang: "pt",
          otherLocaleAvailable: !!(variants.ua || variants.uk),
          prev,
          next,
        },
      });
    }
  }

  // Tag pages stay flat at /tag/<tag>/ — UA tags only for v1. Translating
  // the tag taxonomy is out of scope per spec.
  const tagSet = new Set();
  articles.forEach((article) => {
    const lang = (article.frontmatter.lang || "ua").toLowerCase();
    if (lang === "ua" || lang === "uk") {
      (article.frontmatter.tags || []).forEach((tag) => tagSet.add(tag));
    }
  });

  tagSet.forEach((tag) => {
    createPage({
      path: `/tag/${encodeURIComponent(tag)}/`,
      component: path.resolve("./src/templates/tag.js"),
      context: { tag },
    });
  });
};
