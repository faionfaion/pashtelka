import React from "react";
import { graphql, Link } from "gatsby";
import Layout from "../components/layout";

const ArticleTemplate = ({ data, pageContext }) => {
  const article = data.markdownRemark;
  const { prev, next } = pageContext;
  const fm = article.frontmatter;

  return (
    <Layout>
      <article className="article-full">
        <header>
          <span className={`type-badge type-${fm.type}`}>{fm.type}</span>
          <h1>{fm.title}</h1>
          <div className="article-meta">
            <span className="author">{fm.author}</span>
            <time dateTime={fm.date}>
              {new Date(fm.date + "T12:00:00").toLocaleDateString("uk-UA", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </time>
            <span className="reading-time">
              {Math.ceil(article.wordCount.words / 200)} хв читання
            </span>
          </div>
          {fm.tags && (
            <div className="tags">
              {fm.tags.map((tag) => (
                <Link key={tag} to={`/tag/${encodeURIComponent(tag)}/`} className="tag">
                  #{tag}
                </Link>
              ))}
            </div>
          )}
        </header>

        <div
          className="article-body"
          dangerouslySetInnerHTML={{ __html: article.html }}
        />

        {fm.source_urls && fm.source_urls.length > 0 && (
          <footer className="sources">
            <h3>Джерела</h3>
            <ul>
              {fm.source_urls.map((url, i) => (
                <li key={i}>
                  <a href={url} target="_blank" rel="noopener noreferrer">
                    {fm.source_names && fm.source_names[i]
                      ? fm.source_names[i]
                      : url}
                  </a>
                </li>
              ))}
            </ul>
          </footer>
        )}

        <nav className="article-nav">
          {prev && (
            <Link to={`/${prev.slug}/`} className="nav-prev">
              ← {prev.title}
            </Link>
          )}
          {next && (
            <Link to={`/${next.slug}/`} className="nav-next">
              {next.title} →
            </Link>
          )}
        </nav>
      </article>
    </Layout>
  );
};

export const query = graphql`
  query ($slug: String!) {
    markdownRemark(frontmatter: { slug: { eq: $slug } }) {
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
      }
    }
  }
`;

export default ArticleTemplate;

export const Head = ({ data }) => {
  const fm = data.markdownRemark.frontmatter;
  const ogImage = fm.image
    ? `https://pashtelka.faion.net${fm.image}`
    : null;
  return (
    <>
      <title>{fm.title} — Пастелка</title>
      <meta name="description" content={fm.description || ""} />
      <meta property="og:title" content={fm.title} />
      <meta property="og:description" content={fm.description || ""} />
      <meta property="og:type" content="article" />
      <meta property="og:url" content={`https://pashtelka.faion.net/${fm.slug}/`} />
      {ogImage && <meta property="og:image" content={ogImage} />}
      {ogImage && <meta property="og:image:width" content="1536" />}
      {ogImage && <meta property="og:image:height" content="1024" />}
      {ogImage && <meta name="twitter:card" content="summary_large_image" />}
      {ogImage && <meta name="twitter:image" content={ogImage} />}
      <meta property="og:site_name" content="Пастелка" />
      <meta property="article:author" content={fm.author} />
      <meta property="article:published_time" content={fm.date} />
      {fm.tags && fm.tags.map((tag) => (
        <meta key={tag} property="article:tag" content={tag} />
      ))}
      <html lang="uk" />
    </>
  );
};
