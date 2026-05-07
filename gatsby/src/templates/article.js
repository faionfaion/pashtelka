import React from "react";
import { graphql, Link } from "gatsby";
import Layout from "../components/layout";
import uk from "../i18n/uk.json";
import pt from "../i18n/pt.json";

const SITE_URL = "https://pastelka.news";

const ArticleTemplate = ({ data, pageContext }) => {
  const article = data.markdownRemark;
  const { prev, next, lang, otherLocaleAvailable } = pageContext;
  const fm = article.frontmatter;
  const i18n = lang === "pt" ? pt : uk;
  const dateLocale = lang === "pt" ? "pt-PT" : "uk-UA";
  const otherLocaleHref = otherLocaleAvailable
    ? `/${lang === "pt" ? "uk" : "pt"}/${fm.slug}/`
    : (lang === "pt" ? "/uk/" : "/pt/");

  return (
    <Layout lang={lang} otherLocaleHref={otherLocaleHref}>
      <article className="article-full" data-iv="true">
        <header>
          <div className="article-top">
            <span className={`type-badge type-${fm.type}`}>{fm.type}</span>
            <time dateTime={fm.date}>
              {new Date(fm.date + "T12:00:00").toLocaleDateString(dateLocale, {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </time>
          </div>
          <h1>{fm.title}</h1>
          <div className="article-meta">
            <span className="reading-time">
              {Math.ceil(article.wordCount.words / 200)} {i18n.minRead}
            </span>
          </div>
        </header>

        <div className="article-body">
          {fm.image && (
            <div className="hero-wrap">
              <img src={fm.image} alt={fm.title} loading="eager" />
            </div>
          )}
          <div dangerouslySetInnerHTML={{ __html: article.html }} />
        </div>

        {fm.tags && (
          <div className="article-tags">
            {fm.tags.map((tag) => (
              <Link key={tag} to={`/tag/${encodeURIComponent(tag)}/`} className="tag">
                #{tag}
              </Link>
            ))}
          </div>
        )}

        {fm.source_urls && fm.source_urls.length > 0 && (
          <footer className="sources">
            <h3>{i18n.sources}</h3>
            <ul>
              {fm.source_urls.map((url, i) => (
                <li key={i}>
                  <a href={url} target="_blank" rel="noopener noreferrer">
                    {fm.source_names && fm.source_names[i]
                      ? fm.source_names[i]
                      : (() => { try { return new URL(url).hostname; } catch { return url; } })()}
                  </a>
                </li>
              ))}
            </ul>
          </footer>
        )}

        <nav className="article-nav">
          {prev && (
            <Link to={`/${lang}/${prev.slug}/`} className="nav-prev">
              &larr; {prev.title}
            </Link>
          )}
          {next && (
            <Link to={`/${lang}/${next.slug}/`} className="nav-next">
              {next.title} &rarr;
            </Link>
          )}
        </nav>
      </article>
    </Layout>
  );
};

export const query = graphql`
  query ($slug: String!, $frontmatterLang: String!) {
    markdownRemark(
      frontmatter: { slug: { eq: $slug }, lang: { eq: $frontmatterLang } }
    ) {
      html
      wordCount {
        words
      }
      frontmatter {
        title
        slug
        date
        type
        author
        description
        tags
        source_urls
        source_names
        image
        lang
      }
    }
  }
`;

export default ArticleTemplate;

export const Head = ({ data, pageContext }) => {
  const fm = data.markdownRemark.frontmatter;
  const { lang, otherLocaleAvailable } = pageContext;
  const i18n = lang === "pt" ? pt : uk;
  const ogImage = fm.image ? `${SITE_URL}${fm.image}` : null;
  const canonical = `${SITE_URL}/${lang}/${fm.slug}/`;
  const ogLocale = lang === "pt" ? "pt_PT" : "uk_UA";
  const ogLocaleAlt = lang === "pt" ? "uk_UA" : "pt_PT";

  return (
    <>
      <title>{fm.title} — {i18n.siteName}</title>
      <meta name="description" content={fm.description || ""} />
      <meta property="og:title" content={fm.title} />
      <meta property="og:description" content={fm.description || ""} />
      <meta property="og:type" content="article" />
      <meta property="og:url" content={canonical} />
      <meta property="og:locale" content={ogLocale} />
      {otherLocaleAvailable && (
        <meta property="og:locale:alternate" content={ogLocaleAlt} />
      )}
      {ogImage && <meta property="og:image" content={ogImage} />}
      {ogImage && <meta property="og:image:width" content="1200" />}
      {ogImage && <meta property="og:image:height" content="800" />}
      {ogImage && <meta name="twitter:card" content="summary_large_image" />}
      {ogImage && <meta name="twitter:image" content={ogImage} />}
      <link rel="canonical" href={canonical} />
      <link rel="alternate" hrefLang="uk"
            href={`${SITE_URL}/uk/${fm.slug}/`} />
      {otherLocaleAvailable && (
        <link rel="alternate" hrefLang="pt"
              href={`${SITE_URL}/pt/${fm.slug}/`} />
      )}
      <link rel="alternate" hrefLang="x-default"
            href={`${SITE_URL}/uk/${fm.slug}/`} />
      <meta property="og:site_name" content={i18n.siteName} />
      <meta property="article:author" content={i18n.siteName} />
      <meta property="article:published_time" content={`${fm.date}T00:00:00Z`} />
      {fm.tags && fm.tags.map((tag) => (
        <meta key={tag} property="article:tag" content={tag} />
      ))}
      <html lang={lang} />
    </>
  );
};
