import React from "react";
import { graphql, Link } from "gatsby";
import Layout from "../../components/layout";
import pt from "../../i18n/pt.json";

const PtIndex = ({ data }) => {
  const articles = data.allMarkdownRemark.nodes;

  const grouped = {};
  articles.forEach((article) => {
    const date = article.frontmatter.date;
    if (!grouped[date]) grouped[date] = [];
    grouped[date].push(article);
  });

  const formatDate = (dateStr) => {
    const d = new Date(dateStr + "T12:00:00");
    return d.toLocaleDateString("pt-PT", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <Layout lang="pt" otherLocaleHref="/uk/">
      <div className="hero-section">
        <span className="badge">{pt.siteTagline}</span>
        <p className="subtitle">{pt.heroSubtitle}</p>
      </div>

      {articles.length === 0 && (
        <div className="empty-state">
          <p>Em breve: artigos em português simples (B1).</p>
          <p>
            <Link to="/uk/">{pt.switchToOtherLocale} →</Link>
          </p>
        </div>
      )}

      {Object.entries(grouped).map(([date, posts]) => (
        <div key={date} className="date-group">
          <h2 className="date-header">{formatDate(date)}</h2>
          <div className="articles-grid">
            {posts.map((article) => (
              <article key={article.frontmatter.slug} className="article-card">
                <Link to={`/pt/${article.frontmatter.slug}/`}>
                  {article.frontmatter.image && (
                    <img
                      className="card-image"
                      src={article.frontmatter.image}
                      alt=""
                      loading="lazy"
                    />
                  )}
                  <div className="card-content">
                    <span className={`type-badge type-${article.frontmatter.type}`}>
                      {article.frontmatter.type}
                    </span>
                    <h3>{article.frontmatter.title}</h3>
                    <p className="description">{article.frontmatter.description}</p>
                    <div className="meta">
                      <span>{Math.ceil(article.wordCount.words / 200)} {pt.minRead}</span>
                    </div>
                  </div>
                </Link>
              </article>
            ))}
          </div>
        </div>
      ))}
    </Layout>
  );
};

export const query = graphql`
  {
    allMarkdownRemark(
      filter: { frontmatter: { lang: { eq: "pt" } } }
      sort: { frontmatter: { date: DESC } }
      limit: 60
    ) {
      nodes {
        frontmatter {
          slug
          title
          date
          type
          description
          tags
          image
          lang
        }
        wordCount {
          words
        }
      }
    }
  }
`;

export default PtIndex;

export const Head = () => (
  <>
    <title>{pt.homeTitle}</title>
    <meta name="description" content={pt.siteDescription} />
    <meta property="og:title" content={pt.homeTitle} />
    <meta property="og:description" content={pt.siteDescription} />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="https://pastelka.news/pt/" />
    <meta property="og:site_name" content={pt.siteName} />
    <meta property="og:locale" content="pt_PT" />
    <meta property="og:locale:alternate" content="uk_UA" />
    <link rel="canonical" href="https://pastelka.news/pt/" />
    <link rel="alternate" hrefLang="uk" href="https://pastelka.news/uk/" />
    <link rel="alternate" hrefLang="pt" href="https://pastelka.news/pt/" />
    <link rel="alternate" hrefLang="x-default" href="https://pastelka.news/uk/" />
    <html lang="pt" />
  </>
);
